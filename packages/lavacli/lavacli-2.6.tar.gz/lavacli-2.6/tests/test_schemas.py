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

import pytest
from voluptuous import MultipleInvalid, Schema

from lavacli import schemas
from lavacli.utils import safe_yaml


def test_user_group_must_exist():
    config = """groups:
  group1:
users:
  user1:
    groups:
    - group2
"""
    schema = Schema(schemas.user_group_must_exist)
    with pytest.raises(MultipleInvalid) as exc:
        schema(safe_yaml.load(config))
    assert exc.value.msg == "Group must exist"
    assert exc.value.path == ["users", "user1", "groups", "group2"]


def test_device_dt_must_exist():
    config = """device_types:
  qemu:
devices:
  docker-01:
    device_type: docker
"""
    schema = Schema(schemas.device_dt_must_exist)
    with pytest.raises(MultipleInvalid) as exc:
        schema(safe_yaml.load(config))
    assert exc.value.msg == "Device type must exist"
    assert exc.value.path == ["devices", "docker-01", "device_type", "docker"]


def test_device_worker_must_exist():
    config = """device_types:
  qemu:
devices:
  docker-01:
    worker: worker01
workers:
  worker02:
"""
    schema = Schema(schemas.device_worker_must_exist)
    with pytest.raises(MultipleInvalid) as exc:
        schema(safe_yaml.load(config))
    assert exc.value.msg == "Worker must exist"
    assert exc.value.path == ["devices", "docker-01", "worker", "worker01"]


def test_device_perms_group_must_exist():
    config = """devices:
  docker-01:
    permissions:
    - name: change_device
      group: group2
groups:
  group1:
"""
    schema = Schema(schemas.device_perms_group_must_exist)
    with pytest.raises(MultipleInvalid) as exc:
        schema(safe_yaml.load(config))
    assert exc.value.msg == "Group must exist"
    assert exc.value.path == [
        "devices",
        "docker-01",
        "permissions",
        {"name": "change_device", "group": "group2"},
    ]


def test_dt_perms_group_must_exist():
    config = """device_types:
  docker:
    permissions:
    - name: change_devicetype
      group: group2
groups:
  group1:
"""
    schema = Schema(schemas.dt_perms_group_must_exist)
    with pytest.raises(MultipleInvalid) as exc:
        schema(safe_yaml.load(config))
    assert exc.value.msg == "Group must exist"
    assert exc.value.path == [
        "devices_types",
        "docker",
        "permissions",
        {"name": "change_devicetype", "group": "group2"},
    ]
