# vim: set ts=4

# Copyright 2025-present Linaro Limited
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

    if version < (2025, 5):
        return

    # "add"
    tokens_add = sub.add_parser("add", help="add a token")
    tokens_add.add_argument("name", help="token name")
    tokens_add.add_argument("--token", required=True, help="token string")

    # "delete"
    tokens_delete = sub.add_parser("delete", help="delete a token")
    tokens_delete.add_argument("name", help="token name")

    # "list"
    tokens_list = sub.add_parser("list", help="list tokens")
    out_format = tokens_list.add_mutually_exclusive_group()
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
    tokens_show = sub.add_parser("show", help="show token string")
    tokens_show.add_argument("name", help="token name")


def help_string():
    return "manage user remote artifact tokens"


def handle_add(proxy, options):
    proxy.scheduler.remote_artifact_tokens.add(options.name, options.token)
    return 0


def handle_delete(proxy, options):
    proxy.scheduler.remote_artifact_tokens.delete(options.name)
    return 0


def handle_list(proxy, options):
    tokens = proxy.scheduler.remote_artifact_tokens.list()
    if options.output_format == "json":
        print(json.dumps(tokens))
    elif options.output_format == "yaml":
        safe_yaml.dump(tokens, sys.stdout)
    else:
        print("tokens:")
        for token in tokens:
            if token["token"]:
                print(f"* {token['name']}: {token['token']}")
            else:
                print(f"* {token['name']}:")
    return 0


def handle_show(proxy, options):
    token = proxy.scheduler.remote_artifact_tokens.show(options.name)
    print(token)
    return 0


def handle(proxy, options, _):
    handlers = {
        "add": handle_add,
        "delete": handle_delete,
        "list": handle_list,
        "show": handle_show,
    }
    return handlers[options.sub_sub_command](proxy, options)
