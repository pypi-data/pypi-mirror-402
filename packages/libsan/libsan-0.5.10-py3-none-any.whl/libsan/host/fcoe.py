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


"""fcoe.py: Module to manipulate FCoE devices."""

__author__ = "Bruno Goncalves"
__copyright__ = "Copyright (c) 2016 Red Hat, Inc. All rights reserved."

import os.path
import re  # regex

import libsan.host.linux
import libsan.host.net
from libsan import _print
from libsan.host.cmdline import run

supported_soft_fcoe_drivers = ["ixgbe", "bnx2x"]


def configure_intel_fcoe(nic, mode):
    if not libsan.host.linux.service_start("lldpad"):
        return False

    if not libsan.host.net.iface_down(nic):
        return False

    if not libsan.host.net.iface_up(nic):
        return False

    libsan.host.linux.sleep(5)

    retcode, output = run("dcbtool sc %s dcb on" % nic, return_output=True)
    if retcode != 0:
        print(output)
        return False

    libsan.host.linux.sleep(5)

    retcode, output = run("dcbtool sc %s pfc e:1 a:1 w:1" % nic, return_output=True)
    if retcode != 0:
        print(output)
        return False

    retcode, output = run("dcbtool sc %s app:fcoe e:1 a:1 w:1" % nic, return_output=True)
    if retcode != 0:
        print(output)
        return False

    retcode, output = run("cp -f /etc/fcoe/cfg-ethx /etc/fcoe/cfg-%s" % nic, return_output=True)
    if retcode != 0:
        print(output)
        return False

    retcode, output = run(rf"sed -i -e 's/\(MODE=.*\)$/MODE=\"{mode}\"/' /etc/fcoe/cfg-{nic}", return_output=True)
    if retcode != 0:
        print(output)
        return False

    if not libsan.host.linux.service_restart("lldpad"):
        return False

    if not libsan.host.linux.service_restart("fcoe"):
        return False

    if not libsan.host.linux.service_enable("lldpad"):
        return False

    if not libsan.host.linux.service_enable("fcoe"):
        return False

    return True


def configure_bnx2fc_fcoe(nic, mode):
    if not libsan.host.net.iface_up(nic):
        return False

    retcode, output = run("cp -f /etc/fcoe/cfg-ethx /etc/fcoe/cfg-%s" % nic, return_output=True)
    if retcode != 0:
        print(output)
        return False

    retcode, output = run(
        r"sed -i -e 's/\(DCB_REQUIRED=.*\)$/DCB_REQUIRED=\"no\"/' /etc/fcoe/cfg-%s" % nic, return_output=True
    )
    if retcode != 0:
        print(output)
        return False

    retcode, output = run(rf"sed -i -e 's/\(MODE=.*\)$/MODE=\"{mode}\"/' /etc/fcoe/cfg-{nic}", return_output=True)
    if retcode != 0:
        print(output)
        return False

    if not libsan.host.linux.service_restart("lldpad"):
        return False

    if not libsan.host.linux.service_restart("fcoe"):
        return False

    if not libsan.host.linux.service_enable("lldpad"):
        return False

    if not libsan.host.linux.service_enable("fcoe"):
        return False

    return True


def enable_fcoe_on_nic(nic, mode="fabric"):
    if not nic:
        return False

    driver = libsan.host.net.driver_of_nic(nic)
    if not driver:
        _print("FAIL: Could not find driver for %s" % nic)
        return False

    if driver not in supported_soft_fcoe_drivers:
        _print(f"FAIL: NIC {nic} via {driver} is not supported soft FCoE")
        return False

    if libsan.host.linux.is_installed("NetworkManager"):
        conn = libsan.host.net.nm_get_conn(nic)
        libsan.host.net.nm_conn_mod(conn, "connection.autoconnect", "yes")
        libsan.host.net.nm_conn_reload()
        libsan.host.net.nm_conn_up(conn)
    else:
        print("WARN: NetworkManager not found, trying ifcfg..")
        libsan.host.net.set_ifcfg(nic, {"ONBOOT": "yes"})

    configure_fcoe = None
    if driver == "ixgbe":
        configure_fcoe = configure_intel_fcoe
    if driver == "bnx2x":
        configure_fcoe = configure_bnx2fc_fcoe

    if not configure_fcoe(nic, mode):
        print("FAIL: couldn't configure FCoE on %s" % nic)
        return False

    max_wait_time = 180  # wait for maximum 3 minutes
    _print("INFO: Waiting FCoE session with timeout %d seconds" % max_wait_time)
    while max_wait_time >= 0:
        libsan.host.linux.sleep(1)
        max_wait_time -= 1
        # need to query fcoeadmin
        fcoe_dict = query_fcoeadm_i()
        if not fcoe_dict:
            _print("INFO: No FCoE session found, will keep waiting timeout %s seconds" % max_wait_time)
            continue
        for host in list(fcoe_dict.keys()):
            if fcoe_dict[host]["phy_nic"] == nic:
                _print("INFO: FCoE session created for {} as SCSI Host: {}".format(nic, fcoe_dict[host]["scsi_host"]))
                return fcoe_dict
        _print("INFO: No FCoE session created yet for NIC %s, will keep waiting. timeout %d" % (nic, max_wait_time))
    run("fcoeadm -i")
    _print("FAIL: No FCoE session created for NIC %s" % nic)
    return None


