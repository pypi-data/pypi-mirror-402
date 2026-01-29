from pylibvirt.modules.devices import Device


class RngDevice(Device):
    XML_NAME = "rng"

    def __init__(self, model: str = 'virtio', backend_model: str = "random",
                 host_device: str = '/dev/urandom'):
        super().__init__(name=self.XML_NAME)
        self.__model = model
        self.__backend_model = backend_model
        self.__host_device = host_device
        self.generate_data()

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str):
        self.__model = model

    @property
    def backend_model(self) -> str:
        return self.__backend_model

    @backend_model.setter
    def backend_model(self, backend_model: str):
        self.__backend_model = backend_model

    @property
    def host_device(self) -> str:
        return self.__host_device

    @host_device.setter
    def host_device(self, host_device: str):
        self.__host_device = host_device

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "model": self.model,
                },
                "children": {
                    "backend": {
                        "text": self.host_device,
                        "attr": {
                            "model": self.backend_model
                        }
                    }
                }
            }
        })
