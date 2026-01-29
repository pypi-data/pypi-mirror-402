# vim: set ts=4

# Copyright 2022-present Rémi Duraffort
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

import contextlib
import difflib
import sys
import xmlrpc
from dataclasses import MISSING, InitVar, asdict, dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Set

from voluptuous import MultipleInvalid

from lavacli import colors, schemas
from lavacli.utils import rt_yaml, safe_yaml


def print_file_diff(src, dst):
    if src is None:
        diffs = difflib.unified_diff([], dst.split("\n"), lineterm="")
    elif dst is None:
        diffs = difflib.unified_diff(src.split("\n"), [], lineterm="")
    else:
        diffs = difflib.unified_diff(src.split("\n"), dst.split("\n"), lineterm="")

    print("    | " + "\n    | ".join(list(diffs)[2:]))


class Base:
    @classmethod
    def new(cls, **kwargs):
        fields_names = [f.name for f in fields(cls)]
        i_kwargs = {}
        v_kwargs = {}
        for k in kwargs:
            if k in fields_names:
                v_kwargs[k] = kwargs[k]
            else:
                i_kwargs[k] = kwargs[k]

        return cls(**v_kwargs)

    def diff(self, data: Dict[str, Any]) -> List[str]:
        return [
            f.name for f in fields(self) if getattr(self, f.name) != data.get(f.name)
        ]


@dataclass(frozen=True, order=True)
class GroupDevicePermission:
    name: str
    group: str

    def dump(self):
        data = {k: v for k, v in asdict(self).items()}
        return data if data else None

    def __repr__(self):
        return f"{self.name:<25}{self.group}"


@dataclass
class Device(Base):
    hostname: str
    device_type: str
    worker: str
    description: str = None
    tags: Set[str] = field(default_factory=set)
    permissions: Set[GroupDevicePermission] = field(default_factory=set)
    health: str = None
    retire: InitVar[bool] = None

    def __post_init__(self, retire):
        self.tags = set(self.tags)
        self.permissions = set([GroupDevicePermission(**p) for p in self.permissions])
        self.retire = retire
        if self.retire is True:
            self.health = "RETIRED"

    def diff(self, data: Dict[str, Any]) -> List[str]:
        data = data.copy()
        data["tags"] = set(data["tags"])
        if data["description"] is None:
            data["description"] = ""
        if self.description is None:
            self.description = ""
        if self.health is None:
            # Do nothing if not defined.
            self.health = data["health"]
        if self.retire is False and data["health"] == "RETIRED":
            # set health to UNKNOWN to un-retire.
            self.health = "UNKNOWN"
        return super().diff(data)

    def dump(self, exclude):
        defaults = {f.name: f.default for f in fields(self) if f.default != MISSING}
        data = {}
        for k, v in asdict(self).items():
            if k in defaults and v == defaults[k]:
                continue
            data[k] = v

        if "description" in data and data["description"] in ["", None]:
            del data["description"]
        if not data["tags"]:
            del data["tags"]
        else:
            data["tags"] = sorted(data["tags"])
        del data["hostname"]
        if not data["permissions"] or "permissions" in exclude or "groups" in exclude:
            del data["permissions"]
        else:
            data["permissions"] = [p.dump() for p in sorted(data["permissions"])]
        # Add `retire: true` for retired device.
        if data["health"] == "Retired":
            data["retire"] = True
        del data["health"]
        return data if data else None

    def get_dict(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "devices" / f"{self.hostname}.jinja2").read_text(
                encoding="utf-8"
            )
        return None

    def set_dict(self, base, text):
        (base / "devices").mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(FileNotFoundError):
            return (base / "devices" / f"{self.hostname}.jinja2").write_text(
                text, encoding="utf-8"
            )


@dataclass
class DeviceType(Base):
    name: str
    description: str = ""
    health_disabled: bool = False
    health_denominator: str = "hours"
    health_frequency: int = 24
    aliases: Set[str] = field(default_factory=set)
    display: bool = True
    permissions: Set[GroupDevicePermission] = field(default_factory=set)

    def __post_init__(self):
        self.aliases = set(self.aliases)
        self.permissions = set([GroupDevicePermission(**p) for p in self.permissions])

    def diff(self, data: Dict[str, Any]) -> List[str]:
        data = data.copy()
        data["aliases"] = set(data["aliases"])
        if data["description"] is None:
            data["description"] = ""
        if self.description is None:
            self.description = ""
        return super().diff(data)

    def dump(self, exclude):
        defaults = {f.name: f.default for f in fields(self) if f.default != MISSING}
        data = {}
        for k, v in asdict(self).items():
            if k in defaults and v == defaults[k]:
                continue
            data[k] = v

        if not data["aliases"]:
            del data["aliases"]
        else:
            data["aliases"] = sorted(data["aliases"])
        if "description" in data and data["description"] in ["", None]:
            del data["description"]
        del data["name"]
        if not data["permissions"] or "permissions" in exclude or "groups" in exclude:
            del data["permissions"]
        else:
            data["permissions"] = [p.dump() for p in sorted(data["permissions"])]
        return data if data else None

    def get_health_check(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "health-checks" / f"{self.name}.yaml").read_text(
                encoding="utf-8"
            )
        return None

    def set_health_check(self, base, text):
        (base / "health-checks").mkdir(parents=True, exist_ok=True)
        (base / "health-checks" / f"{self.name}.yaml").write_text(
            text, encoding="utf-8"
        )

    def get_template(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "device-types" / f"{self.name}.jinja2").read_text(
                encoding="utf-8"
            )

    def set_template(self, base, text):
        (base / "device-types").mkdir(parents=True, exist_ok=True)
        (base / "device-types" / f"{self.name}.jinja2").write_text(
            text, encoding="utf-8"
        )