def query_fcoeadm_i():
    cmd = "fcoeadm -i"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        if retcode == 2:
            _print("INFO: No FCoE interface is configured")
            return None
        else:
            _print("FAIL: running %s" % cmd)
            print(output)
            return None

    lines = output.split("\n")
    driver_regex = re.compile(r".*Driver:\s+(\S+)\s+(\S+)")
    nic_regex = re.compile(r".*Symbolic Name:\s+(\S+).* over (\S+)")
    scsi_regex = re.compile(r".*OS Device Name: +host(\d+)")
    node_regex = re.compile(r".*Node Name:\s+(\S+)")
    port_regex = re.compile(r".*Port Name:\s+(\S+)")
    fabric_regex = re.compile(r".*Fabric Name:\s+(\S+).*")
    speed_regex = re.compile(r".*  Speed:\s+(.*)")
    supported_speed_regex = re.compile(r".*Supported Speed:\s+(.*)")
    maxframesize_regex = re.compile(r".*MaxFrameSize:\s+(.*)")
    fcid_regex = re.compile(r".*FC-ID \(Port ID\):\s+(\S+)")
    state_regex = re.compile(r".*State:\s+(\S+)")

    fcoeadm_dict = {}
    fcoe_driver = None
    fcoe_driver_version = None
    for line in lines:
        m = driver_regex.match(line)
        if m:
            # this information can be used for more than 1 port
            fcoe_driver = m.group(1)
            fcoe_driver_version = m.group(2)
            continue

        m = nic_regex.match(line)
        if m:
            info_dict = {}
            info_dict["driver"] = fcoe_driver
            info_dict["driver_version"] = fcoe_driver_version
            info_dict["nic"] = m.group(2)
            info_dict["nic_driver"] = libsan.host.net.driver_of_nic(m.group(2))
            info_dict["phy_nic"] = libsan.host.net.phy_nic_of(m.group(2))
            continue

        m = node_regex.match(line)
        if m:
            info_dict["node_name"] = m.group(1)
            continue

        m = port_regex.match(line)
        if m:
            info_dict["port_name"] = m.group(1)
            continue

        m = fabric_regex.match(line)
        if m:
            info_dict["fabric_name"] = m.group(1)
            continue

        m = speed_regex.match(line)
        if m:
            info_dict["speed"] = m.group(1)
            continue

        m = supported_speed_regex.match(line)
        if m:
            info_dict["supported_speed"] = m.group(1)
            continue

        m = maxframesize_regex.match(line)
        if m:
            info_dict["max_frame_size"] = m.group(1)
            continue

        m = fcid_regex.match(line)
        if m:
            info_dict["fcid"] = m.group(1)
            continue

        m = state_regex.match(line)
        if m:
            info_dict["state"] = m.group(1)
            continue

        m = scsi_regex.match(line)
        if m:
            info_dict["scsi_host"] = "host" + m.group(1)
            info_dict["scsi_host_id"] = m.group(1)
            fcoeadm_dict[info_dict["scsi_host_id"]] = info_dict

    if not fcoeadm_dict:
        return None
    return fcoeadm_dict


