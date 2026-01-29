import sys
import xmlrpc.client

import pytest
import ruamel.yaml

from lavacli import main
from lavacli.commands.lab import ConfigFile
from lavacli.utils import safe_yaml


@pytest.fixture
def mock_get():
    class GetData:
        def __init__(self):
            self.system_version_2023_2 = {
                "request": "system.version",
                "args": (),
                "ret": 2023.2,
            }
            self.system_version_2023_3 = {
                "request": "system.version",
                "args": (),
                "ret": 2023.3,
            }
            self.system_version_2023_05 = {
                "request": "system.version",
                "args": (),
                "ret": 2023.05,
            }
            self.auth_groups_list_empty = {
                "request": "auth.groups.list",
                "args": (),
                "ret": [],
            }
            self.auth_groups_list = {
                "request": "auth.groups.list",
                "args": (),
                "ret": ["group1", "group2"],
            }
            self.auth_groups_show_group1 = {
                "request": "auth.groups.show",
                "args": ("group1",),
                "ret": {
                    "id": 5,
                    "name": "group1",
                    "permissions": ["auth.user.add_user"],
                    "users": ["user1"],
                },
            }
            self.auth_groups_show_group2 = {
                "request": "auth.groups.show",
                "args": ("group2",),
                "ret": {
                    "id": 6,
                    "name": "group2",
                    "permissions": ["auth.user.delete_user"],
                    "users": ["user2"],
                },
            }
            self.auth_groups_show_group3 = {
                "request": "auth.groups.show",
                "args": ("group3",),
                "ret": {
                    "id": 9,
                    "name": "group3",
                    "permissions": ["auth.group.add_group"],
                    "users": ["user3"],
                },
            }
            self.auth_users_list_empty = {
                "request": "auth.users.list",
                "args": (),
                "ret": [],
            }
            self.auth_users_list = {
                "request": "auth.users.list",
                "args": (),
                "ret": [
                    {
                        "username": "user1",
                        "last_name": "",
                        "first_name": "cheese",
                        "is_superuser": False,
                        "is_staff": False,
                        "is_active": True,
                    },
                    {
                        "username": "user2",
                        "last_name": "",
                        "first_name": "",
                        "is_superuser": False,
                        "is_staff": False,
                        "is_active": True,
                    },
                ],
            }
            self.auth_users_show_user1 = {
                "request": "auth.users.show",
                "args": ("user1",),
                "ret": {
                    "email": "",
                    "first_name": "",
                    "groups": ["group1"],
                    "permissions": ["lava_scheduler_app.device.add_device"],
                    "id": 4,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "last_login": None,
                    "last_name": "",
                    "username": "user1",
                },
            }
            self.auth_users_show_user2 = {
                "request": "auth.users.show",
                "args": ("user2",),
                "ret": {
                    "email": "",
                    "first_name": "",
                    "groups": ["group2"],
                    "permissions": ["lava_scheduler_app.device.delete_device"],
                    "id": 5,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "last_login": None,
                    "last_name": "",
                    "username": "user2",
                },
            }
            self.auth_users_show_user3 = {
                "request": "auth.users.show",
                "args": ("user3",),
                "ret": {
                    "email": "",
                    "first_name": "",
                    "groups": ["group3"],
                    "permissions": [],
                    "id": 14,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "last_login": None,
                    "last_name": "",
                    "username": "user3",
                },
            }
            self.auth_users_show_user3_ldap = {
                "request": "auth.users.show",
                "args": ("user3",),
                "ret": {
                    "email": "first.last@linaro,org",
                    "first_name": "First",
                    "groups": ["group3"],
                    "permissions": [],
                    "id": 14,
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "last_login": None,
                    "last_name": "Last",
                    "username": "user3",
                },
            }
            self.scheduler_device_types_list_empty = {
                "request": "scheduler.device_types.list",
                "args": (False,),
                "ret": [],
            }
            self.scheduler_device_types_list = {
                "request": "scheduler.device_types.list",
                "args": (False,),
                "ret": [
                    {
                        "name": "docker",
                        "devices": 2,
                        "installed": True,
                        "template": True,
                    },
                    {"name": "qemu", "devices": 2, "installed": True, "template": True},
                ],
            }
            self.scheduler_device_types_show_docker = {
                "request": "scheduler.device_types.show",
                "args": ("docker",),
                "ret": {
                    "name": "docker",
                    "description": "",
                    "display": True,
                    "health_disabled": False,
                    "health_denominator": "hours",
                    "health_frequency": 24,
                    "aliases": [],
                    "devices": ["docker-01", "docker-02"],
                    "default_template": True,
                    "permissions": [
                        {"name": "change_devicetype", "group": "group1"},
                    ],
                },
            }
            self.scheduler_device_types_show_docker_custom_template = {
                "request": "scheduler.device_types.show",
                "args": ("docker",),
                "ret": {
                    "name": "docker",
                    "description": "",
                    "display": True,
                    "health_disabled": False,
                    "health_denominator": "hours",
                    "health_frequency": 24,
                    "aliases": [],
                    "devices": ["docker-01", "docker-02"],
                    "default_template": False,
                    "permissions": [
                        {"name": "change_devicetype", "group": "group1"},
                    ],
                },
            }
            self.scheduler_device_types_get_health_check_docker = {
                "request": "scheduler.device_types.get_health_check",
                "args": ("docker",),
                "ret": "hc-definition",
            }
            self.scheduler_device_types_get_health_check_docker_empty = {
                "request": "scheduler.device_types.get_health_check",
                "args": ("docker",),
                "ret": {"fault_code": 404},
            }
            self.scheduler_device_types_get_template_docker = {
                "request": "scheduler.device_types.get_template",
                "args": ("docker",),
                "ret": "template content",
            }
            self.scheduler_device_types_show_qemu = {
                "request": "scheduler.device_types.show",
                "args": ("qemu",),
                "ret": {
                    "name": "qemu",
                    "description": None,
                    "display": True,
                    "health_disabled": False,
                    "health_denominator": "hours",
                    "health_frequency": 24,
                    "aliases": [],
                    "devices": ["qemu-01", "qemu-02"],
                    "default_template": True,
                },
            }
            self.scheduler_device_types_show_qemu_custom_template = {
                "request": "scheduler.device_types.show",
                "args": ("qemu",),
                "ret": {
                    "name": "qemu",
                    "description": None,
                    "display": True,
                    "health_disabled": False,
                    "health_denominator": "hours",
                    "health_frequency": 24,
                    "aliases": [],
                    "devices": ["qemu-01", "qemu-02"],
                    "default_template": False,
                },
            }
            self.scheduler_device_types_get_health_check_qemu = {
                "request": "scheduler.device_types.get_health_check",
                "args": ("qemu",),
                "ret": "hc-definition",
            }
            self.scheduler_device_types_show_bbb = {
                "request": "scheduler.device_types.show",
                "args": ("bbb",),
                "ret": {
                    "name": "bbb",
                    "description": None,
                    "display": True,
                    "health_disabled": False,
                    "health_denominator": "hours",
                    "health_frequency": 24,
                    "aliases": [],
                    "devices": [],
                    "default_template": True,
                },
            }
            self.scheduler_device_types_get_health_check_bbb = {
                "request": "scheduler.device_types.get_health_check",
                "args": ("bbb",),
                "ret": "hc-definition",
            }
            self.scheduler_device_types_get_template_qemu = {
                "request": "scheduler.device_types.get_template",
                "args": ("qemu",),
                "ret": "template content",
            }
            self.scheduler_workers_list_empty = {
                "request": "scheduler.workers.list",
                "args": (True,),
                "ret": [],
            }
            self.scheduler_workers_list_empty_2023_2 = {
                "request": "scheduler.workers.list",
                "args": (),
                "ret": [],
            }
            self.scheduler_workers_list = {
                "request": "scheduler.workers.list",
                "args": (True,),
                "ret": ["worker01", "worker02"],
            }
            self.scheduler_workers_list_all = {
                "request": "scheduler.workers.list",
                "args": (True,),
                "ret": ["worker01", "worker02"],
            }
            self.scheduler_workers_list_all_2023_2 = {
                "request": "scheduler.workers.list",
                "args": (),
                "ret": ["worker01", "worker02"],
            }
            self.scheduler_workers_show_worker01 = {
                "request": "scheduler.workers.show",
                "args": ("worker01",),
                "ret": {
                    "hostname": "worker01",
                    "description": "",
                    "state": "Online",
                    "health": "Active",
                    "devices": ["docker-01", "qemu-01"],
                    "job_limit": 0,
                    "version": "2023.03",
                    "default_config": True,
                    "default_env": True,
                    "default_env_dut": True,
                },
            }
            self.scheduler_workers_show_retired_worker01 = {
                "request": "scheduler.workers.show",
                "args": ("worker01",),
                "ret": {
                    "hostname": "worker01",
                    "description": "",
                    "state": "Online",
                    "health": "Retired",
                    "devices": ["docker-01", "qemu-01"],
                    "job_limit": 0,
                    "version": "2023.03",
                    "default_config": True,
                    "default_env": True,
                    "default_env_dut": True,
                },
            }
            self.scheduler_workers_show_worker01_custom_config = {
                "request": "scheduler.workers.show",
                "args": ("worker01",),
                "ret": {
                    "hostname": "worker01",
                    "description": "",
                    "state": "Online",
                    "health": "Active",
                    "devices": ["docker-01", "qemu-01"],
                    "job_limit": 0,
                    "version": "2023.03",
                    "default_config": False,
                    "default_env": True,
                    "default_env_dut": True,
                },
            }
            self.scheduler_workers_get_config_worker01 = {
                "request": "scheduler.workers.get_config",
                "args": ("worker01",),
                "ret": "config content",
            }
            self.scheduler_workers_show_worker01_custom_env = {
                "request": "scheduler.workers.show",
                "args": ("worker01",),
                "ret": {
                    "hostname": "worker01",
                    "description": "",
                    "state": "Online",
                    "health": "Active",
                    "devices": ["docker-01", "qemu-01"],
                    "job_limit": 0,
                    "version": "2023.03",
                    "default_config": True,
                    "default_env": False,
                    "default_env_dut": True,
                },
            }
            self.scheduler_workers_get_env_worker01 = {
                "request": "scheduler.workers.get_env",
                "args": ("worker01",),
                "ret": "env content",
            }
            self.scheduler_workers_show_worker01_custom_env_dut = {
                "request": "scheduler.workers.show",
                "args": ("worker01",),
                "ret": {
                    "hostname": "worker01",
                    "description": "",
                    "state": "Online",
                    "health": "Active",
                    "devices": ["docker-01", "qemu-01"],
                    "job_limit": 0,
                    "version": "2023.03",
                    "default_config": True,
                    "default_env": True,
                    "default_env_dut": False,
                },
            }
            self.scheduler_workers_get_env_dut_worker01 = {
                "request": "scheduler.workers.get_env_dut",
                "args": ("worker01",),
                "ret": "env-dut content",
            }
            self.scheduler_workers_show_worker02 = {
                "request": "scheduler.workers.show",
                "args": ("worker02",),
                "ret": {
                    "hostname": "worker02",
                    "description": "",
                    "state": "Offline",
                    "health": "Active",
                    "devices": ["docker-02", "qemu-02"],
                    "job_limit": 0,
                    "version": "2023.02.0042.g2755aa13a",
                    "default_config": True,
                    "default_env": True,
                    "default_env_dut": True,
                },
            }
            self.scheduler_workers_show_worker03 = {
                "request": "scheduler.workers.show",
                "args": ("worker03",),
                "ret": {
                    "hostname": "worker03",
                    "description": "",
                    "state": "Offline",
                    "health": "Active",
                    "devices": [],
                    "job_limit": 0,
                    "version": None,
                    "default_config": True,
                    "default_env": True,
                    "default_env_dut": True,
                },
            }
            self.scheduler_devices_list_empty = {
                "request": "scheduler.devices.list",
                "args": (True,),
                "ret": [],
            }
            self.scheduler_devices_list = {
                "request": "scheduler.devices.list",
                "args": (True,),
                "ret": [
                    {
                        "hostname": "docker-01",
                        "type": "docker",
                        "health": "Good",
                        "state": "Idle",
                        "current_job": None,
                        "pipeline": True,
                    },
                    {
                        "hostname": "docker-02",
                        "type": "docker",
                        "health": "Unknown",
                        "state": "Idle",
                        "current_job": None,
                        "pipeline": True,
                    },
                    {
                        "hostname": "qemu-01",
                        "type": "qemu",
                        "health": "Good",
                        "state": "Idle",
                        "current_job": None,
                        "pipeline": True,
                    },
                    {
                        "hostname": "qemu-02",
                        "type": "qemu",
                        "health": "Unknown",
                        "state": "Idle",
                        "current_job": None,
                        "pipeline": True,
                    },
                ],
            }
            self.scheduler_devices_show_docker_01 = {
                "request": "scheduler.devices.show",
                "args": ("docker-01",),
                "ret": {
                    "hostname": "docker-01",
                    "device_type": "docker",
                    "health": "Good",
                    "state": "Idle",
                    "health_job": True,
                    "description": "Created automatically by LAVA.",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker01",
                    "current_job": None,
                    "tags": ["docker-01", "worker"],
                    "permissions": [
                        {"name": "change_devicetype", "group": "group1"},
                    ],
                },
            }
            self.scheduler_devices_get_dictionary_docker_01 = {
                "request": "scheduler.devices.get_dictionary",
                "args": ("docker-01",),
                "ret": "yaml_dict",
            }
            self.scheduler_devices_show_docker_02 = {
                "request": "scheduler.devices.show",
                "args": ("docker-02",),
                "ret": {
                    "hostname": "docker-02",
                    "device_type": "docker",
                    "health": "Unknown",
                    "state": "Idle",
                    "health_job": True,
                    "description": "Created automatically by LAVA.",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker02",
                    "current_job": None,
                    "tags": ["docker-02", "docker-worker"],
                },
            }
            self.scheduler_devices_get_dictionary_docker_02 = {
                "request": "scheduler.devices.get_dictionary",
                "args": ("docker-02",),
                "ret": "yaml_dict",
            }
            self.scheduler_devices_show_qemu_01 = {
                "request": "scheduler.devices.show",
                "args": ("qemu-01",),
                "ret": {
                    "hostname": "qemu-01",
                    "device_type": "qemu",
                    "health": "Good",
                    "state": "Idle",
                    "health_job": True,
                    "description": "Created automatically by LAVA.",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker01",
                    "current_job": None,
                    "tags": [],
                },
            }
            self.scheduler_devices_show_retired_qemu_01 = {
                "request": "scheduler.devices.show",
                "args": ("qemu-01",),
                "ret": {
                    "hostname": "qemu-01",
                    "device_type": "qemu",
                    "health": "Retired",
                    "state": "Idle",
                    "health_job": True,
                    "description": "Created automatically by LAVA.",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker01",
                    "current_job": None,
                    "tags": [],
                },
            }
            self.scheduler_devices_get_dictionary_qemu_01 = {
                "request": "scheduler.devices.get_dictionary",
                "args": ("qemu-01",),
                "ret": "yaml_dict",
            }
            self.scheduler_devices_show_qemu_02 = {
                "request": "scheduler.devices.show",
                "args": ("qemu-02",),
                "ret": {
                    "hostname": "qemu-02",
                    "device_type": "qemu",
                    "health": "Unknown",
                    "state": "Idle",
                    "health_job": True,
                    "description": "Created automatically by LAVA.",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker02",
                    "current_job": None,
                    "tags": [],
                },
            }
            self.scheduler_devices_get_dictionary_qemu_02 = {
                "request": "scheduler.devices.get_dictionary",
                "args": ("qemu-02",),
                "ret": "yaml_dict",
            }
            self.scheduler_devices_show_qemu_03 = {
                "request": "scheduler.devices.show",
                "args": ("qemu-03",),
                "ret": {
                    "hostname": "qemu-03",
                    "device_type": "qemu",
                    "health": "Unknown",
                    "state": "Idle",
                    "health_job": True,
                    "description": "qemu03",
                    "pipeline": True,
                    "has_device_dict": True,
                    "worker": "worker01",
                    "current_job": None,
                    "tags": [],
                },
            }
            self.scheduler_devices_get_dictionary_qemu_03 = {
                "request": "scheduler.devices.get_dictionary",
                "args": ("qemu-03",),
                "ret": "yaml_dict",
            }

    return GetData()


