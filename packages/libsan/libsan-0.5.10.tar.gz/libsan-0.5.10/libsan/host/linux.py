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

"""linux.py: Module to get information from Linux servers."""

__author__ = "Bruno Goncalves"
__copyright__ = "Copyright (c) 2016 Red Hat, Inc. All rights reserved."

import errno
import os.path
import re  # regex
import signal
import subprocess
import sys
import time
from datetime import datetime
from os import listdir
from pathlib import Path

import requests
from configobj import ConfigObj

import libsan.host.mp
import libsan.host.scsi
from libsan import _print
from libsan.host.cmdline import exists, run


def _parse_version(version_string):
    """Parse version string into comparable format.
    Replacement for pkg_resources.parse_version.
    Converts version string like '1.2.3' into list of integers [1, 2, 3].
    Handles non-numeric parts by treating them as strings for comparison.

    :param version_string: Version string (e.g., '1.2.3', '2.10.5')
    :return: List of comparable parts
    """
    parts = []
    for part in str(version_string).split("."):
        try:
            parts.append(int(part))
        except ValueError:
            # If not a number, keep as string for comparison
            parts.append(part)
    return parts


def _compare_versions(version1, version2):
    """Compare two version strings.

    :param version1: First version string
    :param version2: Second version string
    :return: -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    v1_parts = _parse_version(version1)
    v2_parts = _parse_version(version2)

    # Pad the shorter version with zeros
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))

    for p1, p2 in zip(v1_parts, v2_parts):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
    return 0


def hostname():
    ret, host = run("hostname", verbose=False, return_output=True)
    if ret != 0:
        _print("FAIL: hostname() - could not run command")
        print(host)
        return None
    return host


def linux_distribution():
    # Not using platform module, as it doesn't provide needed information
    # on recent python3 versions
    # see: https://bugzilla.redhat.com/show_bug.cgi?id=1920385
    # see: https://bugs.python.org/issue28167
    data = {}
    with open("/etc/os-release", encoding="UTF-8") as f:
        for line in f:
            line = line.strip()
            if line == "":
                continue
            k, v = line.split("=")
            data[k] = v.strip('"')
    return [data["ID"], data["VERSION_ID"]]


def dist_release():
    """Find out the release number of Linux distribution."""
    # We are base on output of lsb_release -r -s' which is shipped by redhat-lsb rpm.
    # ret, release = run("lsb_release --release --short", verbose=False, return_output=True)
    # if ret == 0:
    #    return release
    dist = linux_distribution()
    if not dist:
        _print("FAIL: Could not determine dist release!")
        return None
    return dist[1]


def dist_ver():
    """Check the Linux distribution version."""
    release = dist_release()
    if not release:
        return None
    m = re.match(r"(\d+).\d+", release)
    if m:
        return int(m.group(1))

    # See if it is only digits, in that case return it
    m = re.match(r"(\d+)", release)
    if m:
        return int(m.group(1))

    _print("FAIL: dist_ver() - Invalid release output %s" % release)
    return None


def dist_ver_minor():
    """Check the Linux distribution minor version.
    For example: RHEL-7.4 returns 4
    """
    release = dist_release()
    if not release:
        return None
    m = re.match(r"\d+.(\d+)", release)
    if m:
        return int(m.group(1))

    _print("FAIL: dist_ver_minor() - Release does not seem to have minor version: %s" % release)
    return None


def dist_name():
    """Find out the name of Linux distribution."""
    # We are base on output of lsb_release -r -s' which is shipped by redhat-lsb rpm.
    # ret, release = run("lsb_release --release --short", verbose=False, return_output=True)
    # if ret == 0:
    #    return release
    dist = linux_distribution()
    if not dist:
        _print("FAIL: dist_name() - Could not determine Linux dist name")
        return None

    if dist[0] == "rhel":
        return "RHEL"

    return dist[0]


def service_start(service_name):
    """Start service
    The arguments are:
    \tNone
    Returns:
    \tTrue: Service started
    \tFalse: There was some problem
    """
    cmd = "systemctl start %s" % service_name
    has_systemctl = True

    if not exists("systemctl"):
        has_systemctl = False
    if not has_systemctl:
        cmd = "service %s start" % service_name

    retcode = run(cmd, return_output=False, verbose=True)
    if retcode != 0:
        _print("FAIL: Could not start %s" % service_name)
        if has_systemctl:
            run("systemctl status %s" % service_name)
            run("journalctl -xn")
        return False
    return True


def service_stop(service_name):
    """Stop service
    The arguments are:
    \tName of the service
    Returns:
    \tTrue: Service stopped
    \tFalse: There was some problem
    """
    cmd = "systemctl stop %s" % service_name
    has_systemctl = True

    if not exists("systemctl"):
        has_systemctl = False
    if not has_systemctl:
        cmd = "service %s stop" % service_name

    retcode = run(cmd, return_output=False, verbose=True)
    if retcode != 0:
        _print("FAIL: Could not stop %s" % service_name)
        if has_systemctl:
            run("systemctl status %s" % service_name)
            run("journalctl -xn")
        return False
    return True


def service_restart(service_name):
    """Restart service
    The arguments are:
    \tName of the service
    Returns:
    \tTrue: Service restarted
    \tFalse: There was some problem
    """
    cmd = "systemctl restart %s" % service_name
    has_systemctl = True

    if not exists("systemctl"):
        has_systemctl = False
    if not has_systemctl:
        cmd = "service %s restart" % service_name
    service_timestamp = get_service_timestamp(service_name)
    if service_timestamp is not None:
        timestamp_struct = time.strptime(service_timestamp, "%a %Y-%m-%d %H:%M:%S %Z")
        actual_time = time.localtime()
        if time.mktime(actual_time) - time.mktime(timestamp_struct) < 5:
            print("Waiting 5 seconds before restart.")
            time.sleep(5)
    retcode = run(cmd, return_output=False, verbose=True)
    if retcode != 0:
        _print("FAIL: Could not restart %s" % service_name)
        if has_systemctl:
            run("systemctl status %s" % service_name)
            run("journalctl -xn")
        return False
    return True


def service_enable(service_name, now=False):
    """Enable service
    The arguments are:
    \tName of the service
    Returns:
    \tTrue: Service got enabled
    \tFalse: There was some problem
    """
    cmd = "systemctl enable %s" % service_name
    has_systemctl = True

    if not exists("systemctl"):
        has_systemctl = False
    if not has_systemctl:
        cmd = "chkconfig %s stop" % service_name

    if now and has_systemctl:
        cmd = cmd + " --now"

    retcode = run(cmd, return_output=False, verbose=True)
    if retcode != 0:
        _print("FAIL: Could not enable %s" % service_name)
        if has_systemctl:
            run("systemctl status %s" % service_name)
            run("journalctl -xn")
        return False
    return True


def service_status(service_name, verbose=True):
    """Check service status
    The arguments are:
    \tName of service
    Returns:
    \t 0 - service is running and OK
    \t 1 - service is dead and /run pid file exists
    \t 2 - service is dead and /lock lock file exists
    \t 3 - service is not running
    \t 4 - service could not be found.
    \t False - something went wrong.
    """
    cmd = "systemctl status %s" % service_name
    has_systemctl = True

    if not exists("systemctl"):
        has_systemctl = False
    if not has_systemctl:
        cmd = "service %s status" % service_name

    retcode = run(cmd, return_output=False, verbose=verbose)
    if retcode == 0:
        _print("INFO: Service %s is running." % service_name)
    elif retcode == 1:
        _print("INFO: Service %s is dead and /run pid file exists." % service_name)
    elif retcode == 2:
        _print("INFO: Service %s is dead and /lock lock file exists." % service_name)
    elif retcode == 3:
        _print("INFO: Service %s is not running." % service_name)
    elif retcode == 4:
        _print("INFO: Service %s could not be found." % service_name)
    else:
        _print(f"INFO: Service {service_name} returned unknown code {retcode}.")
    return retcode


def is_service_running(service_name):
    """Check if service is running
    The arguments are:
    \tName of service
    Returns:
    \t True: service is running
    \t False: service is not running
    """

    return service_status(service_name, verbose=False) == 0


def os_arch():
    ret, arch = run("uname -m", verbose=False, return_output=True)
    if ret != 0:
        _print("FAIL: could not get OS arch")
        return None

    return arch


def is_installed(pack, verbose=False):
    """Checks if package is installed"""
    ret, ver = run("rpm -q %s" % pack, verbose=False, return_output=True)
    if ret == 0:
        if verbose:
            print(f"INFO: {pack} is installed ({ver})")
        return True

    if verbose:
        print("INFO: %s is not installed " % pack)
    return False


def install_package(pack, check=True, verbose=True):
    """Install a package "pack" via `yum|dnf install -y`"""
    # Check if package is already installed
    if check and is_installed(pack, verbose):
        return True

    packmngr = "yum"
    if is_installed("dnf"):
        packmngr = "dnf"

    if run(f"{packmngr} install -y {pack}") != 0:
        msg = "FAIL: Could not install %s" % pack
        _print(msg)
        return False

    if verbose:
        print("INFO: %s was successfully installed" % pack)
    return True


def package_version(pkg):
    """Get the version of specific package"""
    if not pkg:
        _print("FAIL: package_version requires package name as parameter")
        return None

    release = dist_name().lower()
    if not release:
        _print("FAIL: package_version() - Couldn't get release")
        return None
    if exists("rpm"):
        ret, output = run("rpm -qa --qf='%%{version}.%%{release}' %s" % pkg, return_output=True, verbose=False)
        if ret != 0:
            _print("FAIL: Could not get version for package: %s" % pkg)
            print(output)
            return None
        return output

    _print("FAIL: package_version() - Unsupported release: %s" % release)
    return None


def compare_version(package, version, release, equal=True):
    """:param package: package name
    :param version: package version
    :param release: package release
    :param equal: return value if packaged are equal version (default 'True')
    :return: Returns 'True' if installed version is newer or equal than asked, 'False' if older
             Return 'None' if the package is not installed (not found)
    """
    pkg = package_version(package)
    if pkg is None:
        return None
    if any(True for x in pkg if not isinstance(x, int)):
        # cut ending of package name containing string, _compare_versions() works better with clean numeric versions
        pack = []
        for p in pkg[:].split("."):
            try:
                int(p)
            except ValueError:
                break
            pack.append(p)
        pkg = ".".join(pack)

    requested_version = version + "." + release
    comparison = _compare_versions(requested_version, pkg)

    if equal:
        return comparison <= 0  # requested <= installed
    return comparison < 0  # requested < installed


def wait_udev(sleeptime=15):
    """Wait udev to finish. Often used after scsi rescan."""
    _print("INFO: Waiting udev to finish storage scan")
    # For example, on RHEL 7 scsi_wait_scan module is deprecated
    if run("modinfo scsi_wait_scan", verbose=False) == 0:
        run("modprobe -q scsi_wait_scan")
        run("modprobe -r -q scsi_wait_scan")

    run("udevadm settle")
    sleep(sleeptime)

    return True


def get_all_loaded_modules():
    """Check /proc/modules and return a list of all modules that are loaded"""
    cmd = 'cat /proc/modules | cut -d " " -f 1'
    ret, output = run(cmd, return_output=True, verbose=False)
    if ret != 0:
        _print("FAIL: load_module() - Could not execute: %s" % cmd)
        print(output)
        return None

    modules = output.split("\n")
    return modules


def load_module(module):
    """Run modprobe using module with parameters given as input
    Parameters:
    \tmodule:       module name and it's parameters
    """
    if not module:
        _print("FAIL: load_module() - requires module parameter")
        return False
    cmd = "modprobe %s" % module
    if run(cmd) != 0:
        _print("FAIL: load_module() - Could not execute: %s" % module)
        return False
    return True


def unload_module(module_name, remove_dependent=False):
    """Run rmmod to unload module
    Parameters:
    \tmodule_name:       module name
    """
    if not module_name:
        _print("FAIL: unload_module() - requires module_name parameter")
        return False
    cmd = f"modprobe -r {module_name}"

    if remove_dependent:
        dep_modules = get_dependent_modules(module_name)
        if dep_modules:  # print info only if there are any modules to remove
            _print(f"INFO: Removing modules dependent on {module_name}")
            for module in dep_modules:
                if not unload_module(module, remove_dependent=remove_dependent):
                    _print("FAIL: unload_module() - Could not unload dependent modules")
                    return False

    if run(cmd) != 0:
        _print(f"FAIL: unload_module() - Could not unload: {module_name}")
        return False

    return True


def get_dependent_modules(module_name):
    """Returns list of modules that loaded this module as a dependency
    Useful when removing parent modules (error "Module is in use by: ")
    Parameters:
    \tmodule_name:      module_name
    """
    if not module_name:
        _print("FAIL: get_dependent_modules() - requires module_name parameter")
        return None
    cmd = f'cat /proc/modules | grep -Ew "^{module_name}" | cut -d \' \' -f 4 | tr "," " "'
    ret, dependent_modules = run(cmd, return_output=True, verbose=False)
    if dependent_modules == "-":
        return []  # No dependent modules found
    if ret != 0:
        _print("FAIL: get_dependent_modules() - failed to get a list of modules")
        return None
    return dependent_modules.split()


def is_module_loaded(module_name):
    """Check if given module is loaded
    Parameters:
    \tmodule_name:      module_name
    """
    if module_name in get_all_loaded_modules():
        return True
    return False


def sleep(duration):
    """It basically call sys.sleep, but as stdout and stderr can be buffered
    We flush them before sleep
    """
    sys.stdout.flush()
    sys.stderr.flush()
    time.sleep(duration)
    return


def is_mounted(device=None, mountpoint=None):
    """Check if mountpoint is already mounted"""
    if device and run("mount | grep %s" % device, verbose=False) != 0:
        return False
    if mountpoint and run("mount | grep %s" % mountpoint, verbose=False) != 0:
        return False
    return True


def mount(device=None, mountpoint=None, fs=None, options=None):
    cmd = "mount"
    if fs:
        cmd += " -t %s" % fs
    if options:
        cmd += " -o %s" % options
    if device:
        cmd += " %s" % device
    if mountpoint:
        cmd += " %s" % mountpoint
    if run(cmd) != 0:
        _print("FAIL: Could not mount partition")
        return False

    return True


def umount(device=None, mountpoint=None):
    cmd = "umount"
    if device:
        cmd += " %s" % device
        if not is_mounted(device):
            # Device is not mounted
            return True

    if mountpoint:
        cmd += " %s" % mountpoint
        if not is_mounted(mountpoint=mountpoint):
            # Device is not mounted
            return True

    if run(cmd) != 0:
        _print("FAIL: Could not umount partition")
        return False

    return True


def get_default_fs():
    """Return the default root FileSystem for this release"""
    path = "/"
    # We need to check different path on image mode, because "/" is only an overlay
    alt_path = "/sysroot"
    _, df_output = run('df --output="target","fstype"', verbose=False, return_output=True)
    filesystems = [line.split() for line in df_output.splitlines() if not line.startswith("Mounted")]
    for fs in filesystems:
        if (fs[0] == path and fs[1] != "overlay") or fs[0] == alt_path:
            return fs[1]
    return "xfs"


def run_cmd_background(cmd):
    """Run Command on background
    Returns:
        subprocess.
            PID is on process.pid
            Exit code is on process.returncode (after run process.communicate())
        Wait for process to finish
            while process.poll() is None:
                linux.sleep(1)
        Get stdout and stderr
            (stdout, stderr) = process.communicate()
    """
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if not process:
        _print("FAIL: Could not run '%s' on background" % cmd)
        return None
    _print("INFO: running %s on background. PID is %d" % (cmd, process.pid))
    return process


def kill_pid(pid):
    os.kill(pid, signal.SIGTERM)
    sleep(1)
    if check_pid(pid):
        os.kill(pid, signal.SIGKILL)
        sleep(1)
        if check_pid(pid):
            return False
    return True


def kill_all(process_name):
    ret = run("killall %s" % process_name, verbose=None)
    # Wait few seconds for process to finish
    sleep(3)
    return ret


def check_pid(pid):
    """Check there is a process running with this PID"""
    # try:
    # #0 is the signal, it does not kill the process
    # os.kill(int(pid), 0)
    # except OSError:
    # return False
    # else:
    # return True
    try:
        return os.waitpid(pid, os.WNOHANG) == (0, 0)
    except OSError as e:
        if e.errno != errno.ECHILD:
            raise


def time_stamp(in_seconds=False):
    now = datetime.now()

    # ts = "%s%s%s%s%s%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    ts = now.strftime("%Y%m%d%H%M%S")
    if in_seconds:
        ts = now.strftime("%s")
    return ts


def kernel_command_line():
    """Return the kernel command line used to boot"""
    retcode, output = run("cat /proc/cmdline", return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: could not get kernel command line")
        print(output)
        return None
    return output


def kernel_version():
    """Usage
        kernel_version()
    Purpose
        Check out running kernel version. The same as output of `uname -r`
    Parameter
        N/A
    Returns
        kernel_version
    """
    retcode, output = run("uname -r", return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: could not get kernel version")
        print(output)
        return None
    # remove arch detail and kernel type
    output = re.sub(r"\.%s.*" % os_arch(), "", output)
    return output


def kernel_type():
    """Usage
        kernel_type()
    Purpose
        Check the kernel type. Current we support detection of these types:
            1. default kernel.
            2. debug kernel.
            3. rt kernel.
    Parameter
        N/A
    Returns
        kernel_type        # 'debug|rt|default'
    """
    retcode, version = run("uname -r", return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: kernel_type() - could not get kernel version")
        print(version)
        return None

    if re.search(r"debug$", version):
        return "debug"

    if re.search(r"rt$", version):
        return "rt"

    return "default"


def kmem_leak_start():
    """Usage
        kmem_leak_start()
    Purpose
        Start and clear kernel memory leak detection.
    Parameter
        N/A
    Returns
        True
          or
        False       # not debug kernel or failure found
    """
    k_type = kernel_type()

    if not k_type or k_type != "debug":
        _print("WARN: Not debug kernel, will not enable kernel memory leak check")
        return False

    arch = os_arch()
    if arch == "i386" or arch == "i686":
        print("INFO: Not enabling kmemleak on 32 bits server.")
        return False

    k_commandline = kernel_command_line()
    if not re.search("kmemleak=on", k_commandline):
        _print("WARN: kmem_leak_start(): need 'kmemleak=on' kernel_option to enable kernel memory leak detection")

    check_debugfs_mount_cmd = 'mount | grep "/sys/kernel/debug type debugfs"'
    retcode = run(check_debugfs_mount_cmd, verbose=False)
    if retcode != 0:
        # debugfs is not mounted
        mount_debugfs_cli_cmd = "mount -t debugfs nodev /sys/kernel/debug"
        run(mount_debugfs_cli_cmd, verbose=True)
        check_debugfs_mount_cmd = 'mount | grep "/sys/kernel/debug type debugfs"'
        retcode, output = run(check_debugfs_mount_cmd, return_output=True, verbose=False)
        if retcode != 0:
            _print("WARN: Failed to mount debugfs to /sys/kernel/debug")
            print(output)
            return False

    # enable kmemleak and clear
    _print("INFO: Begin kernel memory leak check")
    if run("echo scan=on > /sys/kernel/debug/kmemleak") != 0:
        return False
    if run("echo stack=on > /sys/kernel/debug/kmemleak") != 0:
        return False
    if run("echo clear > /sys/kernel/debug/kmemleak") != 0:
        return False
    return True


def kmem_leak_check():
    """Usage
        kmem_leak_check()
    Purpose
        Read out kernel memory leak check log and then clear it up.
    Parameter
        N/A
    Returns
        kmemleak_log
          or
        None       # when file '/sys/kernel/debug/kmemleak' not exists
                  # or no leak found
    """
    sysfs_kmemleak = "/sys/kernel/debug/kmemleak"
    if not os.path.isfile(sysfs_kmemleak):
        return None

    with open(sysfs_kmemleak) as f:
        if not f:
            _print("FAIL: Could not read %s" % sysfs_kmemleak)
            return None
        kmemleak_log = f.read()

    if kmemleak_log:
        _print("WARN: Found kernel memory leak:\n%s" % kmemleak_log)
        _print("INFO: Clearing memory leak for next check")
        run("echo 'clear' > %s" % sysfs_kmemleak)
        return kmemleak_log

    _print("INFO: No kernel memory leak found")
    return None


def kmem_leak_disable():
    """Usage
        kmem_leak_disable()
    Purpose
        Disable kmemleak by 'scan=off' and 'stack=off' to
        '/sys/kernel/debug/kmemleak'.
    Parameter
        N/A
    Returns
        True           # disabled or not enabled yet
          or
        False       # failed to run 'echo' command
    """
    sysfs_kmemleak = "/sys/kernel/debug/kmemleak"
    if not os.path.isfile(sysfs_kmemleak):
        return True

    _print("INFO: kmem_leak_disable(): Disabling kernel memory leak detection")
    ok1, ok1_output = run("echo scan=off > %s" % sysfs_kmemleak, return_output=True)
    ok2, ok2_output = run("echo stack=off > %s" % sysfs_kmemleak, return_output=True)
    if ok1 != 0 or ok2 != 0:
        print("FAIL: kmem_leak_disable(): Failed to disable kernel memory leak detection")
        print(ok1_output)
        print(ok2_output)
        return False

    _print("INFO: kmem_leak_disable(): Kernel memory leak detection disabled")
    return True


def query_os_info():
    """query_os_info()
    Purpose
        Query OS informations and set a reference below:
        os_info = {
            dist_name       = dist_name,
            dist_release    = dist_release,
            kernel_version  = kernel_version,
            os_arch         = os_arch,
            arch            = os_arch,
            pkg_arch        = pkg_arch, #as, for example, rpm on i386 could return different arch then uname -m

        }
    Parameter
        N/A
    Returns
        os_info_dict
            or
        None       # got error
    """

    os_info_dict = {
        "dist_name": dist_name(),
        "dist_version": dist_ver(),
        "dist_release": dist_release(),
        "os_arch": os_arch(),
        "arch": os_arch(),
        "pkg_arch": os_arch(),
        "kernel_version": kernel_version(),
        "kernel_type": kernel_type(),
    }
    return os_info_dict


def get_driver_info(driver):
    if not driver:
        _print("FAIL: get_driver_info() - requires driver parameter")
        return None

    sys_fs_path = "/sys/module"
    if not os.path.isdir(sys_fs_path):
        _print("FAIL: get_driver_info() - %s is not a valid directory" % sys_fs_path)
        return None

    sysfs_driver_folder = f"{sys_fs_path}/{driver}"
    if not os.path.isdir(sysfs_driver_folder):
        _print("FAIL: get_driver_info() - module %s is not loaded" % driver)
        return None

    driver_info = {}
    infos = ["srcversion", "version", "taint"]
    for info in infos:
        info_path = f"{sysfs_driver_folder}/{info}"
        if not os.path.isfile(info_path):
            continue
        _, output = run(f"cat {sysfs_driver_folder}/{info}", return_output=True, verbose=False)
        driver_info[info] = output

    sys_driver_parameter = "%s/parameters/" % sysfs_driver_folder
    if os.path.isdir(sys_driver_parameter):
        # Need to add driver parameters
        param_files = [
            f for f in listdir(sys_driver_parameter) if os.path.isfile(os.path.join(sys_driver_parameter, f))
        ]
        for param in param_files:
            _, output = run(f"cat {sys_driver_parameter}/{param}", return_output=True, verbose=False)
            if "parameters" not in driver_info:
                driver_info["parameters"] = {}
            driver_info["parameters"][param] = output
    return driver_info


def mkdir(new_dir):
    if os.path.isdir(new_dir):
        _print("INFO: %s already exist" % new_dir)
        return True
    cmd = "mkdir -p %s" % new_dir
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: could create directory %s" % new_dir)
        print(output)
        return False
    return True


def rmdir(dir_name):
    """Remove directory and all content from it"""
    if not os.path.isdir(dir_name):
        _print("INFO: %s does not exist" % dir_name)
        return True
    cmd = "rm -rf %s" % dir_name
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: could remove directory %s" % dir_name)
        print(output)
        return False
    return True


def mkfs(device_name, fs_type, force=False):
    """Create a Filesystem on device"""
    if not device_name or not fs_type:
        _print("INFO: mkfs() requires device_name and fs_type")
        return False

    force_option = "-F"
    if fs_type == "xfs":
        force_option = "-f"

    cmd = "mkfs.%s " % fs_type
    if force:
        cmd += "%s " % force_option
    cmd += device_name
    retcode, output = run(cmd, return_output=True, verbose=True)
    if retcode != 0:
        _print(f"FAIL: could create filesystem {fs_type} on {device_name}")
        print(output)
        return False
    return True


def wipefs(device_name, wipe_all=False, offset="0x", return_json=False, return_sigs=False):
    cmd = f"wipefs {device_name} "
    if wipe_all:
        cmd += "-a "
    if offset != "0x":
        cmd += f"-o {offset} "
    if return_json:
        cmd += "-J "
    if return_sigs:
        # default output format: DEVICE OFFSET TYPE UUID LABEL
        cmd += "-i "
    retcode, output = run(cmd, return_output=True)
    if retcode != 0:
        _print("FAIL: Wipefs returned following error:")
        print(output)
        return False, output
    return True, output


def sync(directory=None):
    cmd = "sync"
    if directory:
        cmd += " %s" % directory
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: could not sync")
        print(output)
        return False
    return True


def get_free_space(path):
    """Get free space of a path.
    Path could be:
    \t/dev/sda
    \t/root
    \t./
    """
    if not path:
        return None

    cmd = "df -B 1 %s" % path
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: get_free_space() - could not run %s" % cmd)
        print(output)
        return None
    fs_list = output.split("\n")
    # delete the header info
    del fs_list[0]

    if len(fs_list) > 1:
        # Could be the information was too long and splited in lines
        tmp_info = "".join(fs_list)
        fs_list[0] = tmp_info

    # expected order
    # Filesystem    1B-blocks       Used   Available Use% Mounted on
    free_space_regex = re.compile(r"\S+\s+\d+\s+\d+\s+(\d+)")
    m = free_space_regex.search(fs_list[0])
    if m:
        return int(m.group(1))
    return None


def get_block_device_name(device):
    """Returns kernel name from block device
    eg. lvm1 from /dev/mapper/lvm1
    """
    if not device.startswith("/dev/"):
        device = get_full_path(device)
    if not device:
        _print("FAIL: get_block_device_name - unknown device")
    cmd = "lsblk -ndlo NAME %s" % device
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: run %s" % cmd)
        print(output)
        return None
    return output


def get_full_path(device_name):
    """Returns full block device path, eg. from device: /dev/mapper/device"""
    cmds = [
        "lsblk -pnalo NAME  | grep %s -m1" % device_name,  # should be more robust
        "find /dev/ -name %s" % device_name,
    ]  # older OS(rhel-6), will fail with partitions

    for cmd in cmds:
        retcode, output = run(cmd, return_output=True, verbose=False)
        if retcode == 0 and output != "":
            return output

    _print("FAIL: get_full_path() - %s" % device_name)
    return None


def get_parent_device(child_device, only_direct=False):
    """Returns block device's parent device: eg. sda, nvme0n1
    child_device: eg. /dev/sda2, nvme0n1p1, /dev/mapper/device
    only_direct: returns only the direct parent. eg. lvm -> sda3, not sda
    """
    if not child_device.startswith("/dev/"):
        child_device = get_full_path(child_device)
    if not child_device:  # get_full_path would return None if device does not exist
        _print("FAIL: get_parent_device - unknown child_device '%s'" % child_device)
    cmd = "lsblk -nsl %s -o KNAME | tail -n 1" % child_device
    if only_direct:
        cmd = "lsblk -nsl %s -o KNAME | sed -n 2p" % child_device  # if no parent, returns nothing
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: run %s" % cmd)
        print(output)
        return None
    if output == "" or output == child_device:
        _print("WARN: get_parent_device - device has no parent")
        return None
    return output


def get_udev_property(device_name, property_key):
    """Given an /dev device name, returns specified property using udevadm
    :param device_name: eg. 'sda', 'mpatha', 'dm-0', 'nvme0n1', 'sr0', ...
    :param property_key: eg. 'ID_SERIAL', 'DM_WWN', 'ID_PATH', ...
    :return property_value: eg. for ID_SERIAL: '360fff19abdd9f5fb943525d45126ca27'
    """
    if not device_name:
        _print("WARN: get_udev_property() - requires device_name parameter")
        return None

    # Converts for example mpatha to /dev/mapper/mpatha or sda to /dev/sda
    device = libsan.host.linux.get_full_path(device_name)
    if not device:
        _print("FAIL: get_udev_property - unknown device_name '%s'" % device_name)

    # Trying to catch wrong key name when dm-multipath is used.
    if libsan.host.mp.is_mpath_device(device_name, print_fail=False):  # noqa: SIM102
        if property_key.startswith("ID_") and not property_key.startswith("ID_FS_"):
            property_key = property_key.replace("ID_", "DM_")

    ret, property_value = run(
        f"udevadm info -q property --name={device} | grep {property_key}= | cut -d = -f 2",
        return_output=True,
        verbose=False,
    )
    if ret:
        _print("WARN: Could not get udevadm info of device '%s'" % device)
        return None
    if not property_value:
        _print(f"WARN: Could not find property '{property_key}' in udevadm info of device '{device}'")
        return None

    return property_value


def get_boot_device(parent_device=False, full_path=False):
    """Returns boot device, eg. 'sda1'
    parent_device, eg. 'sda'
    full_path, eg. '/dev/sda1'
    """
    boot_mount = "/boot"
    root_mount = "/"
    # get boot device
    cmd = "mount | grep ' %s ' | cut -d ' ' -f 1" % boot_mount
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: run %s" % cmd)
        print(output)
        return None
    boot_device = output
    # get root device
    cmd = "mount | grep ' %s ' | cut -d ' ' -f 1" % root_mount
    retcode, output = run(cmd, return_output=True, verbose=False)
    if retcode != 0:
        _print("FAIL: run %s" % cmd)
        print(output)
        return None
    root_device = output

    if not boot_device and not root_device:
        _print("FAIL: Could not find '/boot' and '/' mounted!")
        return None
    if not boot_device:
        # /boot is not mounted on openstack virtual machines
        _print("INFO: Could not find /boot mounted... Assuming this is a virtual machine")
        boot_device = root_device
    if boot_device == "overlay":
        _print("INFO: / mounted on overlay device. Assuming running in a container")
        return None

    if parent_device:
        boot_device = get_parent_device(boot_device)
    if full_path:
        return get_full_path(boot_device)
    return get_block_device_name(boot_device)


def is_dm_device(device_name):
    """Checks if device is mapped by device-mapper.
    :param device_name: eg. 'sda', 'mpatha', ...
    :return: True/False
    """
    # Converts for example mpatha to /dev/mapper/mpatha or sda to /dev/sda
    device = libsan.host.linux.get_full_path(device_name)
    if not device:
        _print("FAIL: is_dm_device - unknown device_name '%s'" % device_name)
        return False
    ret, name = run("udevadm info -q name --name=%s" % device, return_output=True)
    if ret:
        _print("FAIL: Could not get udevadm info for device '%s'" % device)
        return False
    if not name:
        _print("FAIL: Could not find udev name for '%s'" % device)
        return False

    if name.startswith("dm"):
        return True

    return False


def is_nvme_device(device):
    """Checks if device is nvme device."""
    return bool(re.match("^nvme[0-9]n[0-9]$", device))


def get_wwid_of_nvme(device):
    """Reads WWID from udev ID_WWN."""
    return get_udev_property(device, property_key="ID_WWN")


def get_device_wwid(device):
    """Given a SCSI, NVMe or multipath device, returns its WWID"""

    if device.startswith("vd"):
        print("INFO: %s: Presuming virtual disk does not have wwid." % device)
        return None

    serial = get_udev_property(device_name=device, property_key="ID_SERIAL")
    if not serial and is_dm_device(device):  # RHEL-6 workaround
        dm_uuid = get_udev_property(device_name=device, property_key="DM_UUID")
        serial = dm_uuid.replace("mpath-", "")
    if not serial:
        _print("INFO: get_device_wwid() - Could not find WWID for %s" % device)
        return None

    return serial


def remove_device_wwid(wwid):
    if not wwid:
        _print("FAIL: remove_device_wwid() - requires wwid as parameter")
        return False

    mpath_wwid = libsan.host.mp.mpath_name_of_wwid(wwid)
    if mpath_wwid:
        libsan.host.mp.remove_mpath(mpath_wwid)

    scsi_ids_wwid = libsan.host.scsi.scsi_ids_of_wwid(wwid)
    if scsi_ids_wwid:
        for scsi_id in scsi_ids_wwid:
            scsi_name = libsan.host.scsi.get_scsi_disk_name(scsi_id)
            if not scsi_name:
                continue
            _print("INFO: detaching SCSI disk %s" % scsi_name)
            libsan.host.scsi.delete_disk(scsi_name)
    return True


def clear_dmesg():
    cmd = "dmesg --clear"
    if dist_ver() < 7:
        cmd = "dmesg -c"
    run(cmd, verbose=False)
    return True


def get_regex_pci_id():
    regex_pci_id = r"(?:([0-0a-f]{4}):){0,1}"  # domain id (optional)
    regex_pci_id += r"([0-9a-f]{2})"  # bus id
    regex_pci_id += r":"
    regex_pci_id += r"([0-9a-f]{2})"  # slot id
    regex_pci_id += r"\."
    regex_pci_id += r"(\d+)"  # function id
    return regex_pci_id


def get_partitions(device):
    """Return a list of all parition numbers from the device"""
    if not device:
        _print("WARN: get_partitions() - requires device as parameter")
        return None

    cmd = "parted -s %s print" % device
    ret, output = run(cmd, verbose=False, return_output=True)
    if ret != 0:
        # _print("FAIL: get_partitions() - Could not read partition information from %s" % device)
        # print output
        return None

    lines = output.split("\n")
    if not lines:
        return None

    partition_regex = re.compile(r"\s(\d+)\s+\S+")
    partitions = []
    found_header = False
    for line in lines:
        if line.startswith("Number"):
            found_header = True
            continue
        if found_header:
            m = partition_regex.match(line)
            if m:
                partitions.append(m.group(1))

    return partitions


def delete_partition(device, partition):
    """Delete specific partition from the device"""
    if not device or not partition:
        _print("FAIL: delete_partition() - requires device and partition as argument")
        return False

    cmd = f"parted -s {device} rm {partition}"
    ret, output = run(cmd, verbose=False, return_output=True)
    if ret != 0:
        _print("FAIL: delete_partition() - Could not delete partition %d from %s" % (partition, device))
        print(output)
        return False

    return True


def add_repo(name, address, metalink=False):
    """Adds yum repository to /etc/yum.repos.d/NAME.repo"""
    repo = "/etc/yum.repos.d/%s.repo" % name.lower()
    if os.path.isfile(repo):
        _print("INFO: Repo %s already exists." % repo)
        return True

    url = "baseurl=%s\n" % address
    if metalink:
        url = "metalink=%s\n" % address

    with open(repo, "w", encoding="UTF-8") as _file:
        _file.write(
            "[%s]\n" % name + "name=%s\n" % name + url + "enabled=1\n" + "gpgcheck=0\n" + "skip_if_unavailable=1\n"
        )

    return True


def download_repo_file(url, name=None, overwrite=True):
    """Downloads .repo file to /etc.repos.d/"""
    if not url:
        print("FAIL: repo file url argument required")
        return False
    if not name:
        name = url.split("/")[-1]
    if name[-5:] != ".repo":
        name = "{}{}".format(name, ".repo")
    path = "/etc/yum.repos.d/%s" % name

    if os.path.isfile(path):
        if overwrite is False:
            print("WARN: %s exits, skipping repo file download" % name)
            return True
        else:
            print("WARN: %s exits, overwriting .repo file" % name)
    try:
        r = requests.get(url, timeout=10)
    except requests.exceptions.RequestException as e:
        print("FAIL: Unable to reach repo url: %s" % e)
        return False
    try:
        with open(path, "wb") as f:
            f.write(r.content)
    except OSError:
        print("FAIL: Unable to write %s file" % path)
        return False

    return True


def del_repo(name):
    """Removes .repo file"""
    repo = "/etc/yum.repos.d/%s.repo" % name.lower()
    if os.path.isfile(repo) and os.remove(repo) is not None:
        _print("WARN: Removing repository %s failed." % repo)
        return False
    return True


def check_repo(name, check_if_enabled=True):
    """Checks if repository works and is enabled"""
    if not name:
        print("FAIL: repo name argument required")
        return False

    cmd = "yum repoinfo %s | grep -i status" % name  # yum=dnf alias works here
    ret, out = run(cmd, return_output=True)
    if ret != 0:
        print("%s repo is not present" % name)
        return False
    if check_if_enabled and "enabled" not in out:
        print("%s repo is not enabled" % name)
        return False

    return True


def is_docker():
    """Check if we are running inside docker container"""
    try:
        proc_current = Path("/proc/1/attr/current").read_text()
        # Check for unconfined, which can be found in gitlab ci
        if "container_t" in proc_current or "unconfined" in proc_current:
            return True
        if "docker" in Path("/proc/self/cgroup").read_text():
            return True
    except PermissionError:
        return True
    return False


def get_memory(units="m", total=False):
    """Returns data from 'free' as a dict."""
    possible_units = "b bytes k kilo m mega  g giga tera peta".split()
    if units not in possible_units:
        _print("FAIL: 'units' must be one of %s" % [str(x) for x in possible_units])
        return None

    memory = {}
    columns = []

    if len(units) > 1:
        units = "-" + units
    cmd = "free -%s" % units
    if total:
        cmd += " -t"
    ret, mem = run(cmd=cmd, return_output=True)
    if ret != 0:
        _print("FAIL: Running '%s' failed." % cmd)
        return None

    for row, m in enumerate(mem.splitlines()):
        if row == 0:
            columns = [c.strip() for c in m.split()]
            continue
        m = [x.strip() for x in m.split()]
        key = m.pop(0)[:-1].lower()
        memory[key] = {}
        for i, value in enumerate(m):
            memory[key][columns[i]] = int(value)

    return memory


def get_service_timestamp(service_name):
    """Returns active enter timestamp of a service.
    :param service_name: Name of the service
    :return:
    Time in format: a YYYY-MM-DD hh:mm:ss Z
    None: systemctl is not installed or timestamp does not exist
    """
    if not exists("systemctl"):
        cmd = "systemctl show %s --property=ActiveEnterTimestamp" % service_name
        ret, data = run(cmd, return_output=True)
        if ret == 0:
            timestamp = data.split("=")
            if timestamp[1] != "":
                return timestamp[1]
            return None
        _print("WARN: Could not get active enter timestamp of service: %s" % service_name)
    return None


def get_system_logs(
    length=None,
    reverse=False,
    kernel_only=False,
    since=None,
    grep=None,
    options=None,
    verbose=False,
    return_output=True,
):
    """Gets system logs using journalctl.
    :param length: (int) Get last $length messages.
    :param reverse: (bool) Get logs in reverse.
    :param kernel_only: (bool) Get only kernel messages.
    :param since: (string) Get messages since some time, can you '+' and '-' prefix.
    :param grep: (string) String to filter messages using 'grep'.
    :param options: (list of strings) Any other possible options with its value as a string.
    :param verbose: (bool) Print the journal when getting it.
    :param return_output (bool) Should the function return only retcode or also the output
    :return: retcode / (retcode, data)
    """
    cmd = "journalctl"
    if kernel_only:
        cmd += " -k"
    if length:
        cmd += " -n %s" % length
    if reverse:
        cmd += " -r"
    if since:
        # since can be used with '+' and '-', see man journalctl
        cmd += " -S %s" % since
    if options:
        cmd += " " + " ".join(options)

    if grep:
        cmd += " | grep '%s'" % grep

    ret, journal = run(cmd, return_output=return_output, verbose=verbose)
    if ret:
        _print(f"FAIL: cmd '{cmd}' failed with retcode {ret}.")
        return None
    if not return_output:
        return ret

    # shorten the hostname to match /var/log/messages format
    data = ""
    for line in journal.splitlines():
        line = line.split()
        if len(line) < 4:
            continue
        line[3] = line[3].split(".")[0]
        data += " ".join(line) + "\n"
    return ret, data


def edit_config(file, parameters, update=False, file_error=True, list_values=True):
    """Merges configuration file with dict using configobj
    For more complex operations see https://configobj.readthedocs.io
    :param file: (str) Path to the configuration file.
    :param parameters: (dict) Accepts also nested sections, e.g. {'logging':{'a': 'a.log', 'b': 'b.log'}}.
    :param update: (bool) Use update() instead of merge(). Will remove section entries not in parameters dict.
    :param file_error: (bool) Set False to allow creating new files.
    :param list_values: (bool) If False, values are not parsed for list values. Single line values are not unquoted.
    :return: boolean
    """
    try:
        config = ConfigObj(file, file_error=file_error, list_values=list_values)
    except OSError as e:
        print(e)
        return False

    config.filename = file

    _print(f"INFO: Updating {file}")
    if update:
        config.update(parameters)
    else:
        config.merge(parameters)

    config.write()
    return True


def remove_from_config(file, parameters_to_remove, section=None, warn=True):
    """Removes objects from a configuration file.
    :param file: (str) Path to the configuration file.
    :param parameters_to_remove: (list) Parameters to remove.
    :param section: (str) Specify section of config file parameters are nested in.
    :param warn: (bool) Set False to supress warning when deleting nonexistent parameter.
    :return: boolean
    """
    try:
        config = ConfigObj(file, file_error=True)
    except OSError as e:
        _print("FAIL: Unable to open {}. It might not exist")
        print(e)
        return False

    config.filename = file
    fail = False
    for param in parameters_to_remove:
        _print(f'INFO: Removing "{param}" from {file}')
        try:
            if section:
                config[section].pop(param)
            else:
                config.pop(param)
        except KeyError:
            if warn:
                _print("WARN: Parameter to remove is not in config")
            fail = True

    config.write()
    if fail:
        return False
    return True


def generate_sosreport(skip_plugins=None, plugin_timeout=300, timeout=900):
    """Generates a sos report.
    :param skip_plugins: (string) comma separated list of plugins to skip (no space after comma)
    :param plugin_timeout: (int) timeout in seconds to allow each plugin to run for (only applicable to rhel-8+)
    :param timeout: (int) timeout for the sosreport proces in seconds. Use `None` for no timeout.
    :return:
    """
    cmd = f"sos report --batch --plugin-timeout {plugin_timeout}"
    dist = dist_ver()
    if dist < 8:
        cmd = "sosreport --batch"

    if not install_package("sos", check=True):
        print("FAIL: unable to install sos package")
        return False

    mount_flag = False
    if is_mounted("/var/crash"):
        print("INFO: Umounting /var/crash to avoid sosreport being hang there")
        umount("/var/crash")
        mount_flag = True

    if skip_plugins:
        cmd = cmd + f" --skip-plugins {skip_plugins}"

    ret_code, sosreport_ret = run(cmd, return_output=True, timeout=timeout)
    if ret_code != 0:
        print("FAIL: sosreport command failed")
        if mount_flag:
            mount("/var/crash")
        return False

    sos_report = None
    for line in sosreport_ret.split("\n"):
        if "/tmp/sosreport" in line:
            sos_report = line.strip()
            break

    if mount_flag:
        mount("/var/crash")

    return sos_report
