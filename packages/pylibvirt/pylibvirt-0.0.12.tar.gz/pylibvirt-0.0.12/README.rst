##############
Python Libvirt
##############

*****************
What is pylibvirt
*****************

Pylibvirt is a tools based on python-libvirt api.
The goal are to create virtual machines, networks, volumes and storage more easily
using yaml description file.


***************************
How to create template file
***************************

The template must contain at least the provider.

After you can declare just what you need.

If you just want to create a Storage on your target you can just add storage element.

**All properties used in the yaml are the same as those used in libvirt**


Provider
========

**Currently the only tested provider is Qemu/Kvm**


The URI format is the same as libvirt api.

.. code-block:: yaml

    provider:
        uri: qemu+ssh://root@ip/system

network
========

**Mode** *is the type of network, values can be nat, route, open, hostdev and False for
isolated network*

.. code-block:: yaml

    network:
        - network_name:
              mode: nat
              domain: network
              ip4_cidr: ipv4_format_cidr
              dhcp_start: first_ip_to_use
              dhcp_stop: last_ip_to_use

storage
========

Only *dir* storage have been tested

.. code-block:: yaml

    storage:
        - storage_name:
              pool_type: dir
              path: storage_path


volume
======

pool is the storage name declared in libvirt or previously in yaml.

name is the end name set to the volume. It's this name that must used in domain section.

The _key_ has no effect you can set what you want.

If you want to clone an existing volume or a previouslly create volume you can
use the clone argument with the name of the volume. The two volumes must be in the same
pool.

.. code-block:: yaml

    volume:
      - _key_:
          disk_format: qcow2
          capacity: 30
          size_unit: G
          pool: storage_name
          name: volume_name

domain
======

_key_ is the name of the VM, choose what you want.

Except the following key ['memory', 'boot_order', 'DiskDevice', 'domain_type',
                    'Feature', 'Os']

all other key must be the name of a class in pylibvirt/modules/devices

The class is called dynamically with the parameters.
Example if you want to add Rng module add an item call RngDevice (class in
pylibvirt/modules/devices/rng.py)

.. code-block:: yaml

    RngDevice:
        - first_rng_device:
            - arg_class: value
        - second_rng_device
            - model: virtio
            - backend_model: random
            - host_device: /dev/my_custom_random


.. code-block:: yaml

    domain:
      - _key_:
          boot_order:
            - cdrom
            - hd
          memory:
            mem_unit: G
            max_memory: 4
          Os:
            arch: x86_64
            machine: q35
            os_type: hvm
          Feature: # Features list: https://libvirt.org/formatdomain.html#hypervisor-features
            - acpi
            - kvm:
                hidden:
                  state: 'on'
                poll-control:
                  state: 'on'
          CpuDevice:
            cpu_model: host
            model_args:
              fallback: allow
            vcpu: 2
            vcpu_args:
              placement: static
          GraphicDevice:
            - spice_server:
                graphic_type: spice
          VideoDevice:
            - screen:
                model_type: qxl
                ram: 66500
          DiskDevice:
            - disk:
                volume: debian-10-2.qcow2
                driver: qemu
                bus: scsi
                pool: data
            - cdrom:
                volume: debian-10.10.0-amd64-netinst.iso
                pool: data

          NetworkInterfaceDevice:
            - default:
                net_interface: default
                net_type: network
                model: e1000e


**************
How to install
**************

Requirements
============

You need to install the following packages on your system to install python-libvirt in a virtualenv

Fedora
----------

RPM dependencies
^^^^^^^^^^^^^^^^

.. code-block:: bash

   dnf install python3-devel pkgconfig libvirt-devel

.. code-block:: bash

   pip install pylibvirt

Debian
----------
DEB dependencies
^^^^^^^^^^^^^^^^

.. code-block:: bash

   apt install python3-dev pkg-config libvirt-dev

.. code-block:: bash

   pip install pylibvirt

***********
How to use
***********

Cli usage
=========

.. code-block:: bash

    pylibvirt -t /path/to/template.yml

Use in python code
==================

To use pylibvirt in your python code you can do:

call manager and set file path

.. code-block:: python

    import pylibvirt
    pylibvirt.Manager(template='path_to_file')


or call manager and directly pass template object

.. code-block:: python

    import pylibvirt
    pylibvirt.Manager(template=[yaml object])


Create your external module
===========================

If you want to create your own pylibvirt modules you must create a class that inherits from

.. code-block:: python

    from pylibvirt.modules.devices import Device

and implement method *generate_data(self)*

In your setup.py you must register it

.. code-block:: python

    from setuptools import setup

    setup(
        name='cute_snek',
        entry_points={
            'pylibvirt_modules': [
                'ClassName = ModuleName',
            ],
        }
    )

If you use poetry configure your toml like this

.. code-block:: toml

    [tool.poetry.plugins."pylibvirt_modules"]
    ClassName = 'ModuleName'

You can find example of modules in pylibvirt/modules/devices