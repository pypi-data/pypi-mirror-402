# LibSAN

Python library to manage Storage Area Network devices
## Installation
### Dependencies
 * Python>=3.6
 * pip>=20.3

### Fedora, RHEL-8, RHEL-9
`dnf install python3-pip`  

(optional) create virtualenv  
`python3 -m pip install virtualenv`  
`python3 -m venv ~/libsan-venv`

`~/libsan-venv/bin/python3 -m pip install -U pip wheel`  
`~/libsan-venv/bin/python3 -m pip install libsan`  
(use `libsan[ssh]` to install optional ssh capabilities)


### From source
`git clone; cd python-libsan` \
`python3 -m pip install .` \
or \
`python3 -m pip install .[ssh]`

### Installation on alternate architectures
Before installing libsan on non-x86_64 archs (s390x, ppc64le, aarch64),
install `python3-devel` and `gcc` to be able to compile dependencies as needed.

### How to uninstall the module
`python3 -m pip uninstall libsan`

## Usage:
Before using the modules copy sample_san_top.conf
to /etc/san_top.conf (this is the default path to read the config) and
edit it according to your SAN environment.
