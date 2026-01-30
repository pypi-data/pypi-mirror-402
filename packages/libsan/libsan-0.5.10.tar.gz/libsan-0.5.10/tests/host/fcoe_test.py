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


import unittest
from unittest.mock import call, patch

from libsan.host import fcoe
from libsan.host.cmdline import run

nic_2_driver = {"test_nic1": "ixgbe", "test_nic2": "bnx2x"}

fake_fcoeadm1 = {"host1": {"phy_nic": "test_nic1", "scsi_host": "host1"}}
fake_fcoeadm2 = {
    "host1": {"phy_nic": "test_nic1", "scsi_host": "host1"},
    "host2": {"phy_nic": "test_nic2", "scsi_host": "host2"},
}
# simulate first just one connection, than both
query_fcoeadm_i_outputs = [{}, {}, fake_fcoeadm1, fake_fcoeadm2]


def driver_of_nic(nic):
    return nic_2_driver[nic]


def _run(cmd, return_output=True, verbose=False):
    # To configure soft fcoe we need some tools to be available
    # We need to make sure setup_soft_fcoe would install them
    tool = cmd.split()[0]
    ret, _ = run(f"command -v {tool}", return_output=return_output, verbose=verbose)
    if ret != 0:
        return ret, f"Required command {tool} not installed"
    return 0, ""


class TestFCoE(unittest.TestCase):
    @patch("libsan.host.fcoe.run")
    @patch("libsan.host.linux.sleep")
    @patch("libsan.host.net.iface_up")
    @patch("libsan.host.net.iface_down")
    @patch("libsan.host.linux.service_enable")
    @patch("libsan.host.linux.service_restart")
    @patch("libsan.host.linux.service_start")
    def test_configure_intel_fcoe(
        self,
        service_start_func,
        service_restart_func,
        service_enable_func,
        iface_down_func,
        iface_up_func,
        sleep_func,
        run_func,
    ):
        service_start_func.return_value = True
        service_restart_func.return_value = True
        service_enable_func.return_value = True
        iface_down_func.return_value = True
        iface_up_func.return_value = True
        sleep_func.return_value = True
        run_func.return_value = 0, ""

        assert fcoe.configure_intel_fcoe("test_nic1", "fabric")

        assert run_func.call_count == 5
        run_calls = [
            call("dcbtool sc test_nic1 dcb on", return_output=True),
            call("dcbtool sc test_nic1 pfc e:1 a:1 w:1", return_output=True),
            call("dcbtool sc test_nic1 app:fcoe e:1 a:1 w:1", return_output=True),
            call("cp -f /etc/fcoe/cfg-ethx /etc/fcoe/cfg-test_nic1", return_output=True),
            call("sed -i -e 's/\\(MODE=.*\\)$/MODE=\\\"fabric\\\"/' /etc/fcoe/cfg-test_nic1", return_output=True),
        ]
        run_func.assert_has_calls(run_calls)

    @patch("libsan.host.fcoe.run")
    @patch("libsan.host.net.iface_up")
    @patch("libsan.host.linux.service_enable")
    @patch("libsan.host.linux.service_restart")
    def test_configure_bnx2fc_fcoe(self, service_restart_func, service_enable_func, iface_up_func, run_func):
        service_restart_func.return_value = True
        service_enable_func.return_value = True
        iface_up_func.return_value = True
        run_func.return_value = 0, ""

        assert fcoe.configure_bnx2fc_fcoe("test_nic2", "fabric")

        assert run_func.call_count == 3
        run_calls = [
            call("cp -f /etc/fcoe/cfg-ethx /etc/fcoe/cfg-test_nic2", return_output=True),
            call(
                "sed -i -e 's/\\(DCB_REQUIRED=.*\\)$/DCB_REQUIRED=\\\"no\\\"/' /etc/fcoe/cfg-test_nic2",
                return_output=True,
            ),
            call("sed -i -e 's/\\(MODE=.*\\)$/MODE=\\\"fabric\\\"/' /etc/fcoe/cfg-test_nic2", return_output=True),
        ]
        # print(run_func.call_args_list)
        run_func.assert_has_calls(run_calls)

    @patch("libsan.host.fcoe.query_fcoeadm_i")
    @patch("libsan.host.fcoe.configure_bnx2fc_fcoe")
    @patch("libsan.host.fcoe.configure_intel_fcoe")
    @patch("libsan.host.net.nm_conn_up")
    @patch("libsan.host.net.nm_conn_reload")
    @patch("libsan.host.net.nm_conn_mod")
    @patch("libsan.host.net.nm_get_conn")
    @patch("libsan.host.linux.is_installed")
    @patch("libsan.host.net.driver_of_nic")
    def test_enable_fcoe_on_nic(
        self,
        driver_of_nic_func,
        is_installed_func,
        nm_get_conn_func,
        nm_conn_mod_func,
        nm_conn_reload_func,
        nm_conn_up_func,
        configure_intel_fcoe_func,
        configure_bnx2fc_fcoe_func,
        query_fcoeadm_i_func,
    ):
        driver_of_nic_func.side_effect = driver_of_nic
        is_installed_func.return_value = True
        nm_get_conn_func.return_value = "test_conn"
        nm_conn_mod_func.return_value = True
        nm_conn_reload_func.return_value = True
        nm_conn_up_func.return_value = True
        configure_intel_fcoe_func.return_value = True
        configure_bnx2fc_fcoe_func.return_value = True
        query_fcoeadm_i_func.side_effect = query_fcoeadm_i_outputs

        assert fcoe.enable_fcoe_on_nic("test_nic1")
        assert fcoe.enable_fcoe_on_nic("test_nic2")
