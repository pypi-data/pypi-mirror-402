#!/usr/bin/python

# Copyright (C) 2021 Red Hat, Inc.
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


import io
import re
import sys
import unittest

from libsan.host.cmdline import run


class TestCmdline(unittest.TestCase):
    def test_run_verbose(self):
        test_msg = "run test message"
        # write to stderr, the message should be shown in the test
        test_cmd = f"echo {test_msg} >&2"
        running_regex = rf"INFO: \[\d+-\d+-\d+ \d+:\d+:\d+\] Running: '{test_cmd}'..."
        cmd_output_regex = f"^{test_msg}$"

        new_callable = io.StringIO()
        sys.stdout = new_callable
        # By default is verbose true
        assert run(test_cmd) == 0
        sys.stdout = sys.__stdout__
        assert re.search(running_regex, new_callable.getvalue().split("\n")[0])
        cmd_output_regex = f"^{test_msg}$"
        assert re.search(cmd_output_regex, new_callable.getvalue().split("\n")[1])
        sys.stdout = sys.__stdout__

        # not verbose
        new_callable = io.StringIO()
        sys.stdout = new_callable
        assert run(test_cmd, verbose=False) == 0
        sys.stdout = sys.__stdout__
        assert new_callable.getvalue() == ""
        sys.stdout = sys.__stdout__

    def test_run_force_flush(self):
        test_msg = "run test message"
        test_cmd = f"echo {test_msg}"
        running_regex = rf"INFO: \[\d+-\d+-\d+ \d+:\d+:\d+\] Running: '{test_cmd}'..."
        cmd_output_regex = f"^{test_msg}$"

        new_callable = io.StringIO()
        sys.stdout = new_callable
        assert run(test_cmd, force_flush=True) == 0
        sys.stdout = sys.__stdout__
        assert re.search(running_regex, new_callable.getvalue().split("\n")[0])
        cmd_output_regex = f"^{test_msg}$"
        assert re.search(cmd_output_regex, new_callable.getvalue().split("\n")[1])
        sys.stdout = sys.__stdout__

    def test_run_return_output(self):
        test_msg = "run test message"
        test_cmd = f"echo {test_msg}"
        running_regex = rf"INFO: \[\d+-\d+-\d+ \d+:\d+:\d+\] Running: '{test_cmd}'..."
        cmd_output_regex = f"^{test_msg}$"

        new_callable = io.StringIO()
        sys.stdout = new_callable
        assert run(test_cmd, return_output=True) == (0, test_msg)
        sys.stdout = sys.__stdout__
        assert re.search(running_regex, new_callable.getvalue().split("\n")[0])
        cmd_output_regex = f"^{test_msg}$"
        assert re.search(cmd_output_regex, new_callable.getvalue().split("\n")[1])
        sys.stdout = sys.__stdout__

    def test_run_fail_return_output(self):
        failure_msg = "ls: cannot access 'invalid_file': No such file or directory"
        test_cmd = "ls invalid_file"
        running_regex = rf"INFO: \[\d+-\d+-\d+ \d+:\d+:\d+\] Running: '{test_cmd}'..."
        cmd_output_regex = f"^{failure_msg}$"

        new_callable = io.StringIO()
        sys.stdout = new_callable
        assert run(test_cmd, return_output=True) == (2, failure_msg)
        sys.stdout = sys.__stdout__
        assert re.search(running_regex, new_callable.getvalue().split("\n")[0])
        cmd_output_regex = f"^{failure_msg}$"
        assert re.search(cmd_output_regex, new_callable.getvalue().split("\n")[1])
        sys.stdout = sys.__stdout__

    def test_run_timeout(self):
        test_cmd = "sleep 9"
        expected_retcode = 124
        assert run(test_cmd, return_output=True, timeout=1) == (expected_retcode, "")
        assert run(test_cmd, return_output=True, timeout=1, force_flush=True) == (expected_retcode, "")
