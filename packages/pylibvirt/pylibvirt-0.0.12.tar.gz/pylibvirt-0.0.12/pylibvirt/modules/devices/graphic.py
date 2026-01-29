from pylibvirt.modules.devices import Device


class GraphicDevice(Device):
    XML_NAME = "graphics"

    def __init__(self, graphic_type: str = "spice", port: int = -1, tls_port: int = -1,
                 password: str = None,
                 image_compression: str = 'off', open_gl: bool = False,
                 render_node: str = "", listen: str = "address"):
        super().__init__(name=self.XML_NAME)
        self.__graphic_type = graphic_type
        self.__port = port
        self.__tls_port = tls_port
        self.__password = password
        self.__image_compression = image_compression
        self.__open_gl = open_gl
        self.__render_node = render_node
        self.__listen = listen
        self.generate_data()

    @property
    def listen(self) -> str:
        return self.__listen

    @listen.setter
    def listen(self, listen: str):
        self.__listen = listen

    @property
    def render_node(self) -> str:
        return self.__render_node

    @render_node.setter
    def render_node(self, render_node: str):
        self.__render_node = render_node

    @property
    def open_gl(self) -> bool:
        return self.__open_gl

    @open_gl.setter
    def open_gl(self, open_gl: bool):
        self.__open_gl = open_gl

    @property
    def image_compression(self) -> str:
        return self.__image_compression

    @image_compression.setter
    def image_compression(self, image_compression: str):
        self.__image_compression = image_compression

    @property
    def password(self) -> str:
        return self.__password

    @password.setter
    def password(self, password: str):
        self.__password = password

    @property
    def tls_port(self) -> int:
        return self.__tls_port

    @tls_port.setter
    def tls_port(self, tls_port: int):
        self.__tls_port = tls_port

    @property
    def port(self) -> int:
        return self.__port

    @port.setter
    def port(self, port: int):
        self.__port = port

    @property
    def graphic_type(self) -> str:
        return self.__graphic_type

    @graphic_type.setter
    def graphic_type(self, graphic_type: str):
        self.__graphic_type = graphic_type

    def __add_open_gl(self):
        data = self.data[self.XML_NAME]["children"]

        if not self.open_gl:
            value = {"gl": {
                "attr": {
                    "enable": "no"
                }
            }}
        else:
            value = {"gl": {
                "attr": {
                    "enable": "yes",
                    "rendernode": self.render_node
                }
            }}
        data.update(value)

    def __add_port(self):
        data = self.data[self.XML_NAME]["attr"]

        if self.port == -1:
            value = {
                "autoport": "yes"
            }
        else:
            value = {
                "autoport": "no",
                "tlsPort": str(self.tls_port),
                "port": str(self.port)
            }
        data.update(value)

    def generate_data(self):
        self.data.update({
            self.XML_NAME: {
                "attr": {
                    "type": self.graphic_type,
                },
                "children": {
                    "listen": {
                        "attr": {
                            "type": self.listen
                        }
                    },
                    "image": {
                        "attr": {
                            "compression": self.image_compression
                        }
                    }
                }
            }
        })
        self.__add_open_gl()
        self.__add_port()