@pytest.fixture
def mock_post():
    class PostData:
        def __init__(self):
            self.auth_groups_add_group3 = {
                "request": "auth.groups.add",
                "args": ("group3",),
                "ret": None,
            }
            self.auth_groups_delete_group2 = {
                "request": "auth.groups.delete",
                "args": ("group2",),
                "ret": None,
            }
            self.auth_groups_perms_add_group1 = {
                "request": "auth.groups.perms.add",
                "args": ("group1", "auth", "user", "delete_user"),
                "ret": None,
            }
            self.auth_groups_perms_delete_group1 = {
                "request": "auth.groups.perms.delete",
                "args": ("group1", "auth", "user", "add_user"),
                "ret": None,
            }
            self.auth_users_add_user3 = {
                "request": "auth.users.add",
                "args": ("user3", None, None, None, True, False, False, False),
                "ret": None,
            }
            self.auth_users_add_user3_ldap = {
                "request": "auth.users.add",
                "args": ("user3", None, None, None, True, False, False, True),
                "ret": None,
            }
            self.auth_users_delete_user2 = {
                "request": "auth.users.delete",
                "args": ("user2",),
                "ret": None,
            }
            self.auth_users_perms_add_user1 = {
                "request": "auth.users.perms.add",
                "args": ("user1", "lava_scheduler_app", "device", "delete_device"),
                "ret": None,
            }
            self.auth_users_update_user1 = {
                "request": "auth.users.update",
                "args": ("user1", None, None, None, None, None, None),
                "ret": None,
            }
            self.auth_users_perms_delete_user1 = {
                "request": "auth.users.perms.delete",
                "args": ("user1", "lava_scheduler_app", "device", "add_device"),
                "ret": None,
            }
            self.auth_users_update_user2 = {
                "request": "auth.users.update",
                "args": ("user2", "first", "last", "user2@email.io", False, True, True),
                "ret": None,
            }
            self.auth_users_groups_add_user1_group2 = {
                "request": "auth.users.groups.add",
                "args": ("user1", "group2"),
                "ret": None,
            }
            self.auth_users_groups_delete_user1_group1 = {
                "request": "auth.users.groups.delete",
                "args": ("user1", "group1"),
                "ret": None,
            }
            self.scheduler_device_types_add_bbb = {
                "request": "scheduler.device_types.add",
                "args": ("bbb", None, True, None, 24, "hours"),
                "ret": None,
            }
            self.scheduler_device_types_hide_qemu = {
                "request": "scheduler.device_types.update",
                "args": ("qemu", None, False, None, None, None, None),
                "ret": None,
            }
            self.scheduler_device_types_update_docker = {
                "request": "scheduler.device_types.update",
                "args": ("docker", "new", False, None, 12, "jobs", True),
                "ret": None,
            }
            self.scheduler_device_types_set_health_check_docker_add = {
                "request": "scheduler.device_types.set_health_check",
                "args": ("docker", "hc-definition"),
                "ret": None,
            }
            self.scheduler_device_types_set_health_check_docker_del = {
                "request": "scheduler.device_types.set_health_check",
                "args": ("docker", None),
                "ret": None,
            }
            self.scheduler_device_types_set_health_check_docker_update = {
                "request": "scheduler.device_types.set_health_check",
                "args": ("docker", "new-hc-definition"),
                "ret": None,
            }
            self.scheduler_device_types_set_template_docker = {
                "request": "scheduler.device_types.set_template",
                "args": ("docker", "new template definition"),
                "ret": None,
            }
            self.scheduler_device_types_perms_add_docker = {
                "request": "scheduler.device_types.perms_add",
                "args": ("docker", "group1", "view_devicetype"),
                "ret": None,
            }
            self.scheduler_device_types_perms_delete_docker = {
                "request": "scheduler.device_types.perms_delete",
                "args": ("docker", "group1", "change_devicetype"),
                "ret": None,
            }
            self.scheduler_workers_add_worker03 = {
                "request": "scheduler.workers.add",
                "args": ("worker03", "", False),
                "ret": None,
            }
            self.scheduler_workers_delete_worker02 = {
                "request": "scheduler.workers.delete",
                "args": ("worker02",),
                "ret": None,
            }
            self.scheduler_workers_update_worker01 = {
                "request": "scheduler.workers.update",
                "args": ("worker01", "new", None, 10),
                "ret": None,
            }
            self.scheduler_workers_retire_worker01 = {
                "request": "scheduler.workers.update",
                "args": ("worker01", None, "RETIRED", None),
                "ret": None,
            }
            self.scheduler_workers_unretire_worker01 = {
                "request": "scheduler.workers.update",
                "args": ("worker01", None, "ACTIVE", None),
                "ret": None,
            }
            self.scheduler_workers_set_config_worker01 = {
                "request": "scheduler.workers.set_config",
                "args": ("worker01", "local config content"),
                "ret": True,
            }
            self.scheduler_workers_set_env_worker01 = {
                "request": "scheduler.workers.set_env",
                "args": ("worker01", "local env content"),
                "ret": True,
            }
            self.scheduler_workers_set_env_dut_worker01 = {
                "request": "scheduler.workers.set_env_dut",
                "args": ("worker01", "local env-dut content"),
                "ret": True,
            }
            self.scheduler_devices_add_qemu_03 = {
                "request": "scheduler.devices.add",
                "args": (
                    "qemu-03",
                    "qemu",
                    "worker01",
                    None,
                    None,
                    None,
                    None,
                    "qemu03",
                ),
                "ret": None,
            }
            self.scheduler_devices_delete_qemu_02 = {
                "request": "scheduler.devices.delete",
                "args": ("qemu-02",),
                "ret": None,
            }
            self.scheduler_devices_update_qemu_01 = {
                "request": "scheduler.devices.update",
                "args": (
                    "qemu-01",
                    "worker02",
                    None,
                    None,
                    None,
                    None,
                    "qemu01",
                    "qemu-aarch64",
                ),
                "ret": None,
            }
            self.scheduler_devices_retire_qemu_01 = {
                "request": "scheduler.devices.update",
                "args": (
                    "qemu-01",
                    None,
                    None,
                    None,
                    None,
                    "RETIRED",
                    None,
                    None,
                ),
                "ret": None,
            }
            self.scheduler_devices_unretire_qemu_01 = {
                "request": "scheduler.devices.update",
                "args": (
                    "qemu-01",
                    None,
                    None,
                    None,
                    None,
                    "UNKNOWN",
                    None,
                    None,
                ),
                "ret": None,
            }
            self.scheduler_devices_set_dictionary_docker_01 = {
                "request": "scheduler.devices.set_dictionary",
                "args": ("docker-01", "new_yaml_dict"),
                "ret": False,
            }
            self.scheduler_devices_tags_add_docker_01 = {
                "request": "scheduler.devices.tags.add",
                "args": ("docker-01", "worker01"),
                "ret": None,
            }
            self.scheduler_devices_tags_delete_docker_01 = {
                "request": "scheduler.devices.tags.delete",
                "args": ("docker-01", "docker-01"),
                "ret": None,
            }
            self.scheduler_devices_perms_add_docker_01 = {
                "request": "scheduler.devices.perms_add",
                "args": ("docker-01", "group1", "view_devicetype"),
                "ret": None,
            }
            self.scheduler_devices_perms_delete_docker_01 = {
                "request": "scheduler.devices.perms_delete",
                "args": ("docker-01", "group1", "change_devicetype"),
                "ret": None,
            }

    return PostData()


