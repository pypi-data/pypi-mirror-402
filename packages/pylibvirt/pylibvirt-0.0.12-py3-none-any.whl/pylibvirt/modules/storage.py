from pylibvirt.modules.devices import Device


class Storage(Device):
    XML_NAME = "pool"

    def __init__(self, pool_type: str, pool_name: str):
        super().__init__(name=self.XML_NAME)
        self.__pool_type = pool_type
        self.__pool_name = pool_name

    @property
    def pool_name(self) -> str:
        return self.__pool_name

    @pool_name.setter
    def pool_name(self, pool_name: str):
        self.__pool_name = pool_name

    @property
    def pool_type(self) -> str:
        return self.__pool_type

    @pool_type.setter
    def pool_type(self, pool_type: str):
        self.__pool_type = pool_type

    def generate_data(self):
        self.data[self.xml_name].update({"children": {
            "name": {
                "text": self.pool_name
            }
        }})
        self.data[self.xml_name].update({"attr": {
            "type": self.pool_type
        }})


class DirStorage(Storage):
    def __init__(self, pool_name: str, path: str):
        super().__init__(pool_type="dir", pool_name=pool_name)
        self.__path = path
        self.generate_data()

    @property
    def path(self) -> str:
        return self.__path

    @path.setter
    def path(self, path: str):
        self.__path = path

    def add_path(self):
        return {
            "target": {
                "children": {
                    "path": {
                        "text": self.path
                    }
                }
            }
        }

    def generate_data(self):
        super().generate_data()
        self.update_data(self.add_path())
