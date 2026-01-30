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

"""ontap.py: Module to manager NetApp Ontap Array with API,
the system software should higher than 9.6.
"""

__author__ = "Guangwu Zhang"
__copyright__ = "Copyright (c) 2016 Red Hat, Inc. All rights reserved."

import base64
import json
import socket
import time

import libsan.host.fc
import libsan.host.linux
import libsan.host.scsi
import libsan.misc.size
from libsan import _print
from netapp_ontap import HostConnection, NetAppRestError, config
from netapp_ontap.resources import (
    CLI,
    FcInterface,
    Igroup,
    IgroupInitiator,
    IpInterface,
    Lun,
    LunMap,
    Node,
    Software,
    Svm,
    Volume,
)


def _lun_serial2wwid(serial):
    """Usage
        _lun_serial2wwid(netapp_serial)
    Purpose
        Convert netapp serial to WWID.
        1. Convert serial to hex string
        2. add '360a98000' at the head
    Parameter
        $netapp_serial  # like '2FiCl+BOAef9'
    Returns
        wwid
    """
    if not serial:
        return None

    # toHex = lambda x:"".join([hex(ord(c))[2:].zfill(2) for c in x])
    wwid = serial

    # wwid = toHex(wwid)
    wwid = base64.b16encode(str.encode(wwid))
    wwid = "3600a0980" + wwid.decode()
    return wwid.lower()


