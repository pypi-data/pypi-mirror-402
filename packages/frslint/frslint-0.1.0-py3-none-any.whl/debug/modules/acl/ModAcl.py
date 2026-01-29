import xml.etree.ElementTree as ET

from debug.modules.AbstractFreeswitchModule import AbstractFreeswitchModule
from debug.modules.acl.ModAclList import ModAclList
from debug.modules.acl.ModAclNode import ModAclNode


class ModAcl(AbstractFreeswitchModule):
    def __init__(self):
        self.lists: dict[str, ModAclList] = {}

    def add_list(self, list_name: str, list_default: str, list_nodes: list[ModAclNode]) -> None:
        self.lists[list_name] = ModAclList(list_name, list_default, list_nodes)

    def supports_function(self, function_name: str) -> bool:
        return function_name == "acl"

    def evaluate(self, function_name: str, args: list[str]) -> bool:
        if not self.supports_function(function_name):
            raise ValueError(f"ACL function not supported: {function_name}")
        if len(args) != 2:
            raise ValueError(f"Invalid number of arguments: {len(args)}")
        network_address = args[0]
        acl_list_name = args[1]
        if acl_list_name not in self.lists:
            raise ValueError(f"ACL list not found: {acl_list_name}")
        return self.lists[acl_list_name].evaluate(network_address)

    @staticmethod
    def parse_configuration(element: ET.Element) -> "ModAcl":
        mod_acl = ModAcl()
        for child in element:
            if child.tag != "network-lists":
                continue
            for network_list in child:
                if network_list.tag != "list":
                    continue
                list_name = network_list.attrib.get("name")
                list_default = network_list.attrib.get("default")
                list_nodes = []
                for node in network_list:
                    if node.tag != "node":
                        continue
                    node_type = node.attrib.get("type")
                    node_cidr = node.attrib.get("cidr")
                    list_nodes.append(ModAclNode(node_type, node_cidr))
                mod_acl.add_list(list_name, list_default, list_nodes)

        return mod_acl
