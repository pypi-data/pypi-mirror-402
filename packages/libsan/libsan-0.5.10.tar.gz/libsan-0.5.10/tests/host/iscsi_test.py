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

from unittest.mock import patch

import pytest
from libsan.host import iscsi

target = "localhost"


def test_install_initiator():
    if not iscsi.install():
        pytest.fail("FAIL: Could not install iSCSI initiator package")
    assert 1


@patch("libsan.host.iscsi.run")
def test_query_discovery(iscsi_run_func):
    discovery_output = """
SENDTARGETS:
DiscoveryAddress: localhost,3260
Target: iqn.2009-10.com.redhat:storage-0
    Portal: [::1]:3260,1
        Iface Name: default
iSNS:
No targets found.
STATIC:
No targets found.
FIRMWARE:
No targets found.
"""
    iscsi_run_func.return_value = (0, discovery_output)

    expected_ret = {
        "SENDTARGETS": {
            "localhost,3260": {
                "disc_addr": "localhost",
                "disc_port": "3260",
                "mode": "sendtargets",
                "targets": {
                    "iqn.2009-10.com.redhat:storage-0": {
                        "portal": {"address": "[::1]", "port": "3260"},
                        "iface": ["default"],
                    }
                },
            }
        },
        "iSNS": {},
        "STATIC": {},
        "FIRMWARE": {},
    }
    if iscsi.query_discovery() != expected_ret:
        pytest.fail("FAIL: Could not  query discovery iSCSI target")
    assert 1


@patch("libsan.host.iscsi.run")
def test_discovery(iscsi_run_func):
    discovery_output = "[::1]:3260,1 iqn.2009-10.com.redhat:storage-0"
    iscsi_run_func.return_value = (0, discovery_output)

    if not iscsi.discovery_st(target):
        pytest.fail("FAIL: Could not discovery iSCSI target")
    assert 1


@patch("libsan.host.linux.service_restart")
def test_set_iscsid_parameter(service_restart_func):
    service_restart_func.return_value = True
    if not iscsi.set_iscsid_parameter({"node.session.cmds_max": "4096", "node.session.queue_depth": "128"}):
        pytest.fail("FAIL: Unable to set iscsid parameter")
    assert 1