class ontap:  # noqa: N801
    def __init__(
        self,
        hostname,
        user,
        passwd,
        timeout=None,
        san_dev=None,
    ):
        self.hostname = hostname
        self.user = user
        self.passwd = passwd
        self.san_dev_name = san_dev
        self.luns = None
        self.igroup = None
        self.vol = None
        self.svm = None
        self.wwid = None
        self.san_conf_path = None
        self.sa_conf_dict = None
        config.CONNECTION = HostConnection(
            self.hostname, username=self.user, password=self.passwd, verify=False, poll_timeout=timeout
        )

    def set_san_conf_path(self, san_conf_path):
        self.san_conf_path = san_conf_path
        return True

    def set_sa_conf(self, sa_conf_dict):
        self.sa_conf_dict = sa_conf_dict
        return True

    def get_sa_conf(self):
        return self.sa_conf_dict

    def lun_info(self, lun_name):
        """Query detailed information of specific LUN"""
        if not lun_name:
            _print("FAIL: lun_info - requires lun_name")
            return None
        luns_dict = self.query_all_lun_info(recheck=True) if not self.luns or lun_name not in self.luns else self.luns

        if not luns_dict:
            _print("FAIL: lun_info() - Could not query all lun info")
            return None
        if lun_name in list(luns_dict.keys()):
            return luns_dict[lun_name]

        _print("INFO: lun_info(): Could not find LUN %s" % lun_name)
        return None

    def get_nodes(self, ip=None):
        """Node name: na-fas8080b
        Node name: na-fas8080a
        """
        nodes = {}

        try:
            for node in Node.get_collection():
                node.get()
                nodes[node.name] = {}
                nodes[node.name]["name"] = node.name
                nodes[node.name]["uuid"] = node.uuid
                nodes[node.name]["state"] = node.state
                nodes[node.name]["version"] = f"{node.version.generation}.{node.version.major}"
                nodes[node.name]["ip"] = node.management_interfaces[0].ip.address
                if socket.gethostbyname(ip) == node.management_interfaces[0].ip.address:
                    return nodes[node.name]

        except NetAppRestError as error:
            _print("FAIL: Error: %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return nodes

    def get_version(self):
        sw = Software()
        sw.get()
        return sw["version"]

    def get_svms(self):
        vms = {}
        try:
            for svm in Svm.get_collection(fields="uuid"):
                vms[svm.name] = svm.uuid
        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return vms

    def get_vols(self, vm_name):
        vols = {}
        try:
            for volume in Volume.get_collection(**{"svm.name": vm_name}, fields="uuid"):
                vols[volume.name] = volume.uuid
        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return vols

    def get_igroups(self, vm_name, igroupname=None, h_wwpn=None):
        igroups = {}
        try:
            for igroup in Igroup.get_collection(**{"svm.name": vm_name}, fields="uuid"):
                igroup.get()
                igroups[igroup.name] = {}
                igroups[igroup.name]["name"] = igroup.name
                igroups[igroup.name]["uuid"] = igroup.uuid
                igroups[igroup.name]["os_type"] = igroup.os_type
                igroups[igroup.name]["svm"] = {igroup.svm.name: igroup.svm.uuid}
                igroups[igroup.name]["type"] = igroup.protocol
                igroups[igroup.name]["delete_on_unmap"] = igroup.delete_on_unmap
                igroups[igroup.name]["members"] = []
                if hasattr(igroup, "initiators"):
                    igroups[igroup.name]["members"] = [init.name for init in igroup.initiators]

                if vm_name == igroup.svm.name:
                    if isinstance(h_wwpn, list) and all(wwpn in igroups[igroup.name]["members"] for wwpn in h_wwpn):
                        return igroups[igroup.name]
                    if igroupname == igroup.name:
                        return igroups[igroup.name]

        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return igroups

    def get_h_wwpn(
        self,
    ):
        return libsan.host.fc.h_wwpn_of_host()

    def get_initiators(self, vm_name, igroup_name):
        init_name = []
        igroup_uuid = ""
        igroup = self.get_igroups(vm_name, igroup_name)
        if "uuid" in igroup:
            igroup_uuid = igroup["uuid"]
        else:
            _print(f"FAIL: Could not find the igroup uuid with {igroup_name} in svm {vm_name}")
            return init_name

        try:
            for ini in IgroupInitiator.get_collection(igroup_uuid):
                init_name.append(ini.name)

        except NetAppRestError as error:
            _print("FAIL: Error:- %s " % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return init_name

    @staticmethod
    def capability():
        """Indicates supported operation on array"""
        cap_dict = {}
        cap_dict["lun_info"] = True
        cap_dict["lun_query"] = True
        cap_dict["lun_create"] = True
        cap_dict["lun_map"] = True
        cap_dict["lun_unmap"] = True
        cap_dict["lun_remove"] = True
        cap_dict["lun_grow"] = False
        cap_dict["lun_shrink"] = False
        cap_dict["lun_trepass"] = False
        cap_dict["lun_thinp"] = False
        cap_dict["sa_ctrler_reboot"] = True
        return cap_dict

    def get_lun_from_wwid(self, wwid):
        all_luns = self.query_all_lun_info()
        for lun_name in list(all_luns.keys()):
            if all_luns[lun_name]["wwid"] == wwid and all_luns[lun_name]["mapped"]:
                self.svm = all_luns[lun_name]["svm"]
                self.vol = all_luns[lun_name]["vol"]
                self.igroup = all_luns[lun_name]["map_infos"][0]["igroup_name"]
                return all_luns[lun_name]
        return None

    def query_all_luns(self, recheck=False):
        return sorted(self.query_all_lun_info(recheck=recheck).keys())

    def query_all_lun_info(self, recheck=False):
        """Lun Name:- /vol/fc_vol_5/dynamic_lun; Lun UUID:- 6668c02e-a0c1-490f-a932-e8e998d72731
        Lun Name:- /vol/tmp_luns_vol/lun0; Lun UUID:- 99be6020-b952-467c-b634-ffe4c994bf13
        """
        luns = {}
        if self.luns and not recheck:
            return self.luns

        map_luns = self.get_map_luns()
        try:
            for lun in Lun.get_collection():
                lun.get()
                luns[lun.name] = {}
                luns[lun.name]["uuid"] = lun["uuid"]
                luns[lun.name]["name"] = lun["name"]
                luns[lun.name]["os_type"] = lun["os_type"]
                luns[lun.name]["create_time"] = lun["create_time"]
                luns[lun.name]["sname"] = lun["location"]["logical_unit"]
                luns[lun.name]["vol"] = {lun["location"]["volume"]["name"]: lun["location"]["volume"]["uuid"]}
                luns[lun.name]["size"] = lun["space"]["size"]
                luns[lun.name]["size_human"] = libsan.misc.size.size_bytes_2_size_human(lun["space"]["size"])
                luns[lun.name]["size_netapp"] = lun["space"]["size"]
                luns[lun.name]["serial"] = lun["serial_number"]
                luns[lun.name]["wwid"] = _lun_serial2wwid(lun.serial_number)
                luns[lun.name]["status"] = lun["status"]["state"]
                luns[lun.name]["svm"] = {lun["svm"]["name"]: lun["svm"]["uuid"]}
                luns[lun.name]["enabled"] = lun["enabled"]
                luns[lun.name]["map_infos"] = []
                if lun.name in map_luns and lun.uuid == map_luns[lun.name]["uuid"]:
                    luns[lun.name]["mapped"] = True
                    lun_id = map_luns[lun.name]["lun_id"]
                    igroup_name = map_luns[lun.name]["igroup"]

                    for init in self.get_initiators(lun["svm"]["name"], igroup_name):
                        map_info = {
                            "igroup_name": igroup_name,
                            "t_lun_id": lun_id,
                            "h_wwpn": init,
                        }
                        luns[lun.name]["map_infos"].append(map_info)

        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        self.luns = luns
        return luns

    def get_map_luns(self, lun_name=None):
        luns = {}
        try:
            for mlun in LunMap.get_collection():
                mlun.get()
                luns[mlun.lun.name] = {}
                luns[mlun.lun.name]["name"] = mlun.lun.name
                luns[mlun.lun.name]["uuid"] = mlun.lun.uuid
                luns[mlun.lun.name]["lun_id"] = mlun.logical_unit_number
                luns[mlun.lun.name]["node"] = mlun.lun.node.name
                luns[mlun.lun.name]["svm"] = mlun.svm.name
                luns[mlun.lun.name]["igroup"] = mlun.igroup.name

                if lun_name == mlun.lun.name:
                    return luns[mlun.lun.name]

        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return luns

    def get_interfaces(self):
        all_interface = {}
        try:
            for interface in IpInterface.get_collection():
                interface.get()
                all_interface[interface.name] = {}
                all_interface[interface.name]["name"] = interface.name
                all_interface[interface.name]["uuid"] = interface.uuid

        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
        return all_interface

    def get_fc_interface(
        self,
        svm=None,
        interface_name=None,
    ):
        target_lif_fc_ports = {}
        try:
            for port in FcInterface.get_collection():
                port.get()
                target_lif_fc_ports[port.name] = {}
                target_lif_fc_ports[port.name]["name"] = port.name
                target_lif_fc_ports[port.name]["uuid"] = port.uuid
                target_lif_fc_ports[port.name]["wwpn"] = port.wwpn
                target_lif_fc_ports[port.name]["wwnn"] = port.wwnn
                target_lif_fc_ports[port.name]["state"] = port.state
                target_lif_fc_ports[port.name]["location"] = {
                    "node": port.location.port.node.name,
                    "port": port.location.port.name,
                }
                target_lif_fc_ports[port.name]["data_protocol"] = port.data_protocol
                target_lif_fc_ports[port.name]["svm"] = {port.svm.name: port.svm.uuid}
                target_lif_fc_ports[port.name]["enabled"] = port.enabled

                if interface_name and interface_name == port.name:
                    return target_lif_fc_ports[port.name]

        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))

        if svm:
            for port in list(target_lif_fc_ports.keys()):
                if svm not in target_lif_fc_ports[port]["svm"]:
                    target_lif_fc_ports.pop(port)
        return target_lif_fc_ports

    def mod_lif_fc_port(self, lif_name, enable=True):
        try:
            lif_fc_port = FcInterface.find(name=lif_name)
            lif_fc_port.enabled = enable
            if lif_fc_port.patch(poll=True):
                _print(f"INFO: update the lif fc port {lif_name} to {enable}")
        except NetAppRestError as error:
            _print("FAIL: Error:- %s" % error.http_err_response.http_response.text)
            _print("FAIL: Exception caught :" + str(error))
            return False
        return True

    def lun_create(self, name, size, os_type="linux", wwid=None):
        if wwid or self.wwid:
            self.get_lun_from_wwid(wwid)
        svm = self.svm if self.svm else self.get_sa_conf()["svm"]

        vol = self.vol if self.vol else self.get_sa_conf()["vol"]

        lun_full_path = "/vol/" + vol + "/" + name if "/vol/" + vol not in name else name
        sname = lun_full_path.split("/")[-1]
        _print(f"INFO: will crate new lun with vol {vol}  verver {svm}")
        l_size = libsan.misc.size.size_human_2_size_bytes(size)
        if not l_size:
            _print("FAIL: Could not convert %s to bytes" % size)
            return False
        try:
            vserver = Svm.find(name=svm)
            if not vserver:
                _print("FAIL: Could not find the vserver %s in the array" % svm)
                return False
            volume = Volume.find(name=vol, **{"svm.name": svm})
            if not volume:
                _print("FAIL: Could not find the volume %s in the array" % vol)
                return False
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False

        try:
            lun = Lun.find(name=lun_full_path)
            if lun:
                time.sleep(2)
                _print("INFO: The lun name %s have used" % lun_full_path)
                new_name = libsan.host.linux.time_stamp()
                lun_full_path += new_name
                sname += new_name
                _print("INFO: Set new lun name %s" % lun_full_path)
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False

        new_lun = {
            "comment": sname,
            "location": {"logical_unit": sname, "volume": {"name": vol}},
            "name": lun_full_path,
            "os_type": os_type,
            "space": {"guarantee": {"requested": bool("")}, "size": l_size},
            "svm": {"name": svm},
        }
        print(new_lun)
        lun_object = Lun.from_dict(new_lun)
        try:
            if lun_object.post(poll=True):
                _print("INFO :LUN created  %s created Successfully" % lun_object.name)
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False
        return lun_full_path

    def lun_remove(self, lun_name):
        self.lun_unmap(lun_name)
        try:
            lun = Lun.find(name=lun_name)
            if lun.delete(poll=True):
                _print("INFO :LUN deleted successfully.")
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False
        return True

    def lun_map(
        self,
        lun_full_name,
    ):
        h_wwpns = self.get_h_wwpn()

        svm = self.svm if self.svm else self.get_sa_conf()["svm"]

        if self.igroup:
            igroup_name = self.igroup
        else:
            igroup = self.get_igroups(svm, h_wwpn=h_wwpns)
            if igroup:
                igroup_name = igroup["name"]
            else:
                _print("FAIL: Could not find the igroup for the wwpn %s" % h_wwpns)
                return False

        if not igroup_name:
            _print("FAIL: Don't create igroup for th wwpn %s" % h_wwpns)
            return False

        map_info = {
            "svm": {"name": svm},
            "igroup": {"name": igroup_name},
            "lun": {"name": lun_full_name},
        }
        print("map info %s" % map_info)
        lun_object = LunMap.from_dict(map_info)
        try:
            if lun_object.post(poll=True):
                time.sleep(3)
                _print("INFO :Send lun map request to the array")
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False
        # after send mapped request, but the system don't recognize at once
        lun_info = self.lun_info(lun_full_name)
        if lun_info:
            n = 10
            while n > 0:
                for wwpn in self.get_initiators(svm, igroup_name):
                    host = libsan.host.fc.fc_host_id_of_wwpn(wwpn)
                    libsan.host.linux.run("echo 1 >/sys/class/fc_host/host%s/issue_lip" % host, False, False)
                    time.sleep(5)
                    libsan.host.scsi.rescan_host(host)
                    libsan.host.linux.wait_udev()
                if libsan.host.scsi.scsi_ids_of_wwid(lun_info["wwid"]):
                    break
                n -= 1

        else:
            _print("FAIL: Could not find the lun %s in the array" % lun_full_name)
            return False
        _print("INFO :LUN map Successfully")
        return True

    def lun_unmap(
        self,
        lun_name,
    ):
        map_luns = self.get_map_luns(lun_name)
        if "igroup" in map_luns:
            igroup_name = map_luns["igroup"]
        else:
            all_luns = self.query_all_lun_info(recheck=True)
            igroup_name = all_luns[lun_name]["map_infos"][0]["igroup_name"]
        try:
            lunmap = LunMap.find(lun=lun_name, igroup=igroup_name)
            if lunmap.delete(poll=True):
                _print("INFO: LUN unmap successfully.")
        except NetAppRestError as error:
            _print("FAIL: Exception caught :" + str(error))
            return False
        return True

    def sa_ctrler_t_wwpns(
        self,
        ctrler_ip,
    ):
        svm_ctrler_wwpn = {}
        node_name = self.get_nodes(ctrler_ip)
        svm = self.get_sa_conf()["svm"]
        all_fc_interface = self.get_fc_interface(svm)
        _print(f"DEBUG: vsm {svm} FC interface info {all_fc_interface}")
        _print(f"DEBUG: the IP {ctrler_ip} is from node name {node_name}")
        for lif in all_fc_interface:
            svm_ctrler_wwpn[lif] = []
            if all_fc_interface[lif]["location"]["node"] == node_name["name"]:
                svm_ctrler_wwpn[lif].append(all_fc_interface[lif]["wwpn"])
            else:
                svm_ctrler_wwpn.pop(lif)
        return svm_ctrler_wwpn

    def system_node_power_on(self, node_name):
        """system node power on module"""
        response = CLI().execute("system node power on", body={"node": node_name}, privilege_level="diagnostic")
        time.sleep(3)
        response = CLI().execute("system node power show", status="on")
        _print("DEBUG: %s" % json.dumps(response.http_response.json(), indent=4))

    def system_node_power_off(self, node_name):
        response = CLI().execute("system node power off", body={"node": node_name}, privilege_level="diagnostic")
        time.sleep(3)
        response = CLI().execute("system node power show", status="off")
        _print("DEBUG: %s" % json.dumps(response.http_response.json(), indent=4))

    def sa_ctrler_reboot(self, ctrler_ip):
        # na-fas8080a'
        # node_name = self.get_nodes(ctrler_ip)['name']
        # print(node_name)
        # self.system_node_power_off(node_name)
        # time.sleep(3)
        # self.system_node_power_on(node_name)
        # time.sleep(3)
        # return True

        for lif in self.sa_ctrler_t_wwpns(ctrler_ip):
            self.mod_lif_fc_port(lif, enable=False)
            time.sleep(2)
            self.mod_lif_fc_port(lif, enable=False)
        time.sleep(15)
        for lif in self.sa_ctrler_t_wwpns(ctrler_ip):
            self.mod_lif_fc_port(lif, enable=True)
            time.sleep(2)
            self.mod_lif_fc_port(lif, enable=True)

    def sa_ctrler_check(self, ctrler_ip):
        # na-fas8080b
        # na-fas8080a
        # response = CLI().execute(
        #     "system node power show", status="on")
        # print(response.http_response.json())
        # if int(json.dumps(response.http_response.json()['num_records'])) != 2 :
        #     return False
        # return True

        for lif in self.sa_ctrler_t_wwpns(ctrler_ip):
            if self.get_fc_interface(interface_name=lif)["enabled"]:
                return "online"
            return "offline"
        return None
