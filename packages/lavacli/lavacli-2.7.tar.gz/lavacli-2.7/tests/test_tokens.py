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
import xmlrpc.client

from lavacli import main


def test_tokens_add(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(
        sys, "argv", ["lavacli", "tokens", "add", "n1", "--token", "v1"]
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.add",
                "args": ("n1", "v1"),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    assert capsys.readouterr()[0] == ""


def test_tokens_delete(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(sys, "argv", ["lavacli", "tokens", "delete", "n1"])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.delete",
                "args": ("n1",),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    assert capsys.readouterr()[0] == ""


def test_tokens_list(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(sys, "argv", ["lavacli", "tokens", "list"])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.list",
                "args": (),
                "ret": [
                    {"name": "n1", "token": "v1"},
                    {"name": "n2", "token": "v2"},
                ],
            },
        ],
    )
    assert main() == 0
    assert (
        capsys.readouterr()[0]
        == """tokens:
* n1: v1
* n2: v2
"""
    )


def test_tokens_list_json(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(sys, "argv", ["lavacli", "tokens", "list", "--json"])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.list",
                "args": (),
                "ret": [
                    {"name": "n1", "token": "v1"},
                    {"name": "n2", "token": "v2"},
                ],
            },
        ],
    )
    assert main() == 0
    assert json.loads(capsys.readouterr()[0]) == [
        {"name": "n1", "token": "v1"},
        {"name": "n2", "token": "v2"},
    ]


def test_tokens_list_yaml(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(sys, "argv", ["lavacli", "tokens", "list", "--yaml"])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.list",
                "args": (),
                "ret": [
                    {"name": "n1", "token": "v1"},
                    {"name": "n2", "token": "v2"},
                ],
            },
        ],
    )
    assert main() == 0
    assert (
        capsys.readouterr()[0]
        == """- {name: n1, token: v1}
- {name: n2, token: v2}
"""
    )


def test_tokens_show(setup, monkeypatch, capsys):
    version = "2025.05"
    monkeypatch.setattr(sys, "argv", ["lavacli", "tokens", "show", "n1"])
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "scheduler.remote_artifact_tokens.show",
                "args": ("n1",),
                "ret": "v1",
            },
        ],
    )
    assert main() == 0
    assert capsys.readouterr()[0] == "v1\n"
