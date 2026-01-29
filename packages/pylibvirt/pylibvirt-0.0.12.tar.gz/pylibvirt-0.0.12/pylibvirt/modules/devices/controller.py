from pylibvirt.modules.devices import Device


class ControllerDevice(Device):
    XML_NAME = "controller"

    def __init__(self, controller_type: str = "scsi", model: str = "virtio-scsi"):
        super().__init__(name=self.XML_NAME)
        self.__controller_type = controller_type
        self.__model = model
        self.generate_data()

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str):
        self.__model = model

    @property
    def controller_type(self) -> str:
        return self.__controller_type

    @controller_type.setter
    def controller_type(self, controller_type: str):
        self.__controller_type = controller_type

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "model": self.model,
                    "type": self.controller_type,
                }}
        })
