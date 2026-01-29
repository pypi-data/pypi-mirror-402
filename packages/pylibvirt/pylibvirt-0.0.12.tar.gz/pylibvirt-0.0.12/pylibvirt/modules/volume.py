import libvirt

from pylibvirt.modules.devices import Device


def create_disk(storage: libvirt.virStoragePool, capacity: int, name: str,
                disk_format: str = 'raw', size_unit: str = 'G', allocation: int = 0):
    new_volume = Volume(name=name, capacity=capacity, disk_format=disk_format,
                        size_unit=size_unit,
                        allocation=allocation)
    return storage.createXML(new_volume.generate_xml(), 0)


def clone_disk(storage: libvirt.virStoragePool, volume: libvirt.virStorageVol,
               capacity: int, name: str,
               disk_format: str = 'raw', size_unit: str = 'G', allocation: int = 0):
    new_volume = Volume(name=name, capacity=capacity, disk_format=disk_format,
                        size_unit=size_unit,
                        allocation=allocation)
    return storage.createXMLFrom(new_volume.generate_xml(), volume, 0)


class Volume(Device):
    XML_NAME = "volume"

    def __init__(self, name: str, capacity: int, allocation: int = 0,
                 size_unit: str = 'G', disk_format: str = "raw"):
        super().__init__(name=self.XML_NAME)
        self.__name = name
        self.__capacity = capacity
        self.__allocation = allocation
        self.__size_unit = size_unit
        self.__disk_format = disk_format
        self.generate_data()

    @property
    def disk_format(self) -> str:
        return self.__disk_format

    @disk_format.setter
    def disk_format(self, disk_format: str):
        self.__disk_format = disk_format

    @property
    def size_unit(self) -> str:
        return self.__size_unit

    @size_unit.setter
    def size_unit(self, size_unit: str):
        self.__size_unit = size_unit

    @property
    def allocation(self) -> int:
        return self.__allocation

    @allocation.setter
    def allocation(self, allocation: int):
        self.__allocation = allocation

    @property
    def capacity(self) -> int:
        return self.__capacity

    @capacity.setter
    def capacity(self, capacity: int):
        self.__capacity = capacity

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, name: str):
        self.__name = name

    def generate_data(self):
        self.data[self.xml_name].update({"children": {
            "name": {
                "text": self.name
            },
            "allocation": {
                "text": str(self.allocation),
                "attr": {
                    "unit": self.size_unit
                }
            },
            "capacity": {
                "text": str(self.capacity),
                "attr": {
                    "unit": self.size_unit
                }
            },
            "target": {
                "children": {
                    "format": {
                        "attr": {
                            "type": self.disk_format
                        }
                    }
                }
            }

        }})
