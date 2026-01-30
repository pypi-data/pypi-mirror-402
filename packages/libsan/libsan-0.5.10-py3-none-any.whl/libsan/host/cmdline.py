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


"""cmdline.py: Module to execute a command line."""

__author__ = "Bruno Goncalves"
__copyright__ = "Copyright (c) 2016 Red Hat, Inc. All rights reserved."

import subprocess
import sys
import time
from shutil import which


def run(cmd, return_output=False, verbose=True, force_flush=False, timeout=None):
    """Run a command line specified as cmd.
    The arguments are:
    \tcmd (str):    Command to be executed
    \tverbose:      if we should show command output or not
    \tforce_flush:  if we want to show command output while command is being executed. eg. hba_test run
    \ttimeout (int):timeout for the process in seconds
    \treturn_output (Boolean): Set to True if want output result to be returned as tuple. Default is False
    Returns:
    \tint: Return code of the command executed
    \tstr: As tuple of return code if return_output is set to True"""
    # by default print command output
    if verbose:
        # Append time information to command
        date = 'date "+%Y-%m-%d %H:%M:%S"'
        p = subprocess.Popen(date, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = p.communicate()
        stdout = stdout.decode("ascii", "ignore")
        stdout = stdout.rstrip("\n")
        print(f"INFO: [{stdout}] Running: '{cmd}'...")

    stderr = b""
    if not force_flush:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        try:
            stdout, stderr = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            stdout, stderr = p.communicate()
            print("WARN: Timeout reached")
            p.returncode = 124  # to stay consistent with bash Timeout return code
        sys.stdout.flush()
        sys.stderr.flush()
    else:
        start_time = time.time()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        stdout = b""
        while p.poll() is None:
            new_data = p.stdout.readline()
            stdout += new_data
            if verbose:
                sys.stdout.write(new_data.decode("ascii", "ignore"))
            sys.stdout.flush()
            if timeout and time.time() - start_time > timeout:
                print("WARN: Timeout reached")
                p.kill()
                p.returncode = 124  # to stay consistent with bash Timeout return code
                break

    retcode = p.returncode

    # print "stdout:(" + stdout + ")"
    # print "stderr:(" + stderr + ")"
    output = stdout.decode("ascii", "ignore") + stderr.decode("ascii", "ignore")

    # remove new line from last line
    output = output.rstrip()

    # by default print command output
    # if force_flush we already printed it
    if verbose and not force_flush:
        print(output)

    # print "stderr " + err
    # print "returncode: " + str(retcode)
    if not return_output:
        return retcode
    else:
        return retcode, output


def exists(cmd):
    if not which(str(cmd)):
        return False
    return True
