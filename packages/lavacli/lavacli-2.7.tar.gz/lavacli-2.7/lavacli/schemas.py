# vim: set ts=4

# Copyright 2022-present Linaro
# This file is part of lavacli.
#
# lavacli is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lavacli is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with lavacli.  If not, see <http://www.gnu.org/licenses/>

from voluptuous import All, Any, Invalid, Length, Range, Schema
from voluptuous.validators import Email

group_device_permission = Schema(
    {
        "name": All(str, Length(min=1)),
        "group": All(str, Length(min=1)),
    }
)

device_schema = Schema(
    {
        "hostname": All(str, Length(min=1)),
        "device_type": All(str, Length(min=1)),
        "worker": Any(str, None),
        "description": str,
        "tags": list,
        "permissions": [group_device_permission],
        "retire": bool,
    },
)


device_types_schema = Schema(
    Any(
        {
            "name": All(str, Length(min=1)),
            "description": str,
            "health_disabled": bool,
            "health_denominator": Any("hours", "jobs"),
            "health_frequency": All(int, Range(min=1)),
            "aliases": list,
            "display": bool,
            "permissions": [group_device_permission],
        },
        None,
    )
)

group_schema = Schema(Any({"name": str, "permissions": list}, None))

user_schema = Schema(
    Any(
        {
            "username": All(str, Length(min=1)),
            "last_name": All(str, Length(min=1)),
            "first_name": All(str, Length(min=1)),
            "email": Email(),
            "is_superuser": bool,
            "is_staff": bool,
            "is_active": bool,
            "ldap": bool,
            "groups": list,
            "permissions": list,
        },
        None,
    )
)

worker_schema = Schema(
    Any(
        {
            "hostname": str,
            "description": str,
            "job_limit": All(int, Range(min=1)),
            "retire": bool,
        },
        None,
    )
)


def user_group_must_exist(data: dict) -> dict:
    users = data.get("users", {})
    for user in users:
        user_config = users[user]
        if user_config:
            for group in user_config.get("groups", []):
                if group not in data.get("groups", {}):
                    raise Invalid(
                        f"Group must exist",
                        path=["users", user, "groups", group],
                    )

    return data


def device_dt_must_exist(data: dict) -> dict:
    devices = data.get("devices", {})
    for device in devices:
        dt = devices[device].get("device_type")
        if dt and dt not in data.get("device_types", {}):
            raise Invalid(
                f"Device type must exist",
                path=["devices", device, "device_type", dt],
            )

    return data


def device_worker_must_exist(data: dict) -> dict:
    devices = data.get("devices", {})
    for device in devices:
        worker = devices[device].get("worker")
        if worker and worker not in data.get("workers", {}):
            raise Invalid(
                f"Worker must exist",
                path=["devices", device, "worker", worker],
            )

    return data


def device_perms_group_must_exist(data: dict) -> dict:
    devices = data.get("devices", {})
    for device in devices:
        perms = devices[device].get("permissions", [])
        for perm in perms:
            group = perm["group"]
            if group not in data.get("groups", {}):
                raise Invalid(
                    f"Group must exist",
                    path=["devices", device, "permissions", perm],
                )

    return data


def dt_perms_group_must_exist(data: dict) -> dict:
    dts = data.get("device_types", {})
    for dt in dts:
        dt_config = dts[dt]
        if dt_config:
            perms = dts[dt].get("permissions", [])
            for perm in perms:
                group = perm["group"]
                if group not in data.get("groups", {}):
                    raise Invalid(
                        f"Group must exist",
                        path=["devices_types", dt, "permissions", perm],
                    )

    return data


config_schema = Schema(
    All(
        {
            "groups": {str: group_schema},
            "users": {str: user_schema},
            "workers": {str: worker_schema},
            "device_types": {str: device_types_schema},
            "devices": {str: device_schema},
        },
        user_group_must_exist,
        device_dt_must_exist,
        device_worker_must_exist,
        device_perms_group_must_exist,
        dt_perms_group_must_exist,
    )
)
