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
from libsan.host import scsi


def test_query_scsi_hosts():
    hosts = scsi.get_hosts()
    if not hosts:
        print("SKIP: Could not find scsi hosts")
        return

    for host in hosts:
        print("Querying info for host %s" % host)
        info = scsi.query_scsi_host_info(host)
        if not info:
            pytest.fail("Could not query info for host: %s" % host)
        for inf in info:
            print(f"\t{inf}: {info[inf]}")

    assert 1


def test_query_scsi_disks():
    disks = scsi.query_all_scsi_disks()
    if not disks:
        print("SKIP: Could not find scsi disks")
        return

    for disk in disks:
        print("INFO: details for scsi ID: %s" % disk)
        disk_info = disks[disk]
        for info in disk_info:
            print(f"\t{info}: {disk_info[info]}")

    assert 1
