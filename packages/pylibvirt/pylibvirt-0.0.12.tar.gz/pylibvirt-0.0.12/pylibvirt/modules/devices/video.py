from pylibvirt.modules.devices import Device


class VideoDevice(Device):
    XML_NAME = "video"

    def __init__(self, model_type: str = "qxl", ram: int = 65536, vram: int = 65536,
                 vgamem: int = 16384):
        super().__init__(name=self.XML_NAME)
        self.__model = model_type
        self.__ram = ram
        self.__vram = vram
        self.__vgamem = vgamem
        self.generate_data()

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str):
        self.__model = model

    @property
    def vgamem(self) -> int:
        return self.__vgamem

    @vgamem.setter
    def vgamem(self, vgamem: int):
        self.__vgamem = vgamem

    @property
    def ram(self) -> int:
        return self.__ram

    @ram.setter
    def ram(self, ram: int):
        self.__ram = ram

    @property
    def vram(self) -> int:
        return self.__vram

    @vram.setter
    def vram(self, vram: int):
        self.__vram = vram

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "children": {
                    "model": {
                        "attr": {
                            "type": self.model,
                            "ram": str(self.ram),
                            "vram": str(self.vram),
                            "vgamem": str(self.vgamem),
                        }
                    }
                }
            }
        })
