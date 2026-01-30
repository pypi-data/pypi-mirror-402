#!/usr/bin/python

import os

import pytest
from libsan.host.cmdline import run


def test_unicode():
    # Read unicode text file from same directory the script is located.
    test_dir = os.path.dirname(__file__)
    if run("cat %s/unicode.txt" % test_dir) != 0:
        pytest.fail("Unable to read unicode.txt")