@pytest.fixture
def config_file(tmp_path):
    return tmp_path / "lab.yaml"


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "lab"


@pytest.fixture
def config_def():
    return """device_types:
  docker:
    permissions:
    - name: change_devicetype
      group: group1
  qemu:
devices:
  docker-01:
    device_type: docker
    worker: worker01
    description: Created automatically by LAVA.
    tags:
    - docker-01
    - worker
    permissions:
    - name: change_devicetype
      group: group1
  docker-02:
    device_type: docker
    worker: worker02
    description: Created automatically by LAVA.
    tags:
    - docker-02
    - docker-worker
  qemu-01:
    device_type: qemu
    worker: worker01
    description: Created automatically by LAVA.
  qemu-02:
    device_type: qemu
    worker: worker02
    description: Created automatically by LAVA.
groups:
  group1:
    permissions:
    - auth.user.add_user
  group2:
    permissions:
    - auth.user.delete_user
users:
  user1:
    groups:
    - group1
    permissions:
    - lava_scheduler_app.device.add_device
  user2:
    groups:
    - group2
    permissions:
    - lava_scheduler_app.device.delete_device
workers:
  worker01:
  worker02:
"""


def test_lab_import_empty(setup, monkeypatch, capsys, config_file, mock_get):
    monkeypatch.setattr(sys, "argv", ["lavacli", "lab", "import", str(config_file)])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list_empty,
            mock_get.auth_users_list_empty,
            mock_get.scheduler_device_types_list_empty,
            mock_get.scheduler_workers_list_empty,
            mock_get.scheduler_devices_list_empty,
        ],
    )

    expected_def = """device_types: {}
devices: {}
groups: {}
users: {}
workers: {}
"""

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_file.exists()
    yaml = ruamel.yaml.YAML(typ="safe")
    assert yaml.load(config_file.read_text()) == yaml.load(expected_def)


