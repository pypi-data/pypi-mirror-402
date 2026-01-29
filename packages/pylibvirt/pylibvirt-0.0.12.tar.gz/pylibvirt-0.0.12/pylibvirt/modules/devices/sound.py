from pylibvirt.modules.devices import Device


class SoundDevice(Device):
    XML_NAME = "sound"

    def __init__(self, model: str = 'ich6'):
        super().__init__(name=self.XML_NAME)
        self.__model = model
        self.generate_data()

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str):
        self.__model = model

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "model": self.model,
                }}
        })
