from collections import defaultdict

from pylibvirt.modules.devices.xml import XmlGenerator

data_dict = defaultdict(list)


class Device(XmlGenerator):

    def __init__(self, name):
        self.root = ['devices']
        self.xml_name = name
        self.data = defaultdict(list)
        self.data.update({
            name: {

            }
        })

    def __str__(self):
        return self.generate_xml()

    def generate_xml(self) -> str:
        return self.generate_xml_element(data=self.data)

    def generate_data(self):
        raise NotImplementedError

    def update_data(self, data):
        self.data[self.xml_name]["children"].update(data)
