# Copyright (C) 2023 Red Hat, Inc.
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

"""nvme.py: Module to manipulate NVME devices."""

__author__ = "Filip Suba"
__copyright__ = "Copyright (c) 2023 Red Hat, Inc. All rights reserved."

from os import listdir
from re import match

from libsan import _print
from libsan.host.cmdline import run
from libsan.host.linux import get_boot_device, get_device_wwid, get_partitions, get_wwid_of_nvme, wipefs
from libsan.host.lvm import pv_query
from libsan.host.md import md_get_storage_dev, md_query
from libsan.host.mp import is_multipathd_running, multipath_query_all
from libsan.misc.size import size_bytes_2_size_human


def is_nvme_device(device: str) -> bool:
    """
    Checks if device is nvme device.
    """
    return bool(match("^nvme[0-9]n[0-9]$", device))


def get_nvme_device_names() -> list:
    """Return list of nvme devices.

    Returns:
    list: Return list of nvme devices
    """
    return [name for name in listdir("/sys/block") if is_nvme_device(name)]


def get_logical_block_size(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/queue/logical_block_size"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_logical_block_size() - Could not get logical block size for nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_physical_block_size(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/queue/physical_block_size"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_physical_block_size() - Could not get physical block size for nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def size_of_device(nvme_device: str) -> int:
    """
    Usage
        size_of_device(device)
    Purpose
        Given an nvme_device name. Eg. nvme0n1
    Parameter
        nvme_device
    Returns
        size in bytes

    """

    logical_block_size = get_logical_block_size(nvme_device)

    if not logical_block_size:
        return 0

    cmd = f"cat /sys/block/{nvme_device}/size"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: size_of_device() - Could not get sector size for device {nvme_device}")
        print(output)
        return 0
    if not output:
        return 0

    sector_size = output

    return int(logical_block_size) * int(sector_size)


def get_nvme_wwid(nvme_device: str) -> str:
    """
    Usage
        get_nvme_wwid(nvme_device)
    Purpose
        Given an NVMe device name. Eg. nvme0n1
    Parameter
        nvme_device   device to get wwid for
    Returns
        wwid:       eg. 360fff19abdd9f5fb943525d45126ca27
    """
    cmd = f"cat /sys/block/{nvme_device}/wwid"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_nvme_wwid() - Could not get wwid of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_nvme_nqn(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/device/subsysnqn"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_nvme_nqn() - Could not get nqn of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_nvme_uuid(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/uuid"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"WARN: get_nvme_uuid() - Could not get uuid of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_nvme_state(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/device/state"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_nvme_subsystem_state() - Could not get state of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_nvme_model(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/device/model"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_nvme_model() - Could not get model of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def get_nvme_transport(nvme_device: str) -> str:
    cmd = f"cat /sys/block/{nvme_device}/device/transport"
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print(f"FAIL: get_nvme_transport() - Could not get transport of nvme device: {nvme_device}")
        print(output)
        return ""
    if not output:
        return ""
    return output


def query_all_nvme_devices(nvme_device="") -> dict:
    """
    Query information of all NVMe devices and return them as a dict
    where NVMe device name is the dict key.
    If an NVMe device is given as argument, return its info
    Parameter:
    \tnvme_device (option):        NVMe device name. eg: 'nvme0n1'
    """
    nvme_devices = {}
    for device in get_nvme_device_names():
        if nvme_device and nvme_device != device:
            # optmization in case we requested specific device, do not query all
            continue
        nvme_wwid = get_wwid_of_nvme(device)
        nvme_uuid = get_nvme_uuid(device)
        nvme_nqn = get_nvme_nqn(device)
        size_bytes = size_of_device(device)
        logical_block_size = get_logical_block_size(device)
        physical_block_size = get_physical_block_size(device)
        nvme_model = get_nvme_model(device)
        state = get_nvme_state(device)
        transport = get_nvme_transport(device)
        nvme_info = {
            "name": device,
            "wwid": nvme_wwid,
            "uuid": nvme_uuid,
            "nqn": nvme_nqn,  # Uses scsi_id to query WWN
            "size": size_bytes,
            "size_human": size_bytes_2_size_human(size_bytes),
            "logical_block_size": logical_block_size,
            "physical_block_size": physical_block_size,
            "state": state,
            "model": nvme_model,
            "transport": transport,
        }
        nvme_devices[device] = nvme_info

    return nvme_devices


def get_free_nvme_devices(
    exclude_boot_device=True,
    exclude_lvm_device=True,
    exclude_mpath_device=True,
    exclude_md_device=True,
    exclude_partitioned_device=True,
    wipe_all=False,
    filter_only=None,
) -> dict:
    all_nvme_devices = query_all_nvme_devices()
    if not all_nvme_devices:
        # could not find any nvme devices
        return {}

    pvs = pv_query()
    md_devices = md_query()
    boot_dev = get_boot_device()
    boot_wwid = None
    # if for some reason we boot from a single device, but this device is part of multipath device
    # the mpath device should be skipped as well
    if boot_dev:
        boot_wwid = get_wwid_of_nvme(boot_dev)

    all_mp_info = None
    if (is_multipathd_running()) and exclude_mpath_device:
        all_mp_info = multipath_query_all()
        if all_mp_info and "by_wwid" not in list(all_mp_info.keys()):
            # Fail querying mpath, setting it back to None
            all_mp_info = None

    chosen_devices = {}
    for nvme_device in list(all_nvme_devices.keys()):
        nvme_info = all_nvme_devices[nvme_device]
        # Skip if mpath device is used for boot
        if boot_wwid == nvme_info["wwid"] and exclude_boot_device:
            _print(f"DEBUG: get_free_nvme_devices() - skip {nvme_info['name']} as it is used for boot")
            continue

        # fixed aws nvme disk wwid is not same with /boot partition
        if nvme_device in boot_dev and exclude_boot_device:
            _print(f"DEBUG: get_free_nvme_devices() - skip {nvme_info['name']} as it is used for boot")
            continue

        # Skip if device is used by multipath
        if all_mp_info and nvme_info["wwid"] in list(all_mp_info["by_wwid"].keys()) and exclude_mpath_device:
            _print(f"DEBUG: get_free_nvme_devices() - skip {nvme_info['name']} as it is used for mpath")
            continue

        # Skip if it is used by Soft RAID
        if md_devices and exclude_md_device:
            used_by_md = False
            for md_dev in md_devices:
                storage_devs = md_get_storage_dev(md_dev)
                if not storage_devs:
                    continue
                for dev in storage_devs:
                    dev_wwid = get_device_wwid(dev)
                    if not dev_wwid:
                        continue
                    if dev_wwid == nvme_info["wwid"]:
                        _print(f"DEBUG: get_free_nvme_devices() - skip {nvme_info['name']} as it is used for md")
                        used_by_md = True
                        continue
            if used_by_md:
                continue

        # Skip if filter_only is specified
        filtered = False
        if filter_only is not None:
            for key in filter_only:
                if nvme_info[key] != filter_only[key]:
                    _print(
                        f"DEBUG: get_free_nvme_devices() - "
                        f"filtered {nvme_info['name']} as {key} is not {filter_only[key]}"
                    )
                    filtered = True
                    continue
        if filtered:
            continue

        if pvs and exclude_lvm_device and "/" + nvme_device in pvs:
            _print(f"DEBUG: get_free_nvme_devices() - skip {nvme_info['name']} as it is used for LVM")
            continue

            # Check partitions
        if get_partitions("/dev/%s" % nvme_info["name"]):
            if exclude_partitioned_device and not wipe_all:
                _print(f"DEBUG: get_free_disks() - skip {nvme_info['name']} as it has partitions")
                continue
            # clear any partitions and filesystems found on disk
            _print(f"DEBUG: Running wipefs on {nvme_info['name']}")
            ret, output = wipefs("/dev/%s" % nvme_info["name"], wipe_all=wipe_all)
            if not ret:
                _print(f"DEBUG: Running wipefs and output {output}")
                continue

        chosen_devices[nvme_info["name"]] = nvme_info

    return chosen_devices
