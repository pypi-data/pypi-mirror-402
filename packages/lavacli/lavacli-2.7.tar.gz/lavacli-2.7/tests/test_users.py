# vim: set ts=4

# Copyright 2018 Rémi Duraffort
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

import sys
import xmlrpc.client

from lavacli import main


def test_users_add_active_staff_superuser(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "add",
            "--staff",
            "--superuser",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.add",
                "args": ("user1", None, None, None, True, True, True, False),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_users_add_no_active(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "add",
            "--no-active",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.add",
                "args": ("user1", None, None, None, False, False, False, False),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_users_add_ldap(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "add",
            "--ldap",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.add",
                "args": ("user1", None, None, None, True, False, False, True),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_users_update_info(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "update",
            "--first-name",
            "first",
            "--last-name",
            "last",
            "--email",
            "user1@email.io",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.update",
                "args": ("user1", "first", "last", "user1@email.io", None, None, None),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_users_update_active_staff_superuser(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "update",
            "--active",
            "--staff",
            "--superuser",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.update",
                "args": ("user1", None, None, None, True, True, True),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""


def test_users_update_no_active_no_staff_no_superuser(setup, monkeypatch, capsys):
    version = "2023.03"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "lavacli",
            "users",
            "update",
            "--no-active",
            "--no-staff",
            "--no-superuser",
            "user1",
        ],
    )
    monkeypatch.setattr(
        xmlrpc.client.ServerProxy,
        "data",
        [
            {"request": "system.version", "args": (), "ret": version},
            {
                "request": "auth.users.update",
                "args": ("user1", None, None, None, False, False, False),
                "ret": None,
            },
        ],
    )
    assert main() == 0
    out, err = capsys.readouterr()
    assert out == ""
    assert err == ""
