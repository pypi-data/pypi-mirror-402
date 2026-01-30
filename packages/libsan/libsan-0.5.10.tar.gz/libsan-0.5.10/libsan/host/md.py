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

"""md.py: Module to manipulate MD devices."""

__author__ = "Bruno Goncalves"
__copyright__ = "Copyright (c) 2016 Red Hat, Inc. All rights reserved."

import os.path
import re

from libsan import _print
from libsan.host.cmdline import exists, run


def _mdadm_query(md_device, verbose=False):
    if not exists("mdadm"):
        if verbose:
            _print("INFO: mdadm is not installed")
        return None

    cmd = "mdadm -D /dev/%s" % md_device
    retcode, output = run(cmd, return_output=True, verbose=verbose)
    if retcode != 0:
        _print("FAIL: couldn't query %s" % md_device)
        if verbose:
            print(output)
        return None
    return output


def md_query(verbose=False):
    """Query Soft RAID devices.
    The arguments are:
    \tverbose: Print additional information. Default: False
    Returns:
    \tdict: Return a list of md devices.
    """
    mdstat_file = "/proc/mdstat"

    if not os.path.exists(mdstat_file):
        if verbose:
            _print("INFO: there is no MD device")
        return False

    cmd = "cat %s" % mdstat_file
    retcode, output = run(cmd, return_output=True, verbose=verbose)
    if retcode != 0:
        if verbose:
            _print("INFO: there is no MD device")
        return None

    md_name_regex = r"^(md\d+) :"
    md_devices = []
    for line in output.split("\n"):
        m = re.match(md_name_regex, line)
        if not m:
            continue
        md_devices.append(m.group(1))

    return md_devices


def md_get_info(md_device, verbose=False):
    """Query information of an MD device.
    The arguments are:
    \tmd_device: md device name to get information about
    \tverbose: Print additional information. Default: False
    Returns:
    \tdict: Return a dictionary with details about the md device.
    """
    if not md_device:
        return None

    if md_device not in md_query():
        if verbose:
            _print("INFO: %s is not a MD device" % md_device)
        return None

    output = _mdadm_query(md_device, verbose)
    if not output:
        return None

    md_info = {}
    # Try to get general information about the device
    md_info_regex = r"\s+(.*) : (.*)"
    for line in output.split("\n"):
        info_match = re.match(md_info_regex, line)
        if not info_match:
            continue
        info_name = info_match.group(1).lower()
        info_name = info_name.replace(" ", "_")
        md_info[info_name] = info_match.group(2)

    # Try to get the storage devices linked to the MD
    storage_section = False
    storage_regex = r"\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(.*)\s+(\S+)$"
    for line in output.split("\n"):
        if re.search(r"Number\s+Major\s+Minor\s+RaidDevice\s+State", line):
            storage_section = True
            md_info["storage_devices"] = {}
        if not storage_section:
            continue
        storage_match = re.match(storage_regex, line)
        if not storage_match:
            continue
        storage_info = {}
        storage_info["number"] = storage_match.group(1)
        storage_info["major"] = storage_match.group(2)
        storage_info["minor"] = storage_match.group(3)
        storage_info["raid_device"] = storage_match.group(4)
        storage_info["state"] = storage_match.group(5).strip()
        md_info["storage_devices"][storage_match.group(6)] = storage_info

    return md_info


def md_get_storage_dev(md_device, verbose=False):
    """Get the storage devices of an MD device.
    The arguments are:
    \tmd_device: md device name to get information about
    \tverbose: Print additional information. Default: False
    Returns:
    \tlist: Return a list of storage devices.
    """
    if not md_device:
        return None

    md_info = md_get_info(md_device, verbose)
    if not md_info:
        return None

    if "storage_devices" not in md_info:
        return None
    return md_info["storage_devices"].keys()


def md_stop(md_device, verbose=False):
    """Stop an specific md device.
    The arguments are:
    \tmd_device: md device name to get information about
    \tverbose: Print additional information. Default: False
    Returns:
    \tBoolean:
    \t\tTrue if success
    \t\tFalse in case of failure.
    """
    cmd = "mdadm --stop /dev/%s" % md_device
    retcode, output = run(cmd, return_output=True, verbose=verbose)
    if retcode != 0:
        _print("FAIL: couldn't stop %s" % md_device)
        if verbose:
            print(output)
        return False
    return True


def md_clean(device, verbose=False):
    """clean an specific storage device.
    The arguments are:
    \tdevice: storage device like /dev/sda
    \tverbose: Print additional information. Default: False
    Returns:
    \tBoolean:
    \t\tTrue if success
    \t\tFalse in case of failure.
    """
    cmd = "mdadm --zero-superblock %s" % device
    retcode, output = run(cmd, return_output=True, verbose=verbose)
    if retcode != 0:
        _print("FAIL: couldn't clean %s" % device)
        if verbose:
            print(output)
        return False
    return True


def md_remove(md_device, clean=False, verbose=False):
    """Remove an specific md device.
    The arguments are:
    \tmd_device: md device name to get information about
    \tverbose: Print additional information. Default: False
    Returns:
    \tBoolean:
    \t\tTrue if success
    \t\tFalse in case of failure.
    """
    sto_devices = md_get_storage_dev(md_device)

    if not md_stop(md_device):
        return False

    cmd = "mdadm --remove /dev/%s" % md_device
    retcode, output = run(cmd, return_output=True, verbose=verbose)
    if (
        retcode != 0
        and
        # error opening the device can be ignored
        "mdadm: error opening /dev/%s: No such file or directory" % md_device not in output
    ):
        _print("FAIL: couldn't remove %s" % md_device)
        if verbose:
            print(output)
        return False
    if clean and sto_devices:
        for device in sto_devices:
            if not md_clean(device, verbose):
                return False
    return True