def setup_soft_fcoe(mode="fabric"):
    """Setup soft FCoE initiator. It supports ixgbe and bnx2x drivers
    The arguments are:
    \tmode:                         The mode defaults to fabric but this option allows the selection of vn2vn mode
    Returns:
    \tTrue:                         If sessions are established
    \tFalse:                        If there was some problem
    """

    libsan.host.linux.install_package("fcoe-utils")

    nic_drv_dict = libsan.host.net.nic_2_driver()
    if not nic_drv_dict:
        _print("FAIL: No NIC found on this server, cannot enable soft FCoE")
        return False

    # print nic_drv_dict
    fcoe_nics = []
    for nic in list(nic_drv_dict.keys()):
        if nic_drv_dict[nic] in supported_soft_fcoe_drivers:
            # _print("INFO: Need to configure %s" % nic)
            fcoe_nics.append(nic)
    if not fcoe_nics:
        _print("INFO: Server has no supported soft FCoE adapter")
        print(nic_drv_dict)
        return False

    fcoeadm_dict = query_fcoeadm_i()
    nic_need_setup = []
    if not fcoeadm_dict:
        nic_need_setup = fcoe_nics
    else:
        # Check if NIC is not already configured
        enabled_nics = []
        for host in list(fcoeadm_dict.keys()):
            enabled_nics.append(fcoeadm_dict[host]["phy_nic"])

        for nic in fcoe_nics:
            if nic not in enabled_nics:
                nic_need_setup.append(nic)
        if not nic_need_setup:
            _print("INFO: All NICs already have FCoE session running:")
            print(fcoe_nics)
            return True

    _print("INFO: Going to enable FCoE on these NICs:")
    for nic in nic_need_setup:
        print(f"\t{nic} ({nic_drv_dict[nic]})")

    error = 0
    for nic in nic_need_setup:
        if not enable_fcoe_on_nic(nic, mode=mode):
            _print("FAIL: Could not enable FCoE on %s" % nic)
            error += 1

    if error:
        run("fcoeadm -i")
        run("ip a")
        return False

    # Wait for server to detect FCoE devices
    _print("INFO: Waiting 120s for devices to be created")
    libsan.host.linux.sleep(120)
    return True


def unconfigure_soft_fcoe():
    """Unconfigure FCoE initiator.
     * unload the related modules
     * stop the fcoe/lldpad daemon
     * chkconfig fcoe/lldpad off
     * delete the /etc/fcoe/cfg-xxx files
     * load the modules

    Returns:
    \tTrue:                         if unconfigure is checked on fcoe initiator
    \tFalse:                        if configure is checked on fcoe initiator
    """

    ret = True
    driver = ""

    # lldpad will still be activated automatically by lldpad.socket
    run("service lldpad stop")
    run("service fcoe stop")

    if run('service fcoe status|grep "Active: active" ') == 0:
        ret = False
        _print("FAIL: Could not stop service of fcoe")

    if run("chkconfig lldpad off") != 0:
        ret = False
        _print("FAIL: Could not disable lldpad on chkconfig")

    if run("chkconfig fcoe off") != 0:
        ret = False
        _print("FAIL: Could not disable fcoe on chkconfig")

    nic_drv_dict = libsan.host.net.nic_2_driver()
    if nic_drv_dict:
        for nic in list(nic_drv_dict.keys()):
            if nic_drv_dict[nic] in supported_soft_fcoe_drivers:
                driver = nic_drv_dict[nic]
                con_path = "/etc/fcoe/cfg-%s" % nic

                if os.path.isfile(con_path) and run("rm -rf %s" % con_path) != 0:
                    ret = False
                    _print("FAIL: Could not delete %s" % con_path)
        if driver:
            if run("modprobe -r %s" % driver) != 0:
                ret = False
                _print("FAIL: Could not unload module %s" % driver)

            if run("modprobe %s" % driver) != 0:
                ret = False
                _print("FAIL: Could not load module %s" % driver)

    return ret


def get_sw_fcoe_nics_n_driver():
    """Get the FCoE nics and its' drivers

    Returns:
    \tstore_dict:                         the dict of store the nics and drivers
    """

    store_dict = {}
    nic_drv_dict = libsan.host.net.nic_2_driver()

    if nic_drv_dict:
        for nic in list(nic_drv_dict.keys()):
            if nic_drv_dict[nic] in supported_soft_fcoe_drivers:
                driver = nic_drv_dict[nic]
                store_dict[nic] = driver

    return store_dict
