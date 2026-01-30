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
import sys
import unittest

import libsan
import pytest


class TestLibsan(unittest.TestCase):
    def test_print(self):
        # simple print
        new_callable = io.StringIO()
        sys.stdout = new_callable
        libsan._print("test _print")
        sys.stdout = sys.__stdout__
        assert new_callable.getvalue().endswith("test _print\n")
        sys.stdout = sys.__stdout__

        # DEBUG print
        new_callable = io.StringIO()
        sys.stdout = new_callable
        libsan._print("DEBUG: test _print")
        sys.stdout = sys.__stdout__
        assert new_callable.getvalue().endswith("DEBUG:(%s) test _print\n" % __name__)
        sys.stdout = sys.__stdout__

        # FATAL print
        new_callable = io.StringIO()
        sys.stdout = new_callable
        with pytest.raises(RuntimeError, match=r"FATAL:\(tests.libsan_test\) test _print"):
            libsan._print("FATAL: test _print")
        sys.stdout = sys.__stdout__
        assert new_callable.getvalue().endswith("FATAL:(%s) test _print\n" % __name__)
        sys.stdout = sys.__stdout__
