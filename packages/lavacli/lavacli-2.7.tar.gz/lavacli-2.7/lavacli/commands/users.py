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
    users_add = sub.add_parser("add", help="add a user")
    users_add.add_argument("username", help="username")
    users_add.add_argument("--email", default=None, help="email")
    users_add.add_argument("--first-name", default=None, help="first name")
    users_add.add_argument("--last-name", default=None, help="last name")
    users_add.add_argument(
        "--no-active",
        action="store_false",
        dest="is_active",
        default=True,
        help="no active user",
    )
    users_add.add_argument(
        "--staff",
        action="store_true",
        dest="is_staff",
        default=False,
        help="staff user",
    )
    users_add.add_argument(
        "--superuser",
        action="store_true",
        dest="is_superuser",
        default=False,
        help="superuser",
    )
    users_add.add_argument(
        "--ldap",
        action="store_true",
        dest="ldap",
        help="ldap user",
    )

    # "delete"
    users_del = sub.add_parser("delete", help="delete a user")
    users_del.add_argument("username", help="username")

    # "groups"
    users_groups = sub.add_parser("groups", help="manage user groups")
    groups_sub = users_groups.add_subparsers(
        dest="sub_sub_sub_command", help="Sub commands"
    )
    groups_sub.required = True
    groups_add = groups_sub.add_parser("add", help="add a group")
    groups_add.add_argument("username", help="username")
    groups_add.add_argument("group", help="name of the group")

    groups_del = groups_sub.add_parser("delete", help="remove a group")
    groups_del.add_argument("username", help="username")
    groups_del.add_argument("group", help="name of the group")

    groups_list = groups_sub.add_parser("list", help="list groups for a user")
    groups_list.add_argument("username", help="username")
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
        action="store_const",
        const="yaml",
        help="print as yaml",
    )

    # "perms"
    users_perms = sub.add_parser("perms", help="manage user permissions")
    perms_sub = users_perms.add_subparsers(
        dest="sub_sub_sub_command", help="Sub commands"
    )
    perms_sub.required = True
    perms_add = perms_sub.add_parser("add", help="add a permission")
    perms_add.add_argument("username", help="username")
    perms_add.add_argument("app", help="application")
    perms_add.add_argument("model", help="model")
    perms_add.add_argument("codename", help="codename")

    perms_del = perms_sub.add_parser("delete", help="remove a permssion")
    perms_del.add_argument("username", help="username")
    perms_del.add_argument("app", help="application")
    perms_del.add_argument("model", help="model")
    perms_del.add_argument("codename", help="codename")

    perms_list = perms_sub.add_parser("list", help="list permissions for a user")
    perms_list.add_argument("username", help="username")
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

    # "list"
    users_list = sub.add_parser("list", help="list users")
    out_format = users_list.add_mutually_exclusive_group()
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

    # "show"
    users_show = sub.add_parser("show", help="show user details")
    users_show.add_argument("username", help="username")
    out_format = users_show.add_mutually_exclusive_group()
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

    # "update"
    users_update = sub.add_parser("update", help="update a user")
    users_update.add_argument("username", help="username")
    users_update.add_argument("--email", default=None, help="email")
    users_update.add_argument("--first-name", default=None, help="first name")
    users_update.add_argument("--last-name", default=None, help="last name")
    users_update.add_argument(
        "--active",
        action="store_true",
        dest="is_active",
        default=None,
        help="active user",
    )
    users_update.add_argument(
        "--no-active",
        action="store_false",
        dest="is_active",
        default=None,
        help="no active user",
    )
    users_update.add_argument(
        "--staff",
        action="store_true",
        dest="is_staff",
        default=None,
        help="staff user",
    )
    users_update.add_argument(
        "--no-staff",
        action="store_false",
        dest="is_staff",
        default=None,
        help="no staff user",
    )
    users_update.add_argument(
        "--superuser",
        action="store_true",
        dest="is_superuser",
        default=None,
        help="superuser",
    )
    users_update.add_argument(
        "--no-superuser",
        action="store_false",
        dest="is_superuser",
        default=None,
        help="no superuser",
    )


def help_string():
    return "manage users"


def handle_add(proxy, options, _):
    proxy.auth.users.add(
        options.username,
        options.first_name,
        options.last_name,
        options.email,
        options.is_active,
        options.is_staff,
        options.is_superuser,
        options.ldap,
    )
    return 0


def handle_delete(proxy, options, _):
    proxy.auth.users.delete(options.username)
    return 0


def handle_groups(proxy, options, _):
    if options.sub_sub_sub_command == "add":
        proxy.auth.users.groups.add(options.username, options.group)
    elif options.sub_sub_sub_command == "delete":
        proxy.auth.users.groups.delete(options.username, options.group)
    else:
        groups = proxy.auth.users.groups.list(options.username)
        if options.output_format == "json":
            print(json.dumps(groups))
        elif options.output_format == "yaml":
            safe_yaml.dump(groups, sys.stdout)
        else:
            print("Groups:")
            for group in groups:
                print("* %s" % group)
    return 0


def handle_list(proxy, options, _):
    users = proxy.auth.users.list()
    if options.output_format == "json":
        print(json.dumps(users))
    elif options.output_format == "yaml":
        safe_yaml.dump(users, sys.stdout)
    else:
        print("Users:")
        for u in users:
            msg = "* %s" % u["username"]
            if u["first_name"] or u["last_name"]:
                msg += " (%s %s)" % (u["first_name"], u["last_name"])
            if u["is_staff"]:
                msg += " [staff]"
            if u["is_superuser"]:
                msg += " [superuser]"
            if not u["is_active"]:
                msg += " [INACTIVE]"
            print(msg)
    return 0


def handle_perms(proxy, options, _):
    if options.sub_sub_sub_command == "add":
        proxy.auth.users.perms.add(
            options.username, options.app, options.model, options.codename
        )
    elif options.sub_sub_sub_command == "delete":
        proxy.auth.users.perms.delete(
            options.username, options.app, options.model, options.codename
        )
    else:
        perms = proxy.auth.users.perms.list(options.username)
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
    user = proxy.auth.users.show(options.username)

    if options.output_format in ("json", "yaml"):
        date_joined = user.get("date_joined")
        user["date_joined"] = date_joined.value if date_joined else None
        last_login = user.get("last_login")
        user["last_login"] = last_login.value if last_login else None

    if options.output_format == "json":
        print(json.dumps(user))
    elif options.output_format == "yaml":
        safe_yaml.dump(user, sys.stdout)
    else:
        print("username   : %s (%d)" % (user["username"], user["id"]))
        print("first name : %s" % user["first_name"])
        print("last name  : %s" % user["last_name"])
        print("groups     : %s" % ", ".join(user["groups"]))
        print("permissions: %s" % ", ".join(user["permissions"]))
        print("email      : %s" % user["email"])
        print("active     : %s" % user["is_active"])
        print("staff      : %s" % user["is_staff"])
        print("superuser  : %s" % user["is_superuser"])
        print("date joined: %s" % user["date_joined"])
        print("last login : %s" % user["last_login"])


def handle_update(proxy, options, _):
    proxy.auth.users.update(
        options.username,
        options.first_name,
        options.last_name,
        options.email,
        options.is_active,
        options.is_staff,
        options.is_superuser,
    )
    return 0


def handle(proxy, options, config):
    handlers = {
        "add": handle_add,
        "delete": handle_delete,
        "groups": handle_groups,
        "list": handle_list,
        "perms": handle_perms,
        "show": handle_show,
        "update": handle_update,
    }
    return handlers[options.sub_sub_command](proxy, options, config)
