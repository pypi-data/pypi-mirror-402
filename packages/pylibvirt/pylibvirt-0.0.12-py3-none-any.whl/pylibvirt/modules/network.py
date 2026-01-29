import ipaddress

from pylibvirt.modules.devices import Device


class Network(Device):
    XML_NAME = "network"

    def __init__(self, name: str, mode: str or bool = "nat", domain: str = "network",
                 mtu: int = None,
                 stp: bool = True,
                 ip4_cidr: str = None,
                 dhcp_start: str = None,
                 dhcp_stop: str = None):
        """
        Create virtual network
        :param name: name of the network, must be unique
        :param mode: Type of network, values can be nat, route, open,
        hostdev and False for isolated network
        :param domain: DNS domain name to use, default is network
        :param mtu: MTU to use on the network, default is set by libvirt
        :param stp: Whether or not spanning tree should be enabled, default is true
        :param ip4_cidr: Optional parameter to set the ip configuration:
        eg: 192.168.1.0/24
        :param dhcp_start: Optional parameter to activate dhcp set start address
        and stop address. eg: 192.168.1.2
        :param dhcp_stop: Optional parameter to activate dhcp set start address
         and stop address. eg: 192.168.1.20
        """
        super().__init__(name=self.XML_NAME)
        self.__name = name
        self.__mode = mode
        self.__domain = domain
        self.__mtu = mtu
        self.__stp = stp
        self.__ip4_cidr = ip4_cidr
        self.__dhcp_start = dhcp_start
        self.__dhcp_stop = dhcp_stop
        self.generate_data()

    @property
    def dhcp_stop(self) -> str:
        return self.__dhcp_stop

    @dhcp_stop.setter
    def dhcp_stop(self, dhcp_stop: str):
        self.__dhcp_stop = dhcp_stop

    @property
    def dhcp_start(self) -> str:
        return self.__dhcp_start

    @dhcp_start.setter
    def dhcp_start(self, dhcp_start: str):
        self.__dhcp_start = dhcp_start

    @property
    def ip4_cidr(self) -> str:
        return self.__ip4_cidr

    @ip4_cidr.setter
    def ip4_cidr(self, ip4_cidr: str):
        self.__ip4_cidr = ip4_cidr

    @property
    def mode(self) -> str:
        return self.__mode

    @mode.setter
    def mode(self, mode: str):
        self.__mode = mode

    @property
    def mtu(self) -> int:
        return self.__mtu

    @mtu.setter
    def mtu(self, mtu: int):
        self.__mtu = mtu

    @property
    def stp(self) -> bool:
        return self.__stp

    @stp.setter
    def stp(self, stp: bool):
        self.__stp = stp

    @property
    def domain(self) -> str:
        return self.__domain

    @domain.setter
    def domain(self, domain: str):
        self.__domain = domain

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    def add_name(self):
        data = {"name": {
            "text": self.name
        }}
        return data

    def add_domain(self):
        data = {"domain": {
            "attr": {
                "name": self.domain
            }
        }}
        return data

    def add_mtu(self):
        data = {"mtu": {
            "attr": {
                "size": str(self.mtu)
            }
        }}
        return data

    def add_bridge_options(self):
        data = {"bridge": {
            "attr": {
                "stp": ("on" if self.stp else "off")
            }
        }}
        return data

    def add_forward(self):
        data = {"forward": {
            "attr": {
                "mode": self.mode
            }
        }}
        return data

    def add_dhcp(self):
        data = {"dhcp": {
            "children": {
                "range": {
                    "attr": {
                        "start": self.dhcp_start,
                        "end": self.dhcp_stop
                    }
                }
            }
        }}
        return data

    def add_ip(self):
        ip_net = ipaddress.ip_network(self.ip4_cidr)
        netmask = str(ip_net.netmask)
        ip = str(ip_net[1]).split('/')[0]
        data = {"ip": {
            "attr": {
                "address": ip,
                "netmask": netmask
            },
            "children": {

            }
        }}
        return data

    def generate_data(self):
        self.data[self.xml_name].update({"children": {}})
        self.update_data(self.add_name())
        self.update_data(self.add_domain())
        self.update_data(self.add_bridge_options())

        if self.mode:
            self.update_data(self.add_forward())

        if self.mtu:
            self.update_data(self.add_mtu())

        if self.ip4_cidr:
            self.update_data(self.add_ip())
            if self.dhcp_start and self.dhcp_stop:
                ip = self.data[self.XML_NAME]["children"]["ip"]["children"]
                ip.update(self.add_dhcp())