@dataclass(frozen=True, order=True)
class Permission:
    app: str
    model: str
    codename: str

    @classmethod
    def from_str(cls, s):
        app, model, codename = s.split(".")
        return cls(app=app, model=model, codename=codename)

    def dump(self):
        return str(self)

    def __repr__(self):
        return f"{self.app}.{self.model}.{self.codename}"


@dataclass
class Group(Base):
    name: str
    permissions: Set[Permission] = field(default_factory=set)

    def __post_init__(self):
        self.permissions = set([Permission.from_str(p) for p in self.permissions])

    def dump(self, exclude):
        defaults = {f.name: f.default for f in fields(self) if f.default != MISSING}
        data = {}
        for k, v in asdict(self).items():
            if k in defaults and v == defaults[k]:
                continue
            data[k] = v

        if not data["permissions"] or "permissions" in exclude:
            del data["permissions"]
        else:
            data["permissions"] = [p.dump() for p in sorted(data["permissions"])]
        del data["name"]
        return data if data else None


@dataclass
class User(Base):
    username: str
    last_name: str = ""
    first_name: str = ""
    email: str = ""
    is_superuser: bool = False
    is_staff: bool = False
    is_active: bool = True
    ldap: bool = False
    groups: Set[str] = field(default_factory=set)
    permissions: Set[Permission] = field(default_factory=set)

    def __post_init__(self):
        self.groups = set(self.groups)
        self.permissions = set([Permission.from_str(p) for p in self.permissions])

    def diff(self, data: Dict[str, Any]) -> List[str]:
        data = data.copy()
        data["groups"] = set(data["groups"])
        diff = super().diff(data)
        # ldap is user add only.
        if "ldap" in diff:
            diff.remove("ldap")
        # Don't update first_name, last_name and email for ldap user.
        if self.ldap:
            diff = [d for d in diff if d not in ["first_name", "last_name", "email"]]

        return diff

    def dump(self, exclude):
        defaults = {f.name: f.default for f in fields(self) if f.default != MISSING}
        data = {}
        for k, v in asdict(self).items():
            if k in defaults and v == defaults[k]:
                continue
            data[k] = v

        if not data["groups"] or "groups" in exclude:
            del data["groups"]
        else:
            data["groups"] = sorted(data["groups"])
        if not data["permissions"] or "permissions" in exclude:
            del data["permissions"]
        else:
            data["permissions"] = [p.dump() for p in sorted(data["permissions"])]
        del data["username"]
        return data if data else None


@dataclass
class Worker(Base):
    hostname: str
    description: str = ""
    job_limit: int = 0
    health: str = None
    retire: InitVar[bool] = False

    def __post_init__(self, retire):
        self.retire = retire
        if self.retire is True:
            self.health = "RETIRED"

    def diff(self, data: Dict[str, Any]) -> List[str]:
        data = data.copy()
        if data["description"] is None:
            data["description"] = ""
        if self.description is None:
            self.description = ""
        if self.health is None:
            # Do nothing if not defined.
            self.health = data["health"]
        if self.retire is False and data["health"] == "RETIRED":
            # Set health to ACTIVE to un-retire.
            self.health = "ACTIVE"
        return super().diff(data)

    def dump(self):
        defaults = {f.name: f.default for f in fields(self) if f.default != MISSING}
        data = {}
        for k, v in asdict(self).items():
            if k in defaults and v == defaults[k]:
                continue
            data[k] = v

        if "description" in data and data["description"] in ["", None]:
            del data["description"]
        del data["hostname"]
        # Add `retire: true` for retired worker.
        if data["health"] == "Retired":
            data["retire"] = True
        del data["health"]
        return data if data else None

    def get_config(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "workers" / self.hostname / "dispatcher.yaml").read_text(
                encoding="utf-8"
            )

    def set_config(self, base, text):
        (base / "workers" / self.hostname).mkdir(parents=True, exist_ok=True)
        (base / "workers" / self.hostname / "dispatcher.yaml").write_text(
            text, encoding="utf-8"
        )

    def get_env(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "workers" / self.hostname / "env.yaml").read_text(
                encoding="utf-8"
            )

    def set_env(self, base, text):
        (base / "workers" / self.hostname).mkdir(parents=True, exist_ok=True)
        (base / "workers" / self.hostname / "env.yaml").write_text(
            text, encoding="utf-8"
        )

    def get_env_dut(self, base):
        with contextlib.suppress(FileNotFoundError):
            return (base / "workers" / self.hostname / "env-dut.yaml").read_text(
                encoding="utf-8"
            )

    def set_env_dut(self, base, text):
        (base / "workers" / self.hostname).mkdir(parents=True, exist_ok=True)
        (base / "workers" / self.hostname / "env-dut.yaml").write_text(
            text, encoding="utf-8"
        )


