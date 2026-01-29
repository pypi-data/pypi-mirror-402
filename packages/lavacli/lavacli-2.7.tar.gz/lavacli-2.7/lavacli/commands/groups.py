# vim: set ts=4

# Copyright 2023-present Rémi Duraffort
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

import json
import sys

from lavacli.utils import safe_yaml


def configure_parser(parser, version):
    sub = parser.add_subparsers(dest="sub_sub_command", help="Sub commands")
    sub.required = True

    if version < (2023, 3):
        return

    # "add"
    groups_add = sub.add_parser("add", help="add a group")
    groups_add.add_argument("name", help="name")

    # "delete"
    groups_del = sub.add_parser("delete", help="delete a group")
    groups_del.add_argument("name", help="name")

    # "list"
    groups_list = sub.add_parser("list", help="list groups")
    out_format = groups_list.add_mutually_exclusive_group()
    out_format.add_argument(
        "--json",
        dest="output_format",
        default=None,
        action="store_const",
        const="json",
        help="print as json",
    )
    out_format.add_argument(
        "--yaml",
        dest="output_format",
        default=None,
        action="store_const",
        const="yaml",
        help="print as yaml",
    )

    # "perms"
    groups_perms = sub.add_parser("perms", help="manage user permissions")
    perms_sub = groups_perms.add_subparsers(
        dest="sub_sub_sub_command", help="Sub commands"
    )
    perms_sub.required = True
    perms_add = perms_sub.add_parser("add", help="add a permission")
    perms_add.add_argument("name", help="group name")
    perms_add.add_argument("app", help="application")
    perms_add.add_argument("model", help="model")
    perms_add.add_argument("codename", help="codename")

    perms_del = perms_sub.add_parser("delete", help="remove a permssion")
    perms_del.add_argument("name", help="group name")
    perms_del.add_argument("app", help="application")
    perms_del.add_argument("model", help="model")
    perms_del.add_argument("codename", help="codename")

    perms_list = perms_sub.add_parser("list", help="list permissions for a user")
    perms_list.add_argument("name", help="group name")
    out_format = perms_list.add_mutually_exclusive_group()
    out_format.add_argument(
        "--json",
        dest="output_format",
        default=None,
        action="store_const",
        const="json",
        help="print as json",
    )
    out_format.add_argument(
        "--yaml",
        dest="output_format",
        action="store_const",
        const="yaml",
        help="print as yaml",
    )

    # "show"
    groups_show = sub.add_parser("show", help="show group details")
    groups_show.add_argument("name", help="name")
    out_format = groups_show.add_mutually_exclusive_group()
    out_format.add_argument(
        "--json",
        dest="output_format",
        default=None,
        action="store_const",
        const="json",
        help="print as json",
    )
    out_format.add_argument(
        "--yaml",
        dest="output_format",
        action="store_const",
        const="yaml",
        default=None,
        help="print as yaml",
    )


def help_string():
    return "manage groups"


def handle_add(proxy, options, _):
    proxy.auth.groups.add(
        options.name,
    )
    return 0


def handle_delete(proxy, options, _):
    proxy.auth.groups.delete(options.name)
    return 0


def handle_list(proxy, options, _):
    groups = proxy.auth.groups.list()
    if options.output_format == "json":
        print(json.dumps(groups))
    elif options.output_format == "yaml":
        safe_yaml.dump(groups, sys.stdout)
    else:
        print("Groups:")
        for g in groups:
            print("* %s" % g)
    return 0


def handle_perms(proxy, options, _):
    if options.sub_sub_sub_command == "add":
        proxy.auth.groups.perms.add(
            options.name, options.app, options.model, options.codename
        )
    elif options.sub_sub_sub_command == "delete":
        proxy.auth.groups.perms.delete(
            options.name, options.app, options.model, options.codename
        )
    else:
        perms = proxy.auth.groups.perms.list(options.name)
        if options.output_format == "json":
            print(json.dumps(perms))
        elif options.output_format == "yaml":
            safe_yaml.dump(perms, sys.stdout)
        else:
            print("Permissions:")
            for perm in perms:
                print("* %s.%s.%s" % (perm["app"], perm["model"], perm["codename"]))
    return 0


def handle_show(proxy, options, config):
    group = proxy.auth.groups.show(options.name)

    if options.output_format == "json":
        print(json.dumps(group))
    elif options.output_format == "yaml":
        safe_yaml.dump(group, sys.stdout)
    else:
        print("name       : %s (%d)" % (group["name"], group["id"]))
        print("permissions: %s" % ", ".join(group["permissions"]))
        print("users      : %s" % ", ".join(group["users"]))


def handle(proxy, options, config):
    handlers = {
        "add": handle_add,
        "delete": handle_delete,
        "list": handle_list,
        "perms": handle_perms,
        "show": handle_show,
    }
    return handlers[options.sub_sub_command](proxy, options, config)
