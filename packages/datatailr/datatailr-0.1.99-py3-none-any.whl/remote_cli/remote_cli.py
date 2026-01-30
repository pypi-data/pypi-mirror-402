#!/usr/bin/env python3

"""
Remote dt CLI client for Datatailr.

Usage:
  - Run `dt login` to authenticate.
  - Use `dt <command> <subcommand> [args...]` as usual - the calls will be executed remotely.
  - To get help, either append -h / --help to a CLI call, or call bare `dt`, `dt <command>` or `dt <command> <subcommand>`.

Notes:
  - Files specified as arguments will be read from local disk and sent as JSON when possible.
  - This client requires the 'requests' library.
"""

from __future__ import annotations
import argparse
import base64
import getpass
import json
import os
import sys
import tarfile
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import requests


CONFIG_DIR = Path.home() / ".dt" / "remote_cli"
CONFIG_PATH = CONFIG_DIR / "remote_cli.cfg"
OPENAPI_CACHE_PATH = CONFIG_DIR / "openapi.json"
COOKIE_NAME = "X-Datatailr-Oidc-Data"


@dataclass
class Config:
    base_url: str
    jwt_cookie: str

    @staticmethod
    def load() -> "Config":
        """Load remote CLI config from disk."""
        if not CONFIG_PATH.exists():
            raise RuntimeError(
                "No config found for remote cli - please run 'dt login'."
            )
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        base_url = data.get("base_url")
        jwt_cookie = data.get("jwt_cookie")
        if not base_url or not jwt_cookie:
            raise RuntimeError("Invalid config for remote cli - please run 'dt login'.")
        return Config(base_url=base_url, jwt_cookie=jwt_cookie)

    def save(self) -> None:
        """Persist remote CLI config to disk with restricted permissions."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(
                {"base_url": self.base_url, "jwt_cookie": self.jwt_cookie}, indent=2
            ),
            encoding="utf-8",
        )
        try:
            os.chmod(CONFIG_PATH, 0o600)
        except Exception:
            pass


def fetch_openapi(
    base_url: str, jwt_cookie: str, timeout_s: int = 10
) -> Dict[str, Any]:
    """Fetch OpenAPI spec from the server using the auth cookie."""
    url = f"{base_url}/api/openapi.json"
    for attempt in range(3):
        resp = requests.get(
            url,
            headers={"Cookie": f"{COOKIE_NAME}={jwt_cookie}"},
            timeout=timeout_s,
        )
        if resp.status_code >= 400:
            raise RuntimeError(
                f"Failed to fetch OpenAPI: {resp.status_code}\n{resp.text[:400]}"
            )
        try:
            return resp.json()
        except requests.exceptions.JSONDecodeError:
            if attempt < 2:
                time.sleep(0.3 * (attempt + 1))
                continue
            break
    raise RuntimeError(
        "Failed to parse OpenAPI response (not JSON). If datatailr was just started, it might take around a minute to be ready.\n"
    )


def cache_openapi(spec: Dict[str, Any]) -> None:
    """Write OpenAPI spec to the local cache."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    OPENAPI_CACHE_PATH.write_text(json.dumps(spec, indent=2), encoding="utf-8")


def load_cached_openapi() -> Dict[str, Any]:
    """Load OpenAPI spec from the local cache."""
    if not OPENAPI_CACHE_PATH.exists():
        raise RuntimeError(
            f"No cached OpenAPI at {OPENAPI_CACHE_PATH}. Please run 'dt login'."
        )
    return json.loads(OPENAPI_CACHE_PATH.read_text(encoding="utf-8"))


def load_api_option_metadata(
    operation: Dict[str, Any],
) -> Tuple[Dict[str, str], Dict[str, bool]]:
    """
    Load CLI option metadata from OpenAPI extensions.
    Returns: (short_to_long, long_requires_arg)
    """
    short_to_long: Dict[str, str] = {}
    long_requires: Dict[str, bool] = {}

    for param in operation.get("parameters", []) or []:
        name = param.get("name")
        if not name:
            continue
        schema = param.get("schema") or {}
        param_type = schema.get("type")
        long_requires[name] = param_type != "boolean"
        short_name = param.get("x-short-name")
        if short_name:
            short_to_long[short_name] = name

    rb = operation.get("requestBody", {}) or {}
    content = (rb.get("content") or {}).get("application/json") or {}
    schema = content.get("schema") or {}
    for name, prop in (schema.get("properties") or {}).items():
        prop_type = (prop or {}).get("type")
        long_requires[name] = prop_type != "boolean"
        short_name = (prop or {}).get("x-short-name")
        if short_name:
            short_to_long[short_name] = name

    return short_to_long, long_requires