@dataclass
class Config:
    device_types: Dict[str, DeviceType]
    devices: Dict[str, Device]
    workers: Dict[str, Worker]
    groups: Dict[str, Group] = field(default_factory=dict)
    users: Dict[str, User] = field(default_factory=dict)

    def __post_init__(self):
        self.devices = {n: Device(hostname=n, **d) for n, d in self.devices.items()}
        self.device_types = {
            n: DeviceType(name=n, **(dt if dt is not None else {}))
            for n, dt in self.device_types.items()
        }
        self.groups = {
            n: Group(name=n, **(grp if grp is not None else {}))
            for n, grp in self.groups.items()
        }
        self.users = {
            n: User(username=n, **(user if user is not None else {}))
            for n, user in self.users.items()
        }
        self.workers = {
            h: Worker(hostname=h, **(w if w is not None else {}))
            for h, w in self.workers.items()
        }

    def _groups(self, exclude):
        return {k: self.groups[k].dump(exclude) for k in self.groups}

    def _users(self, exclude):
        return {k: self.users[k].dump(exclude) for k in self.users}

    def _device_types(self, exclude):
        return {k: self.device_types[k].dump(exclude) for k in self.device_types}

    def _workers(self):
        return {k: self.workers[k].dump() for k in self.workers}

    def _devices(self, exclude):
        return {k: self.devices[k].dump(exclude) for k in self.devices}

    def dump(self, resources, exclude):
        data = {}
        if "device-types" in resources:
            data["device_types"] = self._device_types(exclude)
        if "devices" in resources:
            data["devices"] = self._devices(exclude)
        if "workers" in resources:
            data["workers"] = self._workers()
        if "groups" in resources and "groups" not in exclude:
            data["groups"] = self._groups(exclude)
        if "users" in resources and "users" not in exclude:
            data["users"] = self._users(exclude)

        return data

    def dump_device_types(self, exclude):
        return {"device_types": self._device_types(exclude)}

    def dump_devices(self, exclude):
        return {"devices": self._devices(exclude)}

    def dump_groups(self, exclude):
        return {"groups": self._groups(exclude)}

    def dump_users(self, exclude):
        return {"users": self._users(exclude)}

    def dump_workers(self):
        return {"workers": self._workers()}


class ConfigFile:
    def __init__(self, filepath):
        self.filepath = filepath

    @property
    def filepath(self):
        return self._filepath

    @filepath.setter
    def filepath(self, value):
        if not isinstance(value, Path):
            raise ValueError("filepath must be a pathlib.Path object!")
        self._filepath = value.resolve()

    def is_yaml_file(self):
        with contextlib.suppress(AttributeError):
            if self.filepath.suffix == ".yaml":
                return True
        return False

    def is_dir(self):
        """Treat non yaml file as a directory"""
        if self.is_yaml_file():
            return False
        return True

    @property
    def base_dir(self):
        base_dir = self.filepath
        if self.is_yaml_file():
            base_dir = (self.filepath / ".." / self.filepath.stem).resolve()
        return base_dir

    def write(self, filename, data):
        print(f"{colors.yellow}> {filename}{colors.reset}")
        with filename.open("w") as f:
            rt_yaml.dump(data, f)

    def load(self):
        if self.is_yaml_file():
            return safe_yaml.load(self.filepath.read_text(encoding="utf-8"))
        if self.is_dir():
            data = {}
            files = [*sorted(self.filepath.glob("*.yaml"))]
            for _file in files:
                _config = safe_yaml.load(_file.read_text(encoding="utf-8"))
                data.update(_config)
            return data
        return {}

    def dump(self, lab, resources=[], exclude=[]):
        if self.is_yaml_file():
            self.write(self.filepath, lab.dump(resources, exclude))
        if self.is_dir():
            if "groups" in resources and "groups" not in exclude:
                self.write((self.base_dir / "groups.yaml"), lab.dump_groups(exclude))
            if "users" in resources and "users" not in exclude:
                self.write((self.base_dir / "users.yaml"), lab.dump_users(exclude))
            if "device-types" in resources:
                self.write(
                    (self.base_dir / "device-types.yaml"),
                    lab.dump_device_types(exclude),
                )
            if "devices" in resources:
                self.write((self.base_dir / "devices.yaml"), lab.dump_devices(exclude))
            if "workers" in resources:
                self.write((self.base_dir / "workers.yaml"), lab.dump_workers())


