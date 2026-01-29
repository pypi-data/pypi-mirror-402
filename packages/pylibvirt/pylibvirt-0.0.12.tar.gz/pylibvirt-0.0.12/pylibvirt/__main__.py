"""Main module."""

import sys
import importlib
import pkg_resources
import click
import libvirt
import yaml
from rich import print

from pylibvirt.modules.devices.strorage import DEFAULT_BUS
from pylibvirt.modules.devices.strorage import DiskDevice
from pylibvirt.modules import next_dev, get_dev, Domain
from pylibvirt.modules.network import Network
from pylibvirt.modules.storage import DirStorage
from pylibvirt.modules.volume import Volume


class Manager:
    EXCLUDE_CLASS = ['memory', 'boot_order', 'DiskDevice', 'domain_type', 'Feature',
                     'Os']

    def __init__(self, template: str or dict, force_redefine: bool = False):
        self._external_modules = dict()
        self.__template_path = template
        self.__force_redefine = force_redefine
        self.template = self.load_template()
        self.conn = self.connect()
        self.list_domain = []  # List of Domain
        self.list_network = []  # List of Network
        self.list_storage = []  # List of Network
        self.list_volume = []  # List of Network
        self.load_external_modules()
        self.generate_network()
        self.generate_storage()
        self.generate_volume()
        self.generate_domain()

    def load_external_modules(self):
        for entry_point in pkg_resources.iter_entry_points('pylibvirt_modules'):
            self._external_modules.update({entry_point.name: entry_point.load()})

    def print(self):
        print(self.list_domain)
        print(self.list_network)
        print(self.list_storage)
        print(self.list_volume)

    @property
    def force_redefine(self):
        return self.__force_redefine

    @property
    def template_path(self) -> str:
        return self.__template_path

    @template_path.setter
    def template(self, template: str):
        self.__template_path = template

    def load_devices(self, class_name, param):
        if self._external_modules.get(class_name, None):
            _class = getattr(self._external_modules.get(class_name), class_name)
        else:
            module = importlib.import_module('pylibvirt.modules.devices')
            _class = getattr(module, class_name)
        instance = _class(**param)
        return instance

    @staticmethod
    def target_used(domain_disks: [{}]):
        list_target_use = {}

        for disk in domain_disks:
            for _name, config in disk.items():
                bus = config.get('bus', DEFAULT_BUS)
                target = config.get('target', None)
                if target:
                    list_target = list_target_use.get(bus, [])
                    list_target.append(target)
                    list_target_use.update({bus: list_target})
        return list_target_use

    def generate_dom_target(self, domain_disks: [{}]) -> [{}]:
        for disk in domain_disks:
            for _name, config in disk.items():
                bus = config.get('bus', DEFAULT_BUS)
                target = config.get('target', None)
                if not target:
                    target = \
                        next_dev(
                            dev_used=self.target_used(domain_disks=domain_disks).get(
                                bus, []), dev=get_dev(bus=bus))[0]
                    config.update({'target': target})
        return domain_disks

    def load_template(self):
        if isinstance(self.template_path, str):
            with open(self.template_path) as file:
                return yaml.safe_load(file)
        else:
            return self.template_path

    def connect(self):
        uri = self.template['provider']['uri']
        try:
            conn = libvirt.open(str(uri))
            return conn
        except libvirt.libvirtError:
            exit(1)

    def generate_network(self):
        networks = self.template['network'] if 'network' in self.template else []
        for network in networks:
            for name, config in network.items():
                net = Network(name=name, **config)
                if name in self.conn.listNetworks():
                    obj_net = self.conn.networkLookupByName(name)
                    self.list_network.append(obj_net)
                else:
                    # Define a new persistent automatically started network and start it
                    self.list_network.append(
                        self.conn.networkDefineXML(net.generate_xml()))
                    self.list_network[-1].setAutostart(True)
                    self.list_network[-1].create()

    def generate_storage(self):
        storages = self.template['storage'] if 'storage' in self.template else []
        for storage in storages:
            for name, config in storage.items():
                pool_type = config.pop('pool_type')
                if pool_type == 'dir':
                    dir = DirStorage(pool_name=name, **config)
                    if name in self.conn.listStoragePools():
                        self.list_storage.append(
                            self.conn.storagePoolLookupByName(name))
                    else:
                        self.list_storage.append(
                            self.conn.storagePoolDefineXML(dir.generate_xml()))
                        self.list_storage[-1].setAutostart(True)
                        self.list_storage[-1].create()

    def generate_volume(self):
        volumes = self.template['volume'] if 'volume' in self.template else []
        for volume in volumes:
            for _name, config in volume.items():
                pool = config.pop('pool')
                clone = config.pop('clone', None)
                vol = Volume(**config)
                pool = self.conn.storagePoolLookupByName(pool)
                if config.get('name') in pool.listVolumes():
                    self.list_volume.append(pool.storageVolLookupByName(
                        config.get('name')))
                else:
                    if not clone:
                        self.list_volume.append(pool.createXML(vol.generate_xml()))
                    else:
                        vol_to_clone = pool.storageVolLookupByName(clone)
                        self.list_volume.append(pool.createXMLFrom(vol.generate_xml(),
                                                                   vol_to_clone, 0))

    def generate_disk(self, domain):
        devices = list()
        disk_devices = domain['DiskDevice']
        disk_devices = self.generate_dom_target(domain_disks=disk_devices)

        for disk in disk_devices:
            for _name, config in disk.items():
                pool = config.pop('pool', 'default')
                vol_name = config.pop('volume')
                pool = self.conn.storagePoolLookupByName(pool)
                volume = pool.storageVolLookupByName(vol_name)
                devices.append(DiskDevice(volume=volume, **config))
        return devices

    def generate_devices(self, domain):
        devices = []
        for device, data in domain.items():
            if device not in self.EXCLUDE_CLASS:
                if isinstance(data, list):
                    for conf in data:
                        for _key, value in conf.items():
                            devices.append(
                                self.load_devices(class_name=device, param=value))
                else:
                    devices.append(
                        self.load_devices(class_name=device, param=data))

        return devices

    def create_dom(self, name, config):
        devices = []
        devices = devices + self.generate_disk(domain=config)
        devices = devices + self.generate_devices(domain=config)
        boot_order = config.get('boot_order')
        domain_type = config.get('domain_type', 'kvm')
        memory = config.get('memory')
        feature = config.get('Feature', None)
        os = config.get('Os', None)
        domain = Domain(name=name, devices=devices, boot_order=boot_order,
                        domain_type=domain_type, feature=feature, os=os)
        domain.memory = domain.set_memory(**memory)
        print(domain.generate_xml())
        list_domain = [dom.name() for dom in self.conn.listAllDomains()]
        if name in list_domain:
            if self.force_redefine:
                dom = self.conn.lookupByName(name)
                dom.undefine()
                self.conn.defineXML(domain.generate_xml())
            else:
                return self.conn.lookupByName(name)
        else:
            return self.conn.defineXML(domain.generate_xml())

    def generate_domain(self):
        domains = self.template['domain'] if 'domain' in self.template else []
        for domain in domains:
            for name, config in domain.items():
                self.list_domain.append(self.create_dom(name=name, config=config))


@click.command()
@click.option('--template', '-t', help='Path to the template file', required=True,
              default="./template/template.yml")
@click.option('--force-redefine', '-f',
              help='Force to redefine XML Element if it already exist', is_flag=True)
def main(args=None, **kwargs):
    """Console script for pylibvirt_."""
    click.echo("Replace this message by putting your code into "
               "pylibvirt_.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    Manager(template=kwargs['template'], force_redefine=kwargs['force_redefine'])


if __name__ == "__main__":
    sys.exit(main())
