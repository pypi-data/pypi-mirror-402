#!/usr/bin/python
import pytest

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
from libsan.host import loopdev


def test_loopdev():
    dev = loopdev.create_loopdev()
    if not dev:
        print("SKIP: Could not create loop device")
        return

    if not loopdev.delete_loopdev(dev):
        pytest.fail("FAIL: Could not delete loop device")

    assert 1
