#!/usr/bin/python

# Copyright (C) 2016 Red Hat, Inc.
# This file is part of libsan.
#
# libsan is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# libsan is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with libsan.  If not, see <http://www.gnu.org/licenses/>.

import unittest

import pytest
from libsan.host import ssh
from libsan.host.cmdline import run
from libsan.host.linux import is_docker

host = "localhost"
user = "root"
passwd = "redhat"
command = "uname -r"


def connect():
    return ssh.connect(host=host, user=user, passwd=passwd, port=22)


class TestSSH(unittest.TestCase):
    def test_connect(self):
        if not is_docker():
            assert connect() is not None

    def test_connect_no_passwd(self):
        assert ssh.connect(host=host, user=user, passwd="") is None

    def test_connect_passwd_is_none(self):
        assert ssh.connect(host=host, user=user, passwd=None) is None

    def test_connect_no_user(self):
        assert ssh.connect(host=host, user="", passwd=passwd) is None

    def test_connect_user_is_none(self):
        assert ssh.connect(host=host, user=None, passwd=passwd) is None

    def test_connect_no_host(self):
        assert ssh.connect(host="", user=user, passwd=passwd, max_attempt=1) is None

    def test_disconnect(self):
        if not is_docker():
            assert ssh.disconnect(connect()) is True

    def test_disconnect_none(self):
        with pytest.raises(Exception) as context:  # noqa: PT011
            ssh.disconnect(None)
        assert "'NoneType' object has no attribute" in str(context)

    def test_command(self):
        if not is_docker():
            assert ssh.run_cmd(connect(), command) == 0

    def test_command_output(self):
        if not is_docker():
            command_run = run(command, return_output=True)
            command_ssh = ssh.run_cmd(connect(), command, return_output=True)
            assert command_run[1] + "\n" == command_ssh[1]

    def test_command_invoke_shell(self):
        if not is_docker():
            assert ssh.run_cmd(connect(), command, invoke_shell=True, expect="# ") == 0
