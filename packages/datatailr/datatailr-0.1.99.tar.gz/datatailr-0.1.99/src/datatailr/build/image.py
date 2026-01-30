# *************************************************************************
#
#  Copyright (c) 2026 - Datatailr Inc.
#  All Rights Reserved.
#
#  This file is part of Datatailr and subject to the terms and conditions
#  defined in 'LICENSE.txt'. Unauthorized copying and/or distribution
#  of this file, in parts or full, via any medium is strictly prohibited.
# *************************************************************************

import json
import os
import sys
import subprocess
from typing import Optional


class Image:
    """
    Represents a container image for a job.
    The image is defined based on its' python dependencies and two 'build scripts' expressed as Dockerfile commands.
    All attributes can be initialized with either a string or a file name.
    """

    def __init__(
        self,
        python_version: str = "auto",
        python_requirements: str | list[str] = "",
        build_script_pre: str = "",
        build_script_post: str = "",
        branch_name: Optional[str] = None,
        commit_hash: Optional[str] = None,
        path_to_repo: Optional[str] = None,
        path_to_module: Optional[str] = None,
    ):
        self.python_version = python_version
        self.python_requirements = python_requirements
        self.build_script_pre = build_script_pre
        self.build_script_post = build_script_post
        self.branch_name = branch_name
        self.commit_hash = commit_hash
        self.path_to_repo = path_to_repo
        self.path_to_module = path_to_module

        # Additional attributes, available after the image was built
        self.build_stdout: Optional[str] = None
        self.build_stderr: Optional[str] = None
        self.name: Optional[str] = None
        self.last_build_succeeded: Optional[bool] = None
        self.bundle_name: Optional[str] = None
        self.registry: Optional[str] = None
        self.run_after_build: Optional[bool] = False
        self.tag: Optional[str] = None

    @property
    def python_version(self):
        return self._python_version

    @python_version.setter
    def python_version(self, value: str | None):
        if value is None or value == "":
            value = "3.13"
        if not isinstance(value, str):
            raise TypeError("python_version must be a string.")
        if value.lower() == "auto":
            value = f"{sys.version_info.major}.{sys.version_info.minor}"
        if value not in ["3.10", "3.11", "3.12", "3.13", "3.14"]:
            raise ValueError(f"Invalid python_version: {value}")
        self._python_version = value

    @property
    def python_requirements(self):
        return self._python_requirements

    @python_requirements.setter
    def python_requirements(self, value: str | list[str]):
        if isinstance(value, str):
            if value == "auto":
                # Automatically deduce the requirements from the current environment by running pip freeze
                try:
                    value = subprocess.run(
                        ["pip", "freeze"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True,
                        timeout=60,
                    ).stdout
                except Exception as e:
                    raise RuntimeError(
                        "Failed to auto-deduce python_requirements. Ensure that pip is installed in the current environment."
                    )
            elif os.path.isfile(value):
                with open(value, "r") as f:
                    value = f.read()
            elif "," in value:
                value = value.replace(",", "\n")
        elif isinstance(value, list):
            value = "\n".join(value)
        if not isinstance(value, str):
            raise TypeError(
                "python_requirements must be a list of strings, a file path to a requirements file or 'auto'."
            )
        self._python_requirements = value

    @property
    def build_script_pre(self):
        return self._build_script_pre

    @build_script_pre.setter
    def build_script_pre(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                "build_script_pre must be a string or a file path to a script file."
            )
        if os.path.isfile(value):
            with open(value, "r") as f:
                value = f.read()
        self._build_script_pre = value

    @property
    def build_script_post(self):
        return self._build_script_post

    @build_script_post.setter
    def build_script_post(self, value: str):
        if not isinstance(value, str):
            raise TypeError(
                "build_script_post must be a string or a file path to a script file."
            )
        if os.path.isfile(value):
            with open(value, "r") as f:
                value = f.read()
        self._build_script_post = value

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if (
                key in ["branch_name", "commit_hash", "path_to_repo", "path_to_module"]
                and value is not None
                and not isinstance(value, str)
            ):
                raise TypeError(f"{key} must be a string or None.")
            if not hasattr(self, key):
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{key}'"
                )
            setattr(self, key, value)

    def to_dict(self):
        """
        Convert the Image instance to a dictionary representation.
        """
        return {
            "python_version": self.python_version,
            "python_requirements": self.python_requirements,
            "build_script_pre": self.build_script_pre,
            "build_script_post": self.build_script_post,
            "branch_name": self.branch_name,
            "commit_hash": self.commit_hash,
            "path_to_repo": self.path_to_repo,
            "path_to_module": self.path_to_module,
        }

    def to_json(self):
        """
        Convert the Image instance to a JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=4)

    def from_dict(self, data: dict) -> "Image":
        """
        Create an Image instance from a dictionary representation.
        """
        for key, value in data.items():
            if not hasattr(self, key):
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{key}'"
                )
            setattr(self, key, value)

        return self

    def __eq__(self, other):
        if not isinstance(other, Image):
            return NotImplemented
        return (
            self.python_version == other.python_version
            and self.python_requirements == other.python_requirements
            and self.build_script_pre == other.build_script_pre
            and self.build_script_post == other.build_script_post
            and self.branch_name == other.branch_name
            and self.commit_hash == other.commit_hash
            and self.path_to_repo == other.path_to_repo
            and self.path_to_module == other.path_to_module
        )
