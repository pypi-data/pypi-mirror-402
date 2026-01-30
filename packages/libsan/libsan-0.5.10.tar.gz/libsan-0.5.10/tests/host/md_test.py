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

from libsan.host import md

mdstat_output = """Personalities : [raid0]
md0 : active raid0 sdb[1] sda[0]
      2093056 blocks super 1.2 512k chunks

unused devices: <none>
"""

mdadm_output = """
/dev/md0:
           Version : 1.2
     Creation Time : Fri Nov 18 04:15:54 2022
        Raid Level : raid0
        Array Size : 2093056 (2044.00 MiB 2143.29 MB)
      Raid Devices : 2
     Total Devices : 2
       Persistence : Superblock is persistent

       Update Time : Fri Nov 18 04:15:54 2022
             State : clean
    Active Devices : 2
   Working Devices : 2
    Failed Devices : 0
     Spare Devices : 0

            Layout : -unknown-
        Chunk Size : 512K

Consistency Policy : none

              Name : 0
              UUID : 05f704a3:70531edf:80b2414a:0de2efad
            Events : 0

    Number   Major   Minor   RaidDevice State
       0       7        0        0      active sync   /dev/sda
       1       7        1        1      inactive      /dev/sdb1
"""

md0_info = {
    "version": "1.2",
    "creation_time": "Fri Nov 18 04:15:54 2022",
    "raid_level": "raid0",
    "array_size": "2093056 (2044.00 MiB 2143.29 MB)",
    "raid_devices": "2",
    "total_devices": "2",
    "persistence": "Superblock is persistent",
    "update_time": "Fri Nov 18 04:15:54 2022",
    "state": "clean",
    "active_devices": "2",
    "working_devices": "2",
    "failed_devices": "0",
    "spare_devices": "0",
    "layout": "-unknown-",
    "chunk_size": "512K",
    "name": "0",
    "uuid": "05f704a3:70531edf:80b2414a:0de2efad",
    "events": "0",
    "storage_devices": {
        "/dev/sda": {"number": "0", "major": "7", "minor": "0", "raid_device": "0", "state": "active sync"},
        "/dev/sdb1": {"number": "1", "major": "7", "minor": "1", "raid_device": "1", "state": "inactive"},
    },
}


class TestMD(unittest.TestCase):
    @patch("libsan.host.md.run")
    def test_md_query(self, run_func):
        run_func.return_value = (0, mdstat_output)

        assert md.md_query() == ["md0"]

        assert run_func.call_count == 1
        run_calls = [call("cat /proc/mdstat", return_output=True, verbose=False)]
        run_func.assert_has_calls(run_calls)

    @patch("libsan.host.md._mdadm_query")
    @patch("libsan.host.md.md_query")
    def test_md_get_info(self, md_query_func, mdadm_query_func):
        md_query_func.return_value = ["md0"]
        mdadm_query_func.return_value = mdadm_output

        assert md.md_get_info("md0", verbose=True) == md0_info

    @patch("libsan.host.md.md_get_info")
    def test_md_get_storage_dev(self, md_get_info_func):
        md_get_info_func.return_value = md0_info

        storage_devs = md.md_get_storage_dev("md0")
        assert "/dev/sda" in storage_devs
        assert "/dev/sdb1" in storage_devs

    @patch("libsan.host.md.run")
    def test_md_stop(self, run_func):
        run_func.return_value = (0, "")
        assert md.md_stop("md0")
        run_calls = [call("mdadm --stop /dev/md0", return_output=True, verbose=False)]
        run_func.assert_has_calls(run_calls)

    @patch("libsan.host.md.run")
    def test_md_clean(self, run_func):
        run_func.return_value = (0, "")
        assert md.md_clean("/dev/sda")
        run_calls = [call("mdadm --zero-superblock /dev/sda", return_output=True, verbose=False)]
        run_func.assert_has_calls(run_calls)

    @patch("libsan.host.md.run")
    @patch("libsan.host.md.md_stop")
    @patch("libsan.host.md.md_get_storage_dev")
    def test_md_remove(self, get_sto_func, md_stop_func, run_func):
        run_func.return_value = (0, "")
        md_stop_func.return_value = True
        get_sto_func.return_value = ["/dev/sda1", "/dev/sdb1"]
        assert md.md_remove("md0", clean=True)
        run_calls = [
            call("mdadm --remove /dev/md0", return_output=True, verbose=False),
            call("mdadm --zero-superblock /dev/sda1", return_output=True, verbose=False),
            call("mdadm --zero-superblock /dev/sdb1", return_output=True, verbose=False),
        ]
        run_func.assert_has_calls(run_calls)
