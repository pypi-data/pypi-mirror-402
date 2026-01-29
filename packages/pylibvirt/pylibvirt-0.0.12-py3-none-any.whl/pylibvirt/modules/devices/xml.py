import xml.etree.cElementTree as ET  # nosec
import defusedxml


class XmlGenerator:
    def __init__(self):
        defusedxml.defuse_stdlib()

    def __create_xml_elt(self, data, parent):
        for key, value in data.items():
            attr = value.get('attr', {})
            text = value.get('text', None)
            children = value.get('children', None)

            entry = ET.SubElement(parent, key, attrib=attr)
            if text:
                entry.text = text

            if children:
                self.add_node(data=children, parent=entry)

    def add_node(self, data, parent):
        if isinstance(data, list):
            for d in data:
                self.__create_xml_elt(data=d, parent=parent)
        else:
            self.__create_xml_elt(data=data, parent=parent)

    def generate_xml_element(self, data: dict):
        for key, value in data.items():
            attr = value.get('attr', {})
            text = value.get('text', None)
            children = value.get('children', None)

            document = ET.Element(key, attrib=attr)
            if text:
                document.text = text
            if children:
                self.add_node(data=children, parent=document)

        return ET.tostring(document).decode()
