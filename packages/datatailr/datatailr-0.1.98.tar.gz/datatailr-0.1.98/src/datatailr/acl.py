# *************************************************************************
#
#  Copyright (c) 2026 - Datatailr Inc.
#  All Rights Reserved.
#
#  This file is part of Datatailr and subject to the terms and conditions
#  defined in 'LICENSE.txt'. Unauthorized copying and/or distribution
#  of this file, in parts or full, via any medium is strictly prohibited.
# *************************************************************************

from __future__ import annotations

import json
from enum import Enum

from datatailr import Group, User
from datatailr.group import DTUSERS_GROUP_NAME


class Permission(Enum):
    READ = "read"
    WRITE = "write"
    OPERATE = "operate"
    ACCESS = "access"
    PROMOTE = "promote"

    def __str__(self):
        return self.value


class ACL:
    """
    A class to represent an Access Control List (ACL) for managing permissions.
    """

    def __init__(
        self,
        permissions: dict[Permission, list[User | Group]] | None = None,
    ):
        if not permissions:
            user: User = User.signed_user()
            group: Group = Group.get(DTUSERS_GROUP_NAME)
            if user is None or group is None:
                raise ValueError("Signed user or primary group not found.")
            _permissions: dict[Permission, list[User | Group]] = {
                Permission.READ: [user, group],
                Permission.WRITE: [user],
                Permission.OPERATE: [user],
                Permission.ACCESS: [user, group],
                Permission.PROMOTE: [user],
            }
        else:
            _permissions = permissions
        self.permissions = _permissions

    def __repr__(self):
        return "datatailr.ACL:\n" + "\n".join(
            f"{str(permission_type):>10}: {[str(entity) for entity in entities]}"
            for permission_type, entities in self.permissions.items()
        )

    def to_dict(self):
        acl_dict = {
            str(permission_type): [
                -entity.group_id if isinstance(entity, Group) else entity.user_id
                for entity in entities
            ]
            for permission_type, entities in self.permissions.items()
        }
        return acl_dict

    @classmethod
    def from_dict(cls, acl_dict: dict) -> ACL:
        """
        Create an ACL instance from a dictionary.
        """
        permissions: dict[Permission, list[User | Group]] = {}

        for permission_type_str, entity_ids in acl_dict.items():
            permission_type = Permission(permission_type_str)
            entities: list[User | Group] = []

            for entity_id in entity_ids:
                entity = (
                    Group.get(abs(entity_id)) if entity_id < 0 else User.get(entity_id)
                )
                if entity is None:
                    raise ValueError(
                        f"{'Group' if entity_id < 0 else 'User'} id {abs(entity_id)} not found"
                    )
                entities.append(entity)

            permissions[permission_type] = entities

        return ACL(permissions=permissions)

    @classmethod
    def default_for_user(cls, user: User | str) -> ACL:
        """
        Create a default ACL for a given user.
        """
        if isinstance(user, str):
            _user: User = User(user)
        else:
            _user = user
        group: Group = Group.get(DTUSERS_GROUP_NAME)
        permissions: dict[Permission, list[User | Group]] = {
            Permission.READ: [_user, group],
            Permission.WRITE: [_user],
            Permission.OPERATE: [_user],
            Permission.ACCESS: [_user, group],
            Permission.PROMOTE: [_user],
        }
        return ACL(permissions=permissions)

    def to_json(self):
        return json.dumps(self.to_dict())