def parse_options_from_args(
    argv_tail: List[str],
    operation: Dict[str, Any],
    short_to_long: Dict[str, str],
    long_requires: Dict[str, bool],
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Split argv into positional args and option values.
    Supports -x value and --long value (and --flag for no-arg bools).
    """
    valid_long = {p.get("name") for p in operation.get("parameters", []) or []}
    rb = operation.get("requestBody", {}) or {}
    content = (rb.get("content") or {}).get("application/json") or {}
    schema = content.get("schema") or {}
    valid_long.update((schema.get("properties") or {}).keys())
    valid_long.discard(None)

    positionals: List[str] = []
    options: Dict[str, Any] = {}

    i = 0
    while i < len(argv_tail):
        token = argv_tail[i]
        if token == "--":
            positionals.extend(argv_tail[i + 1 :])
            break

        if token.startswith("--") and len(token) > 2:
            name = token[2:]
            if name not in valid_long and name not in long_requires:
                positionals.append(token)
                i += 1
                continue
            requires_arg = long_requires.get(name, True)
            if not requires_arg:
                options[name] = True
                i += 1
                continue
            if i + 1 >= len(argv_tail):
                raise RuntimeError(f"Missing value for option '--{name}'")
            options[name] = argv_tail[i + 1]
            i += 2
            continue

        if token.startswith("-") and len(token) >= 2:
            shorts = token[1:]
            handled = False
            for idx, short in enumerate(shorts):
                long_name = short_to_long.get(short)
                if not long_name:
                    handled = False
                    break
                requires_arg = long_requires.get(long_name, True)
                if requires_arg:
                    # Remainder of the token is the value, otherwise next arg.
                    rest = shorts[idx + 1 :]
                    if rest:
                        options[long_name] = rest
                        handled = True
                        break
                    if i + 1 >= len(argv_tail):
                        raise RuntimeError(f"Missing value for option '-{short}'")
                    options[long_name] = argv_tail[i + 1]
                    i += 1
                    handled = True
                    break
                options[long_name] = True
                handled = True
            if handled:
                i += 1
                continue

        positionals.append(token)
        i += 1

    return positionals, options


def auth_login(base_url: str, username: str, password: str, timeout_s: int = 30) -> str:
    """
    POST /login?response_type=id_token
    Extracts cookie X-Datatailr-Oidc-Data from session cookie jar.
    """
    sess = requests.Session()
    resp = sess.post(
        f"{base_url}/login",
        params={"response_type": "id_token"},
        auth=(username, password),
        timeout=timeout_s,
    )
    if resp.status_code == 401:
        raise RuntimeError("Login failed: invalid username or password.")
    if resp.status_code >= 400:
        raise RuntimeError(f"Login failed: HTTP {resp.status_code}\n{resp.text[:500]}")

    jwt = sess.cookies.get(COOKIE_NAME)
    if not jwt:
        raise RuntimeError("Login succeeded but JWT token is not found.")
    return jwt


def encode_file_as_json(path_str: str) -> Any:
    """
    Send file contents as JSON when possible; fall back to raw text.
    """
    p = Path(path_str)
    text = p.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except Exception as e:
        raise RuntimeError(f"Failed to parse file '{path_str}' as JSON: {e}")


def resolve_repo_path(path_to_repo: str, job_file: Path) -> Path:
    repo_path = Path(path_to_repo)
    if repo_path.exists():
        return repo_path
    fallback = job_file.parent / repo_path.name
    if fallback.exists():
        return fallback
    raise RuntimeError(
        f"Cannot resolve path_to_repo '{path_to_repo}'. "
        f"Expected it to exist or be relative to '{job_file.parent}'."
    )


def create_module_archive(repo_path: Path, module_path: str) -> Tuple[str, str, str]:
    module_dir = repo_path / module_path
    if not module_dir.exists() or not module_dir.is_dir():
        raise RuntimeError(
            f"Module path '{module_path}' not found under repo '{repo_path}'."
        )
    repo_dir_name = str(repo_path).lstrip(os.sep)
    if not repo_dir_name:
        raise RuntimeError(
            f"Cannot infer repo directory name from path_to_repo '{repo_path}'."
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        archive_path = Path(tmp_dir) / "module.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(module_dir, arcname=module_path)
        archive_b64 = base64.b64encode(archive_path.read_bytes()).decode("ascii")
    return archive_b64, repo_dir_name, module_path


def try_to_prepare_repo_bundle(job_json: Any, job_file: Path) -> Dict[str, Any]:
    if not isinstance(job_json, dict):
        return {}
    image = job_json.get("image", {})
    path_to_repo = image.get("path_to_repo")
    path_to_module = image.get("path_to_module")
    if not path_to_repo or not path_to_module:
        return {}

    repo_path = resolve_repo_path(str(path_to_repo), job_file)
    archive_b64, repo_dir_name, module_path = create_module_archive(
        repo_path, str(path_to_module)
    )
    return {
        "repo_archive_b64": archive_b64,
        "repo_dir_name": repo_dir_name,
        "repo_module_path": module_path,
    }


def is_local_file_arg(value: str) -> bool:
    """Return True if value points to an existing local file (non-blob URI)."""
    # Treat blob://... as remote path, everything else can be local file if it exists.
    if value.startswith("blob://"):
        return False
    p = Path(value)
    return p.exists() and p.is_file()


def get_operation_for_path(
    spec: Dict[str, Any], api_path: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Returns (http_method, operation_object) for the given OpenAPI path.
    Assumes exactly one method exists under that path.
    """
    paths = spec.get("paths", {})
    if api_path not in paths:
        raise RuntimeError(f"Unknown command: no OpenAPI path '{api_path}'")

    methods_obj = paths[api_path]
    # Filter to HTTP methods
    candidates = [
        (m.lower(), op)
        for m, op in methods_obj.items()
        if m.lower() in {"get", "post", "put", "patch", "delete"}
    ]
    if not candidates:
        raise RuntimeError(f"No HTTP operation found under '{api_path}'")
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly 1 method for '{api_path}', found: {[m for m,_ in candidates]}"
        )
    return candidates[0][0].upper(), candidates[0][1]


