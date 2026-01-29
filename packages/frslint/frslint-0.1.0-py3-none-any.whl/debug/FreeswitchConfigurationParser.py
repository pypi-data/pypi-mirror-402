import xml.etree.ElementTree as ET
from collections.abc import Generator
from typing import Callable, Dict

from debug.modules.AbstractFreeswitchModule import AbstractFreeswitchModule
from debug.modules.acl.ModAcl import ModAcl


class FreeswitchConfigurationParser:
    def get_configration_parser(self, conf_name: str) -> Callable[[ET.Element], AbstractFreeswitchModule]:
        if conf_name == "acl.conf":
            return ModAcl.parse_configuration
        else:
            raise ValueError(f"Unknown configuration parser: {conf_name}")

    def parse(self, element: ET.Element) -> Dict[str, AbstractFreeswitchModule]:
        configurations: dict[str, AbstractFreeswitchModule] = {}
        for child in self.walk_tree(element):
            if child.tag == "configuration":
                conf_name = child.attrib.get("name")
                if conf_name is None:
                    raise ValueError("Configuration name is required")
                try:
                    parser_func = self.get_configration_parser(conf_name)
                    configurations[conf_name] = parser_func(child)
                except ValueError:
                    # Its just not supported yet
                    # print(f"Error parsing {conf_name}: {e}")
                    continue

        return configurations

    def walk_tree(self, element: ET.Element) -> Generator[ET.Element, None, None]:
        yield element
        for child in element:
            yield from self.walk_tree(child)