def configure_parser(parser, version):
    sub = parser.add_subparsers(dest="sub_sub_command", help="Sub commands")
    sub.required = True

    if version < (2022, 4):
        return

    # "apply"
    lab_apply = sub.add_parser("apply", help="apply configuration")
    lab_apply.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Do not update the configuration",
    )
    lab_apply.add_argument(
        "--resources",
        default=[],
        action="append",
        choices=["groups", "users", "devices", "device-types", "workers"],
        help="resources to sync",
    )
    lab_apply.add_argument(
        "--delete",
        action="store_true",
        default=False,
        help="Delete resource that not found in config file",
    )
    lab_apply.add_argument(
        "config",
        type=Path,
        help="Path to a single config file using '.yaml' extension or a directory containing a set of config files",
    )

    # "import"
    lab_import = sub.add_parser("import", help="import configuration")
    lab_import.add_argument(
        "--resources",
        default=[],
        action="append",
        choices=["groups", "users", "devices", "device-types", "workers"],
        help="resources to import",
    )
    lab_import.add_argument(
        "--exclude",
        default=[],
        action="append",
        choices=["groups", "users", "permissions"],
        help="resource to exclude",
    )
    lab_import.add_argument(
        "config",
        type=Path,
        help="Path to a single config file using '.yaml' extension or a directory containing a set of config files",
    )

    # validate
    lab_validate = sub.add_parser("validate", help="validate configuration")
    lab_validate.add_argument("config", type=Path, help="configuration file")


def help_string():
    return "manage lab configuration"


def validate(data: dict) -> bool:
    try:
        schemas.config_schema(data)
        return True
    except MultipleInvalid as exc:
        print(str(exc))
        print(f"{colors.red}Config invalid!{colors.reset}")
        return False


