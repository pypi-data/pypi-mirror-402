import secrets

from pylibvirt.modules.devices import Device


class NetworkInterfaceDevice(Device):
    XML_NAME = "interface"

    def __init__(self, net_type: str = 'network', net_interface: str = 'default',
                 model: str = 'virtio', vlans: [int] = None,
                 mac: str = None, mtu: int = None, boot_order: int = None):
        super().__init__(name=self.XML_NAME)
        self.__net_type = net_type
        self.__net_interface = net_interface
        self.__model = model
        self.__vlans = vlans
        self.__mtu = mtu
        self.__boot_order = boot_order
        if self.__vlans is not None and net_type != 'bridge':
            raise ValueError("Vlans are not supported on non-bridge interfaces")
        if not mac:
            self.mac = self.random_mac()
        else:
            self.__mac = mac
        self.generate_data()

    @staticmethod
    def random_mac():
        return "02:00:00:%02x:%02x:%02x" % (secrets.randbelow(255),
                                            secrets.randbelow(255),
                                            secrets.randbelow(255))

    @property
    def net_type(self) -> str:
        return self.__net_type

    @net_type.setter
    def net_type(self, model: str):
        self.__net_type = model

    @property
    def mac(self) -> str:
        return self.__mac

    @mac.setter
    def mac(self, mac: str):
        self.__mac = mac

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str):
        self.__model = model

    @property
    def net_interface(self) -> str:
        return self.__net_interface

    @net_interface.setter
    def net_interface(self, net_interface: str):
        self.__net_interface = net_interface

    @property
    def boot_order(self) -> list:
        return self.__boot_order

    @boot_order.setter
    def boot_order(self, boot_order: int):
        self.__boot_order = boot_order

    def add_vlans(self):
        return {
            "virtualport": {
                "attr": {
                    "type": "openvswitch"
                }
            },
            "vlan": {
                "attr": {
                    "trunk": "yes" if len(self.__vlans) > 1 else "no"
                },
                "children": [{
                    "tag": {
                        "attr": {
                            "id": str(vlan)
                        }
                    }
                } for vlan in self.__vlans]
            }
        }

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "type": self.net_type
                },
                "children": {
                    "source": {
                        "attr": {
                            self.net_type: self.net_interface
                        }
                    },
                    "mac": {
                        "attr": {
                            "address": str(self.mac)
                        }
                    },
                    "model": {
                        "attr": {
                            "type": self.model
                        }
                    }
                }
            }
        })
        if self.__mtu is not None:
            self.data[self.XML_NAME]["children"]["mtu"] = {
                "attr": {
                    "size": str(self.__mtu)
                }
            }
        if self.__vlans is not None:
            self.data[self.XML_NAME]["children"].update(self.add_vlans())
        if self.__boot_order is not None:
            self.data[self.XML_NAME]["children"]["boot"] = {
                "attr": {
                    "order": str(self.__boot_order)
                }
            }
