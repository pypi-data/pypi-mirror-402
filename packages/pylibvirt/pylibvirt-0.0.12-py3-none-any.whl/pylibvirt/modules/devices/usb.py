from pylibvirt.modules.devices import Device


class UsbDevice(Device):
    XML_NAME = "hostdev"

    def __init__(self, vendor_id: str, product_id: str):
        super().__init__(name=self.XML_NAME)
        self.__vendor_id = vendor_id
        self.__product_id = product_id
        self.generate_data()

    @property
    def vendor_id(self) -> str:
        return self.__vendor_id

    @vendor_id.setter
    def vendor_id(self, vendor_id: str):
        self.__vendor_id = vendor_id

    @property
    def product_id(self) -> str:
        return self.__product_id

    @product_id.setter
    def product_id(self, product_id: str):
        self.__product_id = product_id

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "type": "usb",
                    "managed": "yes",
                    "mode": "subsystem"
                },
                "children": {
                    "source": {
                        "children": {
                            "vendor": {
                                "attr": {
                                    "id": self.vendor_id
                                }
                            },
                            "product": {
                                "attr": {
                                    "id": self.product_id
                                }
                            }
                        }
                    },
                }
            }
        })
