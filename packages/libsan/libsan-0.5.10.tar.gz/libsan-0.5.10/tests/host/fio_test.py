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
from libsan.host import fio
from libsan.host.cmdline import run


def test_fio():
    if not fio.install_fio():
        pytest.fail("Unable to install fio")

    output_file = "fio.test"

    # Create a file big enough to use by FIO
    run("dd if=/dev/zero of=%s count=20 bs=1024k" % output_file)

    try:
        fio_pid = fio.fio_stress_background(output_file, size="1m")
    except Exception as e:
        pytest.fail("FAIL: Exception: %s" % e)

    # Make sure background process does not generate exception
    print("INFO: Waiting FIO process to finish")
    try:
        _, exit_status = os.waitpid(fio_pid, 0)
    except Exception as e:
        pytest.fail("FAIL: Exception: %s" % e)

    if exit_status != 0:
        pytest.fail("FAIL: there was some error running FIO")
    try:
        os.remove(output_file)
    except Exception:
        pytest.fail("FAIL: Could not delete %s" % output_file)

    assert 1