def handle_apply(proxy, options, config):
    if not options.resources:
        options.resources = ["devices", "device-types", "groups", "users", "workers"]

    config_file = ConfigFile(options.config)
    data = config_file.load()
    if not validate(data):
        return 1
    lab = Config(**data)
    base = config_file.base_dir

    print(f"{colors.cyan}> groups{colors.reset}")
    if "groups" not in options.resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    elif config["version"] >= (2023, 3):
        groups = proxy.auth.groups.list()
        for group in lab.groups.values():
            if group.name in groups:
                print(f"  {colors.green}* {group.name}{colors.reset}")
            else:
                print(f"  {colors.yellow}* {group.name}{colors.reset}")
                if not options.dry_run:
                    proxy.auth.groups.add(group.name)

            data = proxy.auth.groups.show(group.name)
            data["permissions"] = set(
                [Permission.from_str(p) for p in data["permissions"]]
            )
            diff = group.diff(data)
            if "permissions" in diff:
                print(f"    {colors.yellow}-> permissions{colors.reset}")
                missing = group.permissions.difference(set(data["permissions"]))
                for perm in missing:
                    print(f"      {colors.green}+ {perm}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.groups.perms.add(
                            group.name, perm.app, perm.model, perm.codename
                        )
                missing = set(data["permissions"]).difference(group.permissions)
                for perm in missing:
                    print(f"      {colors.red}- {perm}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.groups.perms.delete(
                            group.name, perm.app, perm.model, perm.codename
                        )

        if options.delete:
            for group in groups:
                if group not in lab.groups:
                    print(f"  {colors.red}* {group}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.groups.delete(group)

    print(f"{colors.cyan}> users{colors.reset}")
    if "users" not in options.resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    elif config["version"] >= (2023, 3):
        users = [user["username"] for user in proxy.auth.users.list()]
        for user in lab.users.values():
            if user.username in users:
                print(f"  {colors.green}* {user.username}{colors.reset}")
            else:
                print(f"  {colors.yellow}* {user.username}{colors.reset}")
                if not options.dry_run:
                    proxy.auth.users.add(
                        user.username,
                        user.first_name or None,
                        user.last_name or None,
                        user.email or None,
                        user.is_active,
                        user.is_staff,
                        user.is_superuser,
                        user.ldap,
                    )

            data = proxy.auth.users.show(user.username)
            data["permissions"] = set(
                [Permission.from_str(p) for p in data["permissions"]]
            )
            diff = user.diff(data)
            update_diff = [n for n in diff if n not in ["groups", "permissions"]]
            if update_diff:
                for name in update_diff:
                    print(
                        f"    {colors.yellow}-> {name}: '{data[name]}' => '{getattr(user, name)}'{colors.reset}"
                    )
                if not options.dry_run:
                    proxy.auth.users.update(
                        user.username,
                        user.first_name if "first_name" in diff else None,
                        user.last_name if "last_name" in diff else None,
                        user.email if "email" in diff else None,
                        user.is_active if "is_active" in diff else None,
                        user.is_staff if "is_staff" in diff else None,
                        user.is_superuser if "is_superuser" in diff else None,
                    )
            if "groups" in diff:
                print(f"    {colors.yellow}-> groups{colors.reset}")
                missing = user.groups.difference(set(data["groups"]))
                for grp in missing:
                    print(f"      {colors.green}+ {grp}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.users.groups.add(user.username, grp)
                missing = set(data["groups"]).difference(user.groups)
                for grp in missing:
                    print(f"      {colors.red}- {grp}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.users.groups.delete(user.username, grp)

            if "permissions" in diff:
                print(f"    {colors.yellow}-> permissions{colors.reset}")
                missing = user.permissions.difference(set(data["permissions"]))
                for perm in missing:
                    print(f"      {colors.green}+ {perm}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.users.perms.add(
                            user.username, perm.app, perm.model, perm.codename
                        )
                missing = set(data["permissions"]).difference(user.permissions)
                for perm in missing:
                    print(f"      {colors.red}- {perm}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.users.perms.delete(
                            user.username, perm.app, perm.model, perm.codename
                        )

        if options.delete:
            for user in users:
                if user not in lab.users:
                    print(f"  {colors.red}* {user}{colors.reset}")
                    if not options.dry_run:
                        proxy.auth.users.delete(user)

    print(f"{colors.cyan}> device-types{colors.reset}")
    if "device-types" not in options.resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        device_types = [dt["name"] for dt in proxy.scheduler.device_types.list(False)]
        for dt in lab.device_types.values():
            if dt.name in device_types:
                print(f"  {colors.green}* {dt.name}{colors.reset}")
            else:
                print(f"  {colors.yellow}* {dt.name}{colors.reset}")
                if not options.dry_run:
                    proxy.scheduler.device_types.add(
                        dt.name,
                        dt.description or None,
                        dt.display or True,
                        # owners_only is deprecated.
                        None,
                        dt.health_frequency or 24,
                        dt.health_denominator or "hours",
                    )
            data = proxy.scheduler.device_types.show(dt.name)
            if config["version"] >= (2023, 3):
                data["permissions"] = set(
                    [GroupDevicePermission(**p) for p in data.get("permissions", [])]
                )
            diff = dt.diff(data)
            dt_diff = [n for n in diff if n not in ["aliases", "permissions"]]
            if dt_diff:
                for name in dt_diff:
                    print(
                        f"    {colors.yellow}-> {name}: '{data[name]}' => '{getattr(dt, name)}'{colors.reset}"
                    )
                if not options.dry_run:
                    proxy.scheduler.device_types.update(
                        dt.name,
                        dt.description if "description" in diff else None,
                        dt.display if "display" in diff else None,
                        None,
                        dt.health_frequency if "health_frequency" in diff else None,
                        dt.health_denominator if "health_denominator" in diff else None,
                        dt.health_disabled if "health_disabled" in diff else None,
                    )
            if "aliases" in diff:
                print(f"    {colors.yellow}-> aliases{colors.reset}")
                missing = dt.aliases.difference(set(data["aliases"]))
                for alias in missing:
                    print(f"      {colors.green}+ {alias}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.device_types.aliases.add(dt.name, alias)
                missing = set(data["aliases"]).difference(dt.aliases)
                for alias in missing:
                    print(f"      {colors.red}- {alias}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.device_types.aliases.delete(dt.name, alias)

            if config["version"] >= (2023, 3) and "permissions" in diff:
                if "groups" not in options.resources:
                    print(f"    {colors.yellow}->  SKIP permissions{colors.reset}")
                else:
                    print(
                        f"    {colors.yellow}->  {'permission':<25}group{colors.reset}"
                    )
                    missing = sorted(
                        dt.permissions.difference(set(data["permissions"]))
                    )
                    for perm in missing:
                        print(f"      {colors.green}+ {perm}{colors.reset}")
                        if not options.dry_run:
                            proxy.scheduler.device_types.perms_add(
                                dt.name, perm.group, perm.name
                            )
                    missing = sorted(
                        set(data["permissions"]).difference(dt.permissions)
                    )
                    for perm in missing:
                        print(f"      {colors.red}- {perm}{colors.reset}")
                        if not options.dry_run:
                            proxy.scheduler.device_types.perms_delete(
                                dt.name, perm.group, perm.name
                            )

            try:
                hc = str(proxy.scheduler.device_types.get_health_check(dt.name))
            except xmlrpc.client.Fault as exc:
                if exc.faultCode != 404:
                    raise
                hc = None
            if dt.get_health_check(base) != hc:
                print(f"    {colors.yellow}-> health-check{colors.reset}")
                print_file_diff(hc, dt.get_health_check(base))
                if not options.dry_run:
                    proxy.scheduler.device_types.set_health_check(
                        dt.name, dt.get_health_check(base)
                    )

            if not data["default_template"] or dt.get_template(base) is not None:
                try:
                    template = str(proxy.scheduler.device_types.get_template(dt.name))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    template = None
                if dt.get_template(base) != template:
                    print(f"    {colors.yellow}-> template{colors.reset}")
                    print_file_diff(template, dt.get_template(base))
                    if not options.dry_run:
                        proxy.scheduler.device_types.set_template(
                            dt.name, dt.get_template(base)
                        )

        if options.delete:
            for dt in device_types:
                if dt not in lab.device_types:
                    print(f"  {colors.red}* {dt}{colors.reset}")
                    if not options.dry_run:
                        # Hide the device type in the GUI.
                        proxy.scheduler.device_types.update(
                            dt,
                            None,
                            False,
                            None,
                            None,
                            None,
                            None,
                        )

    print(f"{colors.cyan}> workers{colors.reset}")
    if "workers" not in options.resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        if config["version"] >= (2023, 3):
            workers = proxy.scheduler.workers.list(True)
        else:
            workers = proxy.scheduler.workers.list()
        for worker in lab.workers.values():
            if worker.hostname in workers:
                print(f"  {colors.green}* {worker.hostname}{colors.reset}")
            else:
                print(f"  {colors.yellow}* {worker.hostname}{colors.reset}")
                if not options.dry_run:
                    proxy.scheduler.workers.add(
                        worker.hostname, worker.description, False
                    )
            data = proxy.scheduler.workers.show(worker.hostname)
            # Active/Maintenance/Retired -> ACTIVE/MAINTENANCE/RETRIED for comparison.
            data["health"] = data["health"].upper()
            diff = worker.diff(data)
            for name in diff:
                print(
                    f"    {colors.yellow}-> {name}: '{data[name]}' => '{getattr(worker, name)}'{colors.reset}"
                )
            if diff and not options.dry_run:
                proxy.scheduler.workers.update(
                    worker.hostname,
                    worker.description if "description" in diff else None,
                    worker.health if "health" in diff else None,
                    worker.job_limit if "job_limit" in diff else None,
                )

            if not data["default_config"] or worker.get_config(base) is not None:
                try:
                    wconfig = str(proxy.scheduler.workers.get_config(worker.hostname))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wconfig = None
                if worker.get_config(base) != wconfig:
                    print(f"    {colors.yellow}-> config{colors.reset}")
                    print_file_diff(wconfig, worker.get_config(base))
                    if not options.dry_run:
                        proxy.scheduler.workers.set_config(
                            worker.hostname, worker.get_config(base)
                        )

            if not data["default_env"] or worker.get_env(base) is not None:
                try:
                    wenv = str(proxy.scheduler.workers.get_env(worker.hostname))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wenv = None
                if worker.get_env(base) != wenv:
                    print(f"    {colors.yellow}-> env{colors.reset}")
                    print_file_diff(wenv, worker.get_env(base))
                    if not options.dry_run:
                        proxy.scheduler.workers.set_env(
                            worker.hostname, worker.get_env(base)
                        )

            if not data["default_env_dut"] or worker.get_env_dut(base) is not None:
                try:
                    wenv_dut = str(proxy.scheduler.workers.get_env_dut(worker.hostname))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wenv_dut = None
                if worker.get_env_dut(base) != wenv_dut:
                    print(f"    {colors.yellow}-> env-dut{colors.reset}")
                    print_file_diff(wenv_dut, worker.get_env_dut(base))
                    if not options.dry_run:
                        proxy.scheduler.workers.set_env_dut(
                            worker.hostname, worker.get_env_dut(base)
                        )

        if options.delete and config["version"] >= (2023, 5):
            for worker in workers:
                if worker not in lab.workers:
                    print(f"  {colors.red}* {worker}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.workers.delete(worker)

    print(f"{colors.cyan}> devices{colors.reset}")
    if "devices" not in options.resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        devices = [d["hostname"] for d in proxy.scheduler.devices.list(True)]
        for device in lab.devices.values():
            if device.hostname in devices:
                print(f"  {colors.green}* {device.hostname}{colors.reset}")
            else:
                print(f"  {colors.yellow}* {device.hostname}{colors.reset}")
                if not options.dry_run:
                    proxy.scheduler.devices.add(
                        device.hostname,
                        device.device_type,
                        device.worker,
                        None,
                        None,
                        None,
                        None,
                        device.description,
                    )
            data = proxy.scheduler.devices.show(device.hostname)
            # Good/Unknow/Looping/Bad/Maintenance/Retired ->
            # GOOD/UNKNOWN/LOOPING/BAD/MAINTENANCE/RETIRED for comparison
            data["health"] = data["health"].upper()
            if config["version"] >= (2023, 3):
                data["permissions"] = set(
                    [GroupDevicePermission(**p) for p in data.get("permissions", [])]
                )
            diff = device.diff(data)
            device_diff = [n for n in diff if n not in ["tags", "permissions"]]
            if device_diff:
                for name in device_diff:
                    print(
                        f"    {colors.yellow}-> {name}: '{data[name]}' => '{getattr(device, name)}'{colors.reset}"
                    )
                if not options.dry_run:
                    proxy.scheduler.devices.update(
                        device.hostname,
                        device.worker if "worker" in diff else None,
                        None,
                        None,
                        None,
                        device.health if "health" in diff else None,
                        device.description if "description" in diff else None,
                        device.device_type if "device_type" in diff else None,
                    )
            if "tags" in diff:
                print(f"    {colors.yellow}-> tags{colors.reset}")
                missing = device.tags.difference(set(data["tags"]))
                for tag in missing:
                    print(f"      {colors.green}+ {tag}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.devices.tags.add(device.hostname, tag)
                missing = set(data["tags"]).difference(device.tags)
                for tag in missing:
                    print(f"      {colors.red}- {tag}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.devices.tags.delete(device.hostname, tag)

            if config["version"] >= (2023, 3) and "permissions" in diff:
                if "groups" not in options.resources:
                    print(f"    {colors.yellow}->  SKIP permissions{colors.reset}")
                else:
                    print(
                        f"    {colors.yellow}->  {'permission':<25}group{colors.reset}"
                    )
                    missing = sorted(
                        device.permissions.difference(set(data["permissions"]))
                    )
                    for perm in missing:
                        print(f"      {colors.green}+ {perm}{colors.reset}")
                        if not options.dry_run:
                            proxy.scheduler.devices.perms_add(
                                device.hostname, perm.group, perm.name
                            )
                    missing = sorted(
                        set(data["permissions"]).difference(device.permissions)
                    )
                    for perm in missing:
                        print(f"      {colors.red}- {perm}{colors.reset}")
                        if not options.dry_run:
                            proxy.scheduler.devices.perms_delete(
                                device.hostname, perm.group, perm.name
                            )

            try:
                ddict = str(proxy.scheduler.devices.get_dictionary(device.hostname))
            except xmlrpc.client.Fault as exc:
                if exc.faultCode != 404:
                    raise
                ddict = None

            if device.get_dict(base) != ddict:
                print(f"    {colors.yellow}-> dictionary{colors.reset}")
                print_file_diff(ddict, device.get_dict(base))
                if not options.dry_run:
                    proxy.scheduler.devices.set_dictionary(
                        device.hostname, device.get_dict(base)
                    )

        if options.delete and config["version"] >= (2023, 5):
            for device in devices:
                if device not in lab.devices:
                    print(f"  {colors.red}* {device}{colors.reset}")
                    if not options.dry_run:
                        proxy.scheduler.devices.delete(device)

    return 0


def handle_import(proxy, options, config):
    lab = Config({}, {}, {}, {}, {})

    config_file = ConfigFile(options.config)
    base = config_file.base_dir
    base.mkdir(parents=True, exist_ok=True)

    resources = options.resources
    if resources:
        if "devices" in resources:
            if (
                "device-types" not in resources
                or "workers" not in resources
                or "groups" not in resources
            ):
                sys.stderr.write(
                    "'--resources devices' needs '--resources device-types --resources workers --resources groups'\n"
                )
                return 1
        if "device-types" in resources:
            if "groups" not in resources:
                sys.stderr.write(
                    "'--resources device-types' needs '--resources groups'\n"
                )
                return 1
        if "users" in resources:
            if "groups" not in resources:
                sys.stderr.write("'--resources users' needs '--resources groups'\n")
                return 1
    else:
        resources = ["devices", "device-types", "groups", "users", "workers"]

    excluded_resources = options.exclude

    if config["version"] >= (2023, 3):
        print(f"{colors.cyan}> groups{colors.reset}")
        if "groups" not in resources:
            print(f"  {colors.yellow}-> SKIP{colors.reset}")
        else:
            if "groups" in excluded_resources:
                print(f"  {colors.yellow}-> SKIP{colors.reset}")
            else:
                groups = [grp for grp in proxy.auth.groups.list()]
                for grp in groups:
                    print(f"  {colors.green}* {grp}{colors.reset}")
                    data = proxy.auth.groups.show(grp)
                    lab.groups[grp] = Group.new(
                        name=data["name"], permissions=data["permissions"]
                    )

        print(f"{colors.cyan}> users{colors.reset}")
        if "users" not in resources:
            print(f"  {colors.yellow}-> SKIP{colors.reset}")
        else:
            if "users" in excluded_resources:
                print(f"  {colors.yellow}-> SKIP{colors.reset}")
            else:
                users = [user["username"] for user in proxy.auth.users.list()]
                for user in users:
                    print(f"  {colors.green}* {user}{colors.reset}")
                    data = proxy.auth.users.show(user)
                    lab.users[user] = User.new(**data)

    print(f"{colors.cyan}> device-types{colors.reset}")
    if "device-types" not in resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        device_types = [dt["name"] for dt in proxy.scheduler.device_types.list(False)]
        for dt in device_types:
            print(f"  {colors.green}* {dt}{colors.reset}")
            data = proxy.scheduler.device_types.show(dt)
            lab.device_types[dt] = DeviceType.new(**data)

            try:
                hc = str(proxy.scheduler.device_types.get_health_check(dt))
            except xmlrpc.client.Fault as exc:
                if exc.faultCode != 404:
                    raise
                hc = None
            if hc is not None:
                print(f"  {colors.green}  -> health-check{colors.reset}")
                lab.device_types[dt].set_health_check(base, hc)

            if data["default_template"]:
                print(f"  {colors.green}  -> default template{colors.reset}")
            else:
                try:
                    template = str(proxy.scheduler.device_types.get_template(dt))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    template = None
                if template is not None:
                    print(f"  {colors.green}  -> template{colors.reset}")
                    lab.device_types[dt].set_template(base, template)

    print(f"{colors.cyan}> workers{colors.reset}")
    if "workers" not in resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        if config["version"] >= (2023, 3):
            workers = proxy.scheduler.workers.list(True)
        else:
            workers = proxy.scheduler.workers.list()
        for worker in workers:
            print(f"  {colors.green}* {worker}{colors.reset}")
            data = proxy.scheduler.workers.show(worker)
            lab.workers[worker] = Worker.new(**data)

            if data["default_config"]:
                print(f"  {colors.green}  -> default config{colors.reset}")
            else:
                try:
                    wconfig = str(proxy.scheduler.workers.get_config(worker))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wconfig = None
                if wconfig is not None:
                    print(f"  {colors.green}  -> config{colors.reset}")
                    lab.workers[worker].set_config(base, wconfig)

            if data["default_env"]:
                print(f"  {colors.green}  -> default env{colors.reset}")
            else:
                try:
                    wenv = str(proxy.scheduler.workers.get_env(worker))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wenv = None
                if wenv is not None:
                    print(f"  {colors.green}  -> env{colors.reset}")
                    lab.workers[worker].set_env(base, wenv)

            if data["default_env_dut"]:
                print(f"  {colors.green}  -> default env-dut{colors.reset}")
            else:
                try:
                    wenv_dut = str(proxy.scheduler.workers.get_env_dut(worker))
                except xmlrpc.client.Fault as exc:
                    if exc.faultCode != 404:
                        raise
                    wenv_dut = None
                if wenv_dut is not None:
                    print(f"  {colors.green}  -> env-dut{colors.reset}")
                    lab.workers[worker].set_env_dut(base, wenv_dut)

    print(f"{colors.cyan}> devices{colors.reset}")
    if "devices" not in resources:
        print(f"  {colors.yellow}-> SKIP{colors.reset}")
    else:
        devices = [d["hostname"] for d in proxy.scheduler.devices.list(True)]
        for device in devices:
            print(f"  {colors.green}* {device}{colors.reset}")
            data = proxy.scheduler.devices.show(device)
            lab.devices[device] = Device.new(**data)
            try:
                ddict = str(proxy.scheduler.devices.get_dictionary(device))
            except xmlrpc.client.Fault as exc:
                if exc.faultCode != 404:
                    raise
                ddict = None
            if ddict is not None:
                print(f"  {colors.green}  -> dictionary{colors.reset}")
                lab.devices[device].set_dict(base, ddict)

    config_file.dump(lab, resources, excluded_resources)

    return 0


def handle_validate(proxy, options, config):
    config_file = ConfigFile(options.config)
    data = config_file.load()
    if validate(data):
        print(f"{colors.green}Config valid.{colors.reset}")
        return 0
    return 1


def handle(proxy, options, config):
    handlers = {
        "apply": handle_apply,
        "import": handle_import,
        "validate": handle_validate,
    }
    return handlers[options.sub_sub_command](proxy, options, config)
