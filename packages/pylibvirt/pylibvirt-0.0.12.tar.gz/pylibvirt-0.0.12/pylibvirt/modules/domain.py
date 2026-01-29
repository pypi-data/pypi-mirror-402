import string
import uuid
from defusedxml import minidom

from pylibvirt.modules.devices.device import Device


def generate_dev(patter: str):
    alpha = string.ascii_lowercase
    dev_list = []
    for letter in alpha:
        dev_list.append(patter + letter)
    return dev_list


def next_dev(dev_used: list, dev: str = 'vd'):
    dev_used = set(dev_used)
    dev_list = set(generate_dev(dev))
    return sorted(list(dev_list - dev_used))


def next_dev_from_dict(dom_xml: str, dev: str = 'vd'):
    xml = minidom.parseString(dom_xml)
    disks = xml.getElementsByTagName('disk')
    dev_used = []
    for disk in disks:
        for target in disk.getElementsByTagName('target'):
            dev_used.append(target.getAttribute('dev'))
    dev_used = set(dev_used)
    dev_list = set(generate_dev(dev))
    return sorted(list(dev_list - dev_used))


def get_dev(bus: str):
    if bus == 'scsi':
        return 'sd'
    elif bus == 'virtio':
        return 'vd'
    elif bus == 'usb':
        return 'sd'
    elif bus == 'sata':
        return 'sd'
    elif bus == 'fdc':
        return 'fd'


def _add_sub_feature(feature):
    child = {}
    for key, data in feature.items():
        if isinstance(feature, str):
            child.update({key: {}})
        elif isinstance(feature, dict):
            child.update({key: {
                "attr": data
            }})
    return child


class Feature(Device):
    XML_NAME = "features"

    def __init__(self, feature=None):
        super().__init__(name=self.XML_NAME)
        self.root = []
        if feature is None:
            feature = ['acpi', 'acpi']
        self._feature = feature
        self.generate_data()

    def _convert_feature(self):
        for feature in self._feature:
            if isinstance(feature, str):
                self.update_data(data={feature: {}})
            elif isinstance(feature, dict):
                for key, data in feature.items():
                    self.update_data(data={key: {"children": _add_sub_feature(data)}})

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "children": {
                }
            }
        })
        self._convert_feature()


class Domain(Device):
    XML_NAME = "domain"

    DEFAULT_BOOT_ORDER = ["network", "cdrom", "hd"]

    def __init__(self, name: str, domain_type: str = "kvm", devices=None,
                 boot_order=None, os: dict = None, feature: list = None):
        super().__init__(name=self.XML_NAME)
        if os is None:
            os = {'arch': 'x86_64', 'machine': 'q35', 'os_type': 'hvm'}
        if devices is None:
            devices = []
        self.__domain_type = domain_type
        self.__feature = feature
        self.__uuid = str(uuid.uuid4())
        self.__name = name
        self.__devices = devices
        self.__os = os
        self.__memory = self.set_memory()
        if feature:
            self.__devices.append(self.get_feature())

        is_boot_order_defined = any(
            getattr(device, "boot_order", None) is not None
            for device in self.__devices
        )
        if bool(boot_order) and is_boot_order_defined:
            raise ValueError(
                "Specifying global as well as per-device boot " \
                "order is not supported by libvirt"
            )

        if is_boot_order_defined:
            # make libvirt honor per-device boot order by emptying global one
            boot_order = []
        elif boot_order is None:
            boot_order = self.DEFAULT_BOOT_ORDER.copy()
        self.__boot_order = boot_order

        self.generate_data()

    @property
    def boot_order(self) -> list:
        return self.__boot_order

    @boot_order.setter
    def boot_order(self, boot_order: list):
        self.__boot_order = boot_order

    @property
    def devices(self) -> list:
        return self.__devices

    @devices.setter
    def devices(self, devices: list):
        self.__devices = devices

    @property
    def domain_type(self) -> str:
        return self.__domain_type

    @domain_type.setter
    def domain_type(self, domain_type: str):
        self.__domain_type = domain_type

    @property
    def uuid(self) -> str:
        return self.__uuid

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    @property
    def memory(self) -> dict:
        return self.__memory

    @memory.setter
    def memory(self, memory: {}):
        self.__memory = memory
        self.generate_data()

    @staticmethod
    def set_memory(memory: int = 1, max_memory: int = 2, mem_unit: str = "G"):
        return {"memory": {
            "text": str(max_memory),
            "attr": {
                "unit": mem_unit
            }
        },
            "currentMemory": {
                "text": str(memory),
                "attr": {
                    "unit": mem_unit
                }
            }
        }

    @property
    def os(self) -> dict:
        return self.__os

    def get_os(self) -> dict:
        data = {
            "os": {
                "children": [{
                    "type": {
                        "attr": {
                            "arch": self.os.get('arch'),
                            "machine": self.os.get('machine'),
                        },
                        "text": self.os.get('os_type')
                    }
                }]
            }
        }
        boot_section = data["os"]["children"]
        for boot in self.boot_order:
            boot_section.append({"boot": {
                "attr": {
                    "dev": boot
                }
            }})

        return data

    def get_feature(self):
        feature = Feature(feature=self.__feature)
        return feature

    def add_device(self, device: Device):
        self.devices.append(device)

    def add_devices_to_data(self, device: Device):
        device.generate_data()
        devices = self.data[self.XML_NAME]
        if len(device.root) > 0:
            for root in device.root:
                devices = devices["children"][root]
            devices = devices["children"]
            devices.append(device.data)
        else:
            devices = devices["children"]
            devices.update(device.data)

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "type": self.domain_type
                },
                "children": {
                    "name": {
                        "text": self.name
                    },
                    "uuid": {
                        "text": self.uuid
                    },
                    "devices": {
                        "children": [

                        ]
                    }
                }
            }
        })
        self.update_data(self.get_os())
        self.update_data(self.memory)

        for device in self.devices:
            self.add_devices_to_data(device)