def test_lab_import_groups_users_unsupported(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(sys, "argv", ["lavacli", "lab", "import", str(config_file)])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
            mock_get.scheduler_device_types_list_empty,
            mock_get.scheduler_workers_list_empty_2023_2,
            mock_get.scheduler_devices_list_empty,
        ],
    )

    expected_def = """device_types: {}
devices: {}
groups: {}
users: {}
workers: {}
"""

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_file.exists()
    yaml = ruamel.yaml.YAML(typ="safe")
    assert yaml.load(config_file.read_text()) == yaml.load(expected_def)


def test_lab_import_config_file(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(sys, "argv", ["lavacli", "lab", "import", str(config_file)])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_file.exists()
    yaml = ruamel.yaml.YAML(typ="safe")
    assert yaml.load(config_file.read_text()) == yaml.load(config_def)

    config_dir = config_file.parent / config_file.name.split(".")[0]
    assert (config_dir / "devices/docker-01.jinja2").exists()
    assert (config_dir / "devices/docker-02.jinja2").exists()
    assert (config_dir / "devices/qemu-01.jinja2").exists()
    assert (config_dir / "devices/qemu-02.jinja2").exists()
    assert not (config_dir / "device-types/docker.jinja2").exists()
    assert not (config_dir / "device-types/qemu.jinja2").exists()
    assert (config_dir / "health-checks/docker.yaml").exists()
    assert (config_dir / "health-checks/qemu.yaml").exists()

    config = ConfigFile(config_file)
    assert config.is_yaml_file()
    assert not config.is_dir()
    assert config.load() == safe_yaml.load(config_def)


def test_lab_import_config_dir(
    setup, monkeypatch, capsys, config_dir, config_def, mock_get
):
    monkeypatch.setattr(sys, "argv", ["lavacli", "lab", "import", str(config_dir)])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert (config_dir / "device-types.yaml").exists()
    assert (config_dir / "devices.yaml").exists()
    assert (config_dir / "groups.yaml").exists()
    assert (config_dir / "users.yaml").exists()
    assert (config_dir / "workers.yaml").exists()

    config = ConfigFile(config_dir)
    assert config.is_dir()
    assert not config.is_yaml_file()
    assert config.load() == safe_yaml.load(config_def)


def test_lab_import_config_file_exclude_groups(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "groups" not in config
    assert "groups" not in config["users"]["user1"]
    assert config["device_types"]["docker"] is None
    assert "permissions" not in config["devices"]["docker-01"]


def test_lab_import_config_file_exclude_users(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "users" not in config


def test_lab_import_config_file_exclude_permissions(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "permissions", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert config["groups"]["group1"] is None
    assert "permissions" not in config["users"]["user1"]
    assert config["device_types"]["docker"] is None
    assert "permissions" not in config["devices"]["docker-01"]


def test_lab_import_config_dir_exclude_groups(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "groups", str(config_dir)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_dir).load()
    assert "groups" not in config
    assert "groups" not in config["users"]["user1"]
    assert config["device_types"]["docker"] is None
    assert "permissions" not in config["devices"]["docker-01"]


def test_lab_import_config_dir_exclude_users(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "users", str(config_dir)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_dir).load()
    assert "users" not in config


def test_lab_import_config_dir_exclude_permissions(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--exclude", "permissions", str(config_dir)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_dir).load()
    assert config["groups"]["group1"] is None
    assert "permissions" not in config["users"]["user1"]
    assert config["device_types"]["docker"] is None
    assert "permissions" not in config["devices"]["docker-01"]


def test_lab_import_custom_template(setup, monkeypatch, capsys, config_file, mock_get):
    monkeypatch.setattr(sys, "argv", ["lavacli", "lab", "import", str(config_file)])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list_empty,
            mock_get.auth_users_list_empty,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker_custom_template,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_get_template_docker,
            mock_get.scheduler_device_types_show_qemu_custom_template,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_device_types_get_template_qemu,
            mock_get.scheduler_workers_list_empty,
            mock_get.scheduler_devices_list_empty,
        ],
    )

    expected_def = """device_types:
  docker:
    permissions:
    - name: change_devicetype
      group: group1
  qemu:
devices: {}
groups: {}
users: {}
workers: {}
"""

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_file.exists()
    yaml = ruamel.yaml.YAML(typ="safe")
    assert yaml.load(config_file.read_text()) == yaml.load(expected_def)

    config_dir = config_file.parent / config_file.name.split(".")[0]
    assert (config_dir / "device-types/docker.jinja2").exists()
    assert (config_dir / "device-types/qemu.jinja2").exists()


def test_lab_import_devices_dependency_error(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--resources", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
        ],
    )

    assert main() == 1
    assert (
        capsys.readouterr()[1]
        == "'--resources devices' needs '--resources device-types --resources workers --resources groups'\n"
    )


def test_lab_import_device_types_dependency_error(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--resources", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
        ],
    )

    assert main() == 1
    assert (
        capsys.readouterr()[1]
        == "'--resources device-types' needs '--resources groups'\n"
    )


def test_lab_import_users_dependency_error(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--resources", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
        ],
    )

    assert main() == 1
    assert capsys.readouterr()[1] == "'--resources users' needs '--resources groups'\n"


