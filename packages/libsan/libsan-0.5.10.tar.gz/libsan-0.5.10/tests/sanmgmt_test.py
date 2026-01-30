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
from libsan import sanmgmt


def test_load_san_config():
    san_obj = sanmgmt.SanMgmt()
    if not san_obj.load_conf():
        pytest.fail("Unable to load config")

    for hw_entry in san_obj.san_conf_dict:
        hw_info = san_obj.san_conf_dict[hw_entry]
        if "class_name" in hw_info:
            # Try to load class
            if not sanmgmt.get_class(hw_info["module_name"], hw_info["class_name"]):
                pytest.fail("Unable to load class")
            print("loaded class from {}.{}".format(hw_info["module_name"], hw_info["class_name"]))

    assert 1
