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

import os

import pytest
from libsan.host import dt, linux


def test_dt():
    if not dt.install_dt():
        pytest.fail("Unable to install dt")

    if linux.is_docker():
        print("SKIP: DT has a bug and does not work on container")
        return

    output_file = "dt.test"
    try:
        dt_pid = dt.dt_stress_background(output_file, limit="100m", verbose=True)
    except Exception as e:
        pytest.fail("FAIL: Exception: %s" % e)

    # Make sure background process does not generate exception
    print("INFO: Waiting DT process to finish")
    try:
        _, exit_status = os.waitpid(dt_pid, 0)
    except Exception as e:
        pytest.fail("FAIL: Exception: %s" % e)

    if exit_status != 0:
        pytest.fail("FAIL: there was some error running DT")

    if not os.remove(output_file):
        pytest.fail("FAIL: Could not delete %s" % output_file)

    assert 1