def build_request_from_openapi(
    operation: Dict[str, Any],
    argv_tail: List[str],
    extra_query: Optional[Dict[str, Any]] = None,
    extra_body: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Returns (query_params, json_body).

    Rules:
    - If requestBody application/json exists:
        map positional args to required fields IN THE ORDER LISTED by schema.required.
    - If parameters exist (query):
        map positional args to required query params IN THE ORDER THEY APPEAR in operation.parameters.
    - If both exist, we fill query required first, then body required.
    - After satisfying REQUIRED arguments, any remaining positional args are mapped to
        OPTIONAL query parameters (in declared order) and then OPTIONAL body fields.
    """
    query: Dict[str, Any] = dict(extra_query or {})
    body: Dict[str, Any] = dict(extra_body or {})

    all_query_params: List[Dict[str, Any]] = []
    for p in operation.get("parameters", []) or []:
        if p.get("in") == "query":
            all_query_params.append(p)

    required_query_names = [
        p["name"] for p in all_query_params if p.get("required") is True
    ]
    optional_query_names = [
        p["name"] for p in all_query_params if p.get("required") is not True
    ]

    required_body_names: List[str] = []
    optional_body_names: List[str] = []

    rb = operation.get("requestBody", {})
    if rb:
        content = (rb.get("content") or {}).get("application/json")
        if content:
            schema = content.get("schema") or {}
            required_body_names = list(schema.get("required") or [])
            props = schema.get("properties", {})
            for k in props.keys():
                if k not in required_body_names:
                    optional_body_names.append(k)

    # Filter out already provided via flags
    required_query_names = [n for n in required_query_names if n not in query]
    required_body_names = [n for n in required_body_names if n not in body]

    optional_query_names = [n for n in optional_query_names if n not in query]
    optional_body_names = [n for n in optional_body_names if n not in body]

    min_expected = len(required_query_names) + len(required_body_names)

    if len(argv_tail) < min_expected:
        raise RuntimeError(
            f"Wrong number of arguments.\n"
            f"Expected at least {min_expected} positional args "
            f"(required query={required_query_names}, required body={required_body_names}), "
            f"got {len(argv_tail)}."
        )

    cursor = 0

    for name in required_query_names:
        query[name] = argv_tail[cursor]
        cursor += 1

    for name in required_body_names:
        val = argv_tail[cursor]
        cursor += 1
        # Special file handling logic
        if name == "data" and is_local_file_arg(val):
            job_file = Path(val)
            job_json = encode_file_as_json(val)
            extra_bundle = try_to_prepare_repo_bundle(job_json, job_file)
            body[name] = job_json
            body.update(extra_bundle)
        else:
            body[name] = val

    # If we still have args, try to fill optional query params
    for name in optional_query_names:
        if cursor >= len(argv_tail):
            break
        query[name] = argv_tail[cursor]
        cursor += 1

    for name in optional_body_names:
        if cursor >= len(argv_tail):
            break
        val = argv_tail[cursor]
        cursor += 1
        body[name] = val

    return query, body


def send_request(
    cfg: Config, spec: Dict[str, Any], full_argv: List[str], timeout_s: int = 60
) -> int:
    """Build and execute a remote API call from CLI args."""

    def handle_unknown_command(target_cmd: str) -> int:
        """Route unknown command to appropriate help endpoint."""
        cmd_exists = any(
            p.startswith(f"/api/{target_cmd}/") for p in spec.get("paths", {})
        )
        if cmd_exists:
            return send_help(cfg, target_cmd, None, timeout_s=timeout_s)
        return send_help(cfg, None, None, timeout_s=timeout_s)

    if not full_argv:
        return send_help(cfg, None, None, timeout_s=timeout_s)

    if len(full_argv) == 1:
        return handle_unknown_command(full_argv[0])

    cmd, subcmd, *rest = full_argv
    if rest == ["-h"] or rest == ["--help"]:
        return send_help(cfg, cmd, subcmd, timeout_s=timeout_s)
    api_path = f"/api/{cmd}/{subcmd}"

    try:
        method, operation = get_operation_for_path(spec, api_path)
    except RuntimeError:
        return handle_unknown_command(cmd)

    if cmd == "blob" and subcmd == "cp":
        print("dt blob cp is not yet supported in remote CLI.", file=sys.stderr)
        return 2
    short_to_long, long_requires = load_api_option_metadata(operation)
    positionals, options = parse_options_from_args(
        rest, operation, short_to_long, long_requires
    )

    try:
        if method == "GET":
            query, body = build_request_from_openapi(
                operation, positionals, extra_query=options
            )
        else:
            query, body = build_request_from_openapi(
                operation, positionals, extra_body=options
            )
    except RuntimeError as e:
        if str(e).startswith("Wrong number of arguments"):
            return send_help(cfg, cmd, subcmd, timeout_s=timeout_s)
        raise

    url = f"{cfg.base_url}{api_path}"
    headers = build_headers(cfg)

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=query, timeout=timeout_s)
        else:
            # For non-GET, include JSON body if present; include query too if needed.
            resp = requests.request(
                method,
                url,
                headers=headers,
                params=query,
                json=(body if body else None),
                timeout=timeout_s,
            )
    except requests.RequestException as e:
        print(
            f"Cannot reach the platform at {cfg.base_url}. Is the platform running?\n"
            "If the URL is wrong, run 'dt login' to update it.",
            file=sys.stderr,
        )
        return 2

    return handle_response(resp, pretty_print=options.get("pretty", False))


def send_help(
    cfg: Config, group: Optional[str], subcmd: Optional[str], timeout_s: int = 30
) -> int:
    """Request server-side help output for a command or subcommand."""
    if group and subcmd:
        url = f"{cfg.base_url}/api/{group}/{subcmd}/help"
    elif group:
        url = f"{cfg.base_url}/api/{group}/help"
    else:
        url = f"{cfg.base_url}/api/help"

    headers = build_headers(cfg)

    try:
        resp = requests.get(url, headers=headers, timeout=timeout_s)
    except requests.RequestException as e:
        print(
            f"Cannot reach the platform at {cfg.base_url}. Is the platform running?\n"
            "If the URL is wrong, run 'dt login' to update it.",
            file=sys.stderr,
        )
        return 2

    return handle_response(resp)


def build_headers(cfg: Config) -> Dict[str, str]:
    """Build request headers for authenticated CLI calls."""
    return {
        "Cookie": f"{COOKIE_NAME}={cfg.jwt_cookie}",
        "Accept": "text/plain, application/json;q=0.9, */*;q=0.8",
        "User-Agent": "dt-remote-cli/0.1",
    }


def handle_response(resp: requests.Response, pretty_print: bool = False) -> int:
    """Render HTTP responses to stdout/stderr and return exit code."""
    if is_auth_failure(resp):
        print(
            "Not authenticated or session expired - please call 'dt login' to authenticate.",
            file=sys.stderr,
        )
        return 1

    if resp.status_code >= 400:
        try:
            data = resp.json()
            err = data.get("error", "")
            if err:
                print(str(err), file=sys.stderr)
                return 1
            if "message" in data:
                print(data["message"], file=sys.stderr)
                return 1
        except Exception:
            pass

        print(resp.text, file=sys.stderr)
        return 1

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = resp.json()
        except Exception:
            print(resp.text)
            return 0 if resp.ok else 1

        err = data.get("error", "")
        res = data.get("result", None)

        if err:
            print(err, file=sys.stderr)
            if res is not None:
                print(json.dumps(res, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

        if isinstance(res, str):
            print(res, end="" if res.endswith("\n") else "\n")
        else:
            if pretty_print:
                print(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(res, ensure_ascii=False))
        return 0 if resp.ok else 1

    if resp.text:
        try:
            val = json.loads(resp.text)
            if pretty_print:
                print(json.dumps(val, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(val, ensure_ascii=False))
            return 0 if resp.ok else 1
        except Exception:
            print(resp.text, end="" if resp.text.endswith("\n") else "\n")

    return 0 if resp.ok else 1


def is_auth_failure(resp: requests.Response) -> bool:
    """Return True if response indicates an auth failure or login redirect."""
    if resp.status_code == 401:
        return True
    if resp.status_code in {301, 302, 303, 307, 308} and "login" in resp.url:
        return True
    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type.lower():
        body = resp.text or ""
        if "Enter your login credentials" in body or (
            "<title" in body and "Login" in body
        ):
            return True
    return False


def cmd_auth(_: argparse.Namespace) -> int:
    """Interactive login flow for storing JWT + cached OpenAPI."""
    default_base_url = "http://localhost"
    try:
        default_base_url = Config.load().base_url
    except Exception:
        pass

    base_url_in = (
        input(f"Base URL (default {default_base_url}): ").strip() or default_base_url
    )
    base_url = base_url_in.strip().rstrip("/")
    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = (
            "http://" + base_url if "localhost" in base_url else "https://" + base_url
        )

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    try:
        jwt = auth_login(base_url, username, password)
        spec = fetch_openapi(base_url, jwt)
        cache_openapi(spec)

        cfg = Config(base_url=base_url, jwt_cookie=jwt)
        cfg.save()

        print("Login successful. Configuration saved.")
        return 0
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2
    except requests.RequestException as e:
        print(
            f"Cannot reach the platform at {base_url}. Is the platform running?\n"
            "If the URL is wrong, run 'dt login' to update it.",
            file=sys.stderr,
        )
        return 2


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser for the remote CLI."""
    parser = argparse.ArgumentParser(
        prog="dt",
        description="Remote dt CLI client for the Datatailr platform. Run 'dt login' to authenticate, then use dt <command> <subcommand> [args...] as usual to issue commands.",
    )
    sub = parser.add_subparsers(dest="subcmd")

    parser_auth = sub.add_parser("login", help="Login to remote Datatailr platform")
    parser_auth.set_defaults(func=cmd_auth)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entrypoint handling login, help, and remote commands."""
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_parser()

    if not argv:
        try:
            cfg = Config.load()
            return send_help(cfg, None, None)
        except Exception:
            parser.print_help()
            return 1

    if argv and argv[0] == "login":
        args = parser.parse_args(argv)
        return int(args.func(args))

    cfg = Config.load()
    spec = load_cached_openapi()
    try:
        return send_request(cfg, spec, argv)
    except RuntimeError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
