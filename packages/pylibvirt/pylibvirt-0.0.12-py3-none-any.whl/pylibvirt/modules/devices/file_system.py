from pylibvirt.modules.devices import Device


class FileSystemDevice(Device):
    XML_NAME = "filesystem"

    def __init__(self, source: str, target: str, mount_type: str = "mount",
                 access_mode: str = "mapped",
                 read_only: bool = False):
        super().__init__(name=self.XML_NAME)
        self.__source = source
        self.__target = target
        self.__mount_type = mount_type
        self.__access_mode = access_mode
        self.__read_only = read_only
        self.generate_data()

    @property
    def read_only(self) -> bool:
        return self.__read_only

    @read_only.setter
    def read_only(self, read_only: bool):
        self.__read_only = read_only

    @property
    def access_mode(self) -> str:
        return self.__access_mode

    @access_mode.setter
    def access_mode(self, access_mode: str):
        self.__access_mode = access_mode

    @property
    def mount_type(self) -> str:
        return self.__mount_type

    @mount_type.setter
    def mount_type(self, mount_type: str):
        self.__mount_type = mount_type

    @property
    def target(self) -> str:
        return self.__target

    @target.setter
    def target(self, target: str):
        self.__target = target

    @property
    def source(self) -> str:
        return self.__source

    @source.setter
    def source(self, source: str):
        self.__source = source

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "type": self.mount_type,
                    "accessmode": self.access_mode
                },
                "children": {
                    "source": {
                        "attr": {
                            "dir": self.source
                        }
                    },
                    "target": {
                        "attr": {
                            "dir": self.target
                        }
                    }
                }
            }
        })
        # TODO: if self.read_only add readonly