def test_lab_import_config_file_groups(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--resources", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "groups" in config
    assert "users" not in config
    assert "devices" not in config
    assert "device_types" not in config
    assert "workers" not in config


def test_lab_import_config_file_users(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "users",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "users" in config
    assert "groups" in config
    assert "devices" not in config
    assert "device_types" not in config
    assert "workers" not in config


def test_lab_import_config_file_devices(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "devices",
            "--resources",
            "device-types",
            "--resources",
            "groups",
            "--resources",
            "workers",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "devices" in config
    assert "device_types" in config
    assert "workers" in config
    assert "groups" in config
    assert "users" not in config


def test_lab_import_config_file_device_types(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "device-types",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "device_types" in config
    assert "groups" in config
    assert "workers" not in config
    assert "users" not in config
    assert "devices" not in config


def test_lab_import_config_file_workers(
    setup, monkeypatch, capsys, config_file, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "workers",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    config = ConfigFile(config_file).load()
    assert "workers" in config
    assert "users" not in config
    assert "groups" not in config
    assert "devices" not in config
    assert "device_types" not in config


def test_lab_import_config_dir_groups(setup, monkeypatch, capsys, config_dir, mock_get):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "import", "--resources", "groups", str(config_dir)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert not (config_dir / "device-types.yaml").exists()
    assert not (config_dir / "devices.yaml").exists()
    assert (config_dir / "groups.yaml").exists()
    assert not (config_dir / "users.yaml").exists()
    assert not (config_dir / "workers.yaml").exists()


def test_lab_import_config_dir_users(setup, monkeypatch, capsys, config_dir, mock_get):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "users",
            "--resources",
            "groups",
            str(config_dir),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert not (config_dir / "device-types.yaml").exists()
    assert not (config_dir / "devices.yaml").exists()
    assert (config_dir / "groups.yaml").exists()
    assert (config_dir / "users.yaml").exists()
    assert not (config_dir / "workers.yaml").exists()


def test_lab_import_config_dir_devices(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "devices",
            "--resources",
            "device-types",
            "--resources",
            "groups",
            "--resources",
            "workers",
            str(config_dir),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert (config_dir / "device-types.yaml").exists()
    assert (config_dir / "devices.yaml").exists()
    assert (config_dir / "groups.yaml").exists()
    assert not (config_dir / "users.yaml").exists()
    assert (config_dir / "workers.yaml").exists()


def test_lab_import_config_dir_device_types(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "device-types",
            "--resources",
            "groups",
            str(config_dir),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert (config_dir / "device-types.yaml").exists()
    assert not (config_dir / "devices.yaml").exists()
    assert (config_dir / "groups.yaml").exists()
    assert not (config_dir / "users.yaml").exists()
    assert not (config_dir / "workers.yaml").exists()


def test_lab_import_config_dir_workers(
    setup, monkeypatch, capsys, config_dir, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "import",
            "--resources",
            "workers",
            str(config_dir),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    assert main() == 0
    assert capsys.readouterr()[1] == ""

    assert config_dir.exists()
    assert not (config_dir / "device-types.yaml").exists()
    assert not (config_dir / "devices.yaml").exists()
    assert not (config_dir / "groups.yaml").exists()
    assert not (config_dir / "users.yaml").exists()
    assert (config_dir / "workers.yaml").exists()


def test_lab_apply_groups_unsupported(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_groups_no_change(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_groups_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_post.auth_groups_add_group3,
            mock_get.auth_groups_show_group3,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["groups"]["group3"] = {"permissions": ["auth.group.add_group"]}
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n  \x1b[33m* group3\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_groups_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "groups",
            "--delete",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_post.auth_groups_delete_group2,
        ],
    )

    data = safe_yaml.load(config_def)
    del data["groups"]["group2"]
    del data["users"]["user2"]["groups"]
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "  \x1b[91m* group2\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_groups_perms_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_post.auth_groups_perms_add_group1,
            mock_get.auth_groups_show_group2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["groups"]["group1"]["permissions"].append("auth.user.delete_user")
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n    \x1b[33m-> permissions\x1b[0m\n      \x1b[32m+ auth.user.delete_user\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_groups_perms_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "groups", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_post.auth_groups_perms_delete_group1,
            mock_get.auth_groups_show_group2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["groups"]["group1"]["permissions"].pop()
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n    \x1b[33m-> permissions\x1b[0m\n      \x1b[91m- auth.user.add_user\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_unsupported(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_no_change(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n  \x1b[32m* user2\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_post.auth_users_add_user3,
            mock_get.auth_users_show_user3,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user3"] = {"groups": ["group3"], "permissions": []}
    data["groups"]["group3"] = None
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n  \x1b[32m* user2\x1b[0m\n  \x1b[33m* user3\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_add_ldap(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_post.auth_users_add_user3_ldap,
            mock_get.auth_users_show_user3_ldap,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user3"] = {"ldap": True, "groups": ["group3"], "permissions": []}
    data["groups"]["group3"] = None
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n  \x1b[32m* user2\x1b[0m\n  \x1b[33m* user3\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "users",
            "--delete",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_post.auth_users_delete_user2,
        ],
    )

    data = safe_yaml.load(config_def)
    del data["users"]["user2"]
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "  \x1b[91m* user2\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_users_update(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_get.auth_users_show_user2,
            mock_post.auth_users_update_user2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user2"]["first_name"] = "first"
    data["users"]["user2"]["last_name"] = "last"
    data["users"]["user2"]["email"] = "user2@email.io"
    data["users"]["user2"]["is_active"] = False
    data["users"]["user2"]["is_staff"] = True
    data["users"]["user2"]["is_superuser"] = True
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n  \x1b[32m* user2\x1b[0m\n    \x1b[33m-> last_name: '' => 'last'\x1b[0m\n    \x1b[33m-> first_name: '' => 'first'\x1b[0m\n    \x1b[33m-> email: '' => 'user2@email.io'\x1b[0m\n    \x1b[33m-> is_superuser: 'False' => 'True'\x1b[0m\n    \x1b[33m-> is_staff: 'False' => 'True'\x1b[0m\n    \x1b[33m-> is_active: 'True' => 'False'\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_groups_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_post.auth_users_groups_add_user1_group2,
            mock_get.auth_users_show_user2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user1"]["groups"].append("group2")
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n    \x1b[33m-> groups\x1b[0m\n      \x1b[32m+ group2\x1b[0m\n  \x1b[32m* user2\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_groups_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_post.auth_users_groups_delete_user1_group1,
            mock_get.auth_users_show_user2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user1"]["groups"].pop()
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n    \x1b[33m-> groups\x1b[0m\n      \x1b[91m- group1\x1b[0m\n  \x1b[32m* user2\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_perms_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_post.auth_users_perms_add_user1,
            mock_get.auth_users_show_user2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user1"]["permissions"].append(
        "lava_scheduler_app.device.delete_device"
    )
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n    \x1b[33m-> permissions\x1b[0m\n      \x1b[32m+ lava_scheduler_app.device.delete_device\x1b[0m\n  \x1b[32m* user2\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_users_perms_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "users", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_users_list,
            mock_get.auth_users_show_user1,
            mock_post.auth_users_perms_delete_user1,
            mock_get.auth_users_show_user2,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["users"]["user1"]["permissions"].pop()
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[32m* user1\x1b[0m\n    \x1b[33m-> permissions\x1b[0m\n      \x1b[91m- lava_scheduler_app.device.add_device\x1b[0m\n  \x1b[32m* user2\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


@pytest.fixture
def dt_hc(config_file):
    config_dir = config_file.parent / config_file.name.split(".")[0]
    hc_dir = config_dir / "health-checks"
    hc_dir.mkdir(parents=True, exist_ok=True)
    (hc_dir / "bbb.yaml").write_text("hc-definition", encoding="utf-8")
    (hc_dir / "docker.yaml").write_text("hc-definition", encoding="utf-8")
    (hc_dir / "qemu.yaml").write_text("hc-definition", encoding="utf-8")


def test_lab_apply_dt_no_change(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_post.scheduler_device_types_add_bbb,
            mock_get.scheduler_device_types_show_bbb,
            mock_get.scheduler_device_types_get_health_check_bbb,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["device_types"]["bbb"] = {}
    with open(config_file, "w") as f:
        yaml.dump(data, f)

    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m* bbb\x1b[0m\n  \x1b[32m* docker\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_hide(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "device-types",
            "--delete",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_post.scheduler_device_types_hide_qemu,
        ],
    )

    data = safe_yaml.load(config_def)
    del data["device_types"]["qemu"]
    # delete devices need the device type.
    del data["devices"]["qemu-01"]
    del data["devices"]["qemu-02"]
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "  \x1b[91m* qemu\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_dt_update(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_post.scheduler_device_types_update_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    data["device_types"]["docker"]["description"] = "new"
    data["device_types"]["docker"]["display"] = False
    data["device_types"]["docker"]["health_frequency"] = 12
    data["device_types"]["docker"]["health_denominator"] = "jobs"
    data["device_types"]["docker"]["health_disabled"] = True
    with open(config_file, "w") as f:
        yaml.dump(data, f)

    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n    \x1b[33m-> description: '' => 'new'\x1b[0m\n    \x1b[33m-> health_disabled: 'False' => 'True'\x1b[0m\n    \x1b[33m-> health_denominator: 'hours' => 'jobs'\x1b[0m\n    \x1b[33m-> health_frequency: '24' => '12'\x1b[0m\n    \x1b[33m-> display: 'True' => 'False'\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_set_hc_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker_empty,
            mock_post.scheduler_device_types_set_health_check_docker_add,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")

    assert main() == 0
    out, err = capsys.readouterr()
    diff = "  \x1b[32m* docker\x1b[0m\n    \x1b[33m-> health-check\x1b[0m\n    | @@ -0,0 +1 @@\n    | +hc-definition\n"
    assert diff in out
    assert err == ""


def test_lab_apply_dt_set_hc_del(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_post.scheduler_device_types_set_health_check_docker_del,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    config_dir = config_file.parent / config_file.name.split(".")[0]
    hc_path = config_dir / "health-checks" / "docker.yaml"
    hc_path.unlink()

    assert main() == 0
    out, err = capsys.readouterr()
    diff = "  \x1b[32m* docker\x1b[0m\n    \x1b[33m-> health-check\x1b[0m\n    | @@ -1 +0,0 @@\n    | -hc-definition\n"
    assert diff in out
    assert err == ""


def test_lab_apply_dt_set_hc_update(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_post.scheduler_device_types_set_health_check_docker_update,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    config_dir = config_file.parent / config_file.name.split(".")[0]
    hc_path = config_dir / "health-checks" / "docker.yaml"
    hc_path.write_text("new-hc-definition", encoding="utf-8")

    assert main() == 0
    out, err = capsys.readouterr()
    diff = "  \x1b[32m* docker\x1b[0m\n    \x1b[33m-> health-check\x1b[0m\n    | @@ -1 +1 @@\n    | -hc-definition\n    | +new-hc-definition\n"
    assert diff in out
    assert err == ""


def test_lab_apply_dt_set_template(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker_custom_template,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_get_template_docker,
            mock_post.scheduler_device_types_set_template_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    config_dir = config_file.parent / config_file.name.split(".")[0]
    hc_dir = config_dir / "device-types"
    hc_dir.mkdir(parents=True, exist_ok=True)
    (hc_dir / "docker.jinja2").write_text("new template definition", encoding="utf-8")

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n    \x1b[33m-> template\x1b[0m\n    | @@ -1 +1 @@\n    | -template content\n    | +new template definition\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_perms_add_groups_missing(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    data["device_types"]["docker"]["permissions"].append(
        {"name": "view_devicetype", "group": "group1"}
    )
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = """\x1b[36m> groups\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
\x1b[36m> users\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
\x1b[36m> device-types\x1b[0m
  \x1b[32m* docker\x1b[0m
    \x1b[33m->  SKIP permissions\x1b[0m
  \x1b[32m* qemu\x1b[0m
\x1b[36m> workers\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
\x1b[36m> devices\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
"""

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_perms_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "device-types",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_post.scheduler_device_types_perms_add_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    data["device_types"]["docker"]["permissions"].append(
        {"name": "view_devicetype", "group": "group1"}
    )
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = """\x1b[36m> groups\x1b[0m
  \x1b[32m* group1\x1b[0m
  \x1b[32m* group2\x1b[0m
\x1b[36m> users\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
\x1b[36m> device-types\x1b[0m
  \x1b[32m* docker\x1b[0m
    \x1b[33m->  permission               group\x1b[0m
      \x1b[32m+ view_devicetype          group1\x1b[0m
  \x1b[32m* qemu\x1b[0m
\x1b[36m> workers\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
\x1b[36m> devices\x1b[0m
  \x1b[33m-> SKIP\x1b[0m
"""

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_perms_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "device-types",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_post.scheduler_device_types_perms_delete_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    del data["device_types"]["docker"]["permissions"]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n    \x1b[33m->  permission               group\x1b[0m\n      \x1b[91m- change_devicetype        group1\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_perms_update(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "device-types",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_post.scheduler_device_types_perms_add_docker,
            mock_post.scheduler_device_types_perms_delete_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    data["device_types"]["docker"]["permissions"] = [
        {"name": "view_devicetype", "group": "group1"},
    ]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n    \x1b[33m->  permission               group\x1b[0m\n      \x1b[32m+ view_devicetype          group1\x1b[0m\n      \x1b[91m- change_devicetype        group1\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_dt_perms_unsupported(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post, dt_hc
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "device-types", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
            mock_get.scheduler_device_types_list,
            mock_get.scheduler_device_types_show_docker,
            mock_get.scheduler_device_types_get_health_check_docker,
            mock_get.scheduler_device_types_show_qemu,
            mock_get.scheduler_device_types_get_health_check_qemu,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["device_types"]["docker"] is None:
        data["device_types"]["docker"] = {}
    data["device_types"]["docker"]["permissions"] = [
        {"name": "view_devicetype", "group": "group1"},
    ]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[32m* docker\x1b[0m\n  \x1b[32m* qemu\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_no_change(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )


def test_lab_apply_workers_list_2023_2(
    setup, monkeypatch, capsys, config_file, config_def, mock_get
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
            mock_get.scheduler_workers_list_all_2023_2,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n  \x1b[32m* worker02\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_add(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_get.scheduler_workers_show_worker02,
            mock_post.scheduler_workers_add_worker03,
            mock_get.scheduler_workers_show_worker03,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["workers"]["worker03"] = {}
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n  \x1b[32m* worker02\x1b[0m\n  \x1b[33m* worker03\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_delete(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "workers",
            "--delete",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_05,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_post.scheduler_workers_delete_worker02,
        ],
    )

    data = safe_yaml.load(config_def)
    del data["workers"]["worker02"]
    # delete devices need the worker.
    del data["devices"]["docker-02"]
    del data["devices"]["qemu-02"]
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "  \x1b[91m* worker02\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_workers_update(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_post.scheduler_workers_update_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["workers"]["worker01"] is None:
        data["workers"]["worker01"] = {}
    data["workers"]["worker01"]["description"] = "new"
    data["workers"]["worker01"]["job_limit"] = 10
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n    \x1b[33m-> description: '' => 'new'\x1b[0m\n    \x1b[33m-> job_limit: '0' => '10'\x1b[0m\n  \x1b[32m* worker02\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_retire(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01,
            mock_post.scheduler_workers_retire_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    data = safe_yaml.load(config_def)
    if data["workers"]["worker01"] is None:
        data["workers"]["worker01"] = {}
    data["workers"]["worker01"]["retire"] = True
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "    \x1b[33m-> health: 'ACTIVE' => 'RETIRED'\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_workers_unretire(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, mock_post
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_retired_worker01,
            mock_post.scheduler_workers_unretire_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    data = safe_yaml.load(config_def)
    if data["workers"]["worker01"] is None:
        data["workers"]["worker01"] = {}
    data["workers"]["worker01"]["retire"] = False
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "    \x1b[33m-> health: 'RETIRED' => 'ACTIVE'\x1b[0m\n" in out
    assert err == ""


@pytest.fixture
def worker_config(config_file):
    config_dir = config_file.parent / config_file.name.split(".")[0]
    worker_dir = config_dir / "workers/worker01"
    worker_dir.mkdir(parents=True, exist_ok=True)
    return worker_dir


def test_lab_apply_workers_set_config(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    worker_config,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01_custom_config,
            mock_get.scheduler_workers_get_config_worker01,
            mock_post.scheduler_workers_set_config_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    (worker_config / "dispatcher.yaml").write_text(
        "local config content", encoding="utf-8"
    )
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n    \x1b[33m-> config\x1b[0m\n    | @@ -1 +1 @@\n    | -config content\n    | +local config content\n  \x1b[32m* worker02\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_env_update(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    worker_config,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01_custom_env,
            mock_get.scheduler_workers_get_env_worker01,
            mock_post.scheduler_workers_set_env_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    (worker_config / "env.yaml").write_text("local env content", encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n    \x1b[33m-> env\x1b[0m\n    | @@ -1 +1 @@\n    | -env content\n    | +local env content\n  \x1b[32m* worker02\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_workers_set_env_dut(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    worker_config,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "workers", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_workers_list_all,
            mock_get.scheduler_workers_show_worker01_custom_env_dut,
            mock_get.scheduler_workers_get_env_dut_worker01,
            mock_post.scheduler_workers_set_env_dut_worker01,
            mock_get.scheduler_workers_show_worker02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    (worker_config / "env-dut.yaml").write_text(
        "local env-dut content", encoding="utf-8"
    )
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[32m* worker01\x1b[0m\n    \x1b[33m-> env-dut\x1b[0m\n    | @@ -1 +1 @@\n    | -env-dut content\n    | +local env-dut content\n  \x1b[32m* worker02\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


@pytest.fixture
def device_dict(config_file):
    config_dir = config_file.parent / config_file.name.split(".")[0]
    device_dir = config_dir / "devices"
    device_dir.mkdir(parents=True, exist_ok=True)

    (device_dir / "docker-01.jinja2").write_text("yaml_dict", encoding="utf-8")
    (device_dir / "docker-02.jinja2").write_text("yaml_dict", encoding="utf-8")
    (device_dir / "qemu-01.jinja2").write_text("yaml_dict", encoding="utf-8")
    (device_dir / "qemu-02.jinja2").write_text("yaml_dict", encoding="utf-8")
    (device_dir / "qemu-03.jinja2").write_text("yaml_dict", encoding="utf-8")


def test_lab_apply_devices_no_change(
    setup, monkeypatch, capsys, config_file, config_def, mock_get, device_dict
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_add(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
            mock_post.scheduler_devices_add_qemu_03,
            mock_get.scheduler_devices_show_qemu_03,
            mock_get.scheduler_devices_get_dictionary_qemu_03,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["devices"]["qemu-03"] = {
        "device_type": "qemu",
        "worker": "worker01",
        "description": "qemu03",
    }
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n  \x1b[33m* qemu-03\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_delete(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "devices",
            "--delete",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_05,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_post.scheduler_devices_delete_qemu_02,
        ],
    )

    data = safe_yaml.load(config_def)
    del data["devices"]["qemu-02"]
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "  \x1b[91m* qemu-02\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_devices_update(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_post.scheduler_devices_update_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["devices"]["qemu-01"] = {
        "device_type": "qemu-aarch64",
        "worker": "worker02",
        "description": "qemu01",
    }
    data["device_types"]["qemu-aarch64"] = None
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n    \x1b[33m-> device_type: 'qemu' => 'qemu-aarch64'\x1b[0m\n    \x1b[33m-> worker: 'worker01' => 'worker02'\x1b[0m\n    \x1b[33m-> description: 'Created automatically by LAVA.' => 'qemu01'\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_retire(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_post.scheduler_devices_retire_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    data = safe_yaml.load(config_def)
    data["devices"]["qemu-01"]["retire"] = True
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "    \x1b[33m-> health: 'GOOD' => 'RETIRED'\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_devices_unretire(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_retired_qemu_01,
            mock_post.scheduler_devices_unretire_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    data = safe_yaml.load(config_def)
    data["devices"]["qemu-01"]["retire"] = False
    with open(config_file, "w") as f:
        safe_yaml.dump(data, f)

    assert main() == 0
    out, err = capsys.readouterr()
    assert "    \x1b[33m-> health: 'RETIRED' => 'UNKNOWN'\x1b[0m\n" in out
    assert err == ""


def test_lab_apply_devices_set_dictionary(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_post.scheduler_devices_set_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    config_file.write_text(config_def, encoding="utf-8")
    config_dir = config_file.parent / config_file.name.split(".")[0]
    (config_dir / "devices/docker-01.jinja2").write_text(
        "new_yaml_dict", encoding="utf-8"
    )
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m-> dictionary\x1b[0m\n    | @@ -1 +1 @@\n    | -yaml_dict\n    | +new_yaml_dict\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_tags_add(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_post.scheduler_devices_tags_add_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
            mock_get.scheduler_devices_show_qemu_03,
            mock_get.scheduler_devices_get_dictionary_qemu_03,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["devices"]["docker-01"]["tags"].append("worker01")
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m-> tags\x1b[0m\n      \x1b[32m+ worker01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_tags_delete(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_post.scheduler_devices_tags_delete_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
            mock_get.scheduler_devices_show_qemu_03,
            mock_get.scheduler_devices_get_dictionary_qemu_03,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    data["devices"]["docker-01"]["tags"].remove("docker-01")
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m-> tags\x1b[0m\n      \x1b[91m- docker-01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_perms_add(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "devices",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_post.scheduler_devices_perms_add_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["devices"]["docker-01"] is None:
        data["devices"]["docker-01"] = {}
    data["devices"]["docker-01"]["permissions"].append(
        {"name": "view_devicetype", "group": "group1"}
    )
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m->  permission               group\x1b[0m\n      \x1b[32m+ view_devicetype          group1\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_perms_delete(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "devices",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_post.scheduler_devices_perms_delete_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["devices"]["docker-01"] is None:
        data["devices"]["docker-01"] = {}
    del data["devices"]["docker-01"]["permissions"]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m->  permission               group\x1b[0m\n      \x1b[91m- change_devicetype        group1\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_perms_update(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "lab",
            "apply",
            "--resource",
            "devices",
            "--resources",
            "groups",
            str(config_file),
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_3,
            mock_get.auth_groups_list,
            mock_get.auth_groups_show_group1,
            mock_get.auth_groups_show_group2,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_post.scheduler_devices_perms_add_docker_01,
            mock_post.scheduler_devices_perms_delete_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["devices"]["docker-01"] is None:
        data["devices"]["docker-01"] = {}
    data["devices"]["docker-01"]["permissions"] = [
        {"name": "view_devicetype", "group": "group1"},
    ]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[32m* group1\x1b[0m\n  \x1b[32m* group2\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n    \x1b[33m->  permission               group\x1b[0m\n      \x1b[32m+ view_devicetype          group1\x1b[0m\n      \x1b[91m- change_devicetype        group1\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


def test_lab_apply_devices_perms_unsupported(
    setup,
    monkeypatch,
    capsys,
    config_file,
    config_def,
    mock_get,
    mock_post,
    device_dict,
):
    monkeypatch.setattr(
        sys,
        "argv",
        ["lavacli", "lab", "apply", "--resource", "devices", str(config_file)],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            mock_get.system_version_2023_2,
            mock_get.scheduler_devices_list,
            mock_get.scheduler_devices_show_docker_01,
            mock_get.scheduler_devices_get_dictionary_docker_01,
            mock_get.scheduler_devices_show_docker_02,
            mock_get.scheduler_devices_get_dictionary_docker_02,
            mock_get.scheduler_devices_show_qemu_01,
            mock_get.scheduler_devices_get_dictionary_qemu_01,
            mock_get.scheduler_devices_show_qemu_02,
            mock_get.scheduler_devices_get_dictionary_qemu_02,
        ],
    )

    yaml = ruamel.yaml.YAML(typ="safe")
    data = yaml.load(config_def)
    if data["devices"]["docker-01"] is None:
        data["devices"]["docker-01"] = {}
    data["devices"]["docker-01"]["permissions"] = [
        {"name": "view_devicetype", "group": "group1"},
    ]
    with open(config_file, "w") as f:
        yaml.dump(data, f)
    expected_out = "\x1b[36m> groups\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> users\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> device-types\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> workers\x1b[0m\n  \x1b[33m-> SKIP\x1b[0m\n\x1b[36m> devices\x1b[0m\n  \x1b[32m* docker-01\x1b[0m\n  \x1b[32m* docker-02\x1b[0m\n  \x1b[32m* qemu-01\x1b[0m\n  \x1b[32m* qemu-02\x1b[0m\n"

    assert main() == 0
    out, err = capsys.readouterr()
    assert out == expected_out
    assert err == ""


class TestConfigFile:
    def test_filepath_setter(self, tmp_path):
        with pytest.raises(ValueError) as exc:
            _config = ConfigFile("path_str")
        assert str(exc.value) == "filepath must be a pathlib.Path object!"

    def test_is_dir(self, tmp_path):
        config = ConfigFile(tmp_path / "lab")
        assert config.is_dir()

    def test_is_yaml_file(self, tmp_path):
        config = ConfigFile(tmp_path / "lab.yaml")
        assert config.is_yaml_file()

    def test_base_dir(self, tmp_path):
        """
        Test 'lab.yaml/../lab' is resolved to 'lab'. If not, 'lab.yaml'
        will be created as an parent dir of 'lab' which leads to file
        writing error.
        """
        config = ConfigFile(tmp_path / "lab.yaml")
        assert str(config.base_dir) == str(config.filepath.with_suffix(""))
