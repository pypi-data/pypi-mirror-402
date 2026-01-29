from typing import List

from debug.modules.acl.ModAclNode import ModAclNode


class ModAclList:
    def __init__(self, list_name: str, list_default: str, list_nodes: List[ModAclNode]):
        if list_default not in ["deny", "allow"]:
            raise ValueError(f"ACL-config: Invalid list default: {list_default}")
        self.list_name = list_name
        self.list_default = list_default
        self.list_nodes = list_nodes

    def evaluate(self, network_address: str) -> bool:
        for node in self.list_nodes:
            in_cidr = node.evaluate(network_address)
            if in_cidr:
                return node.node_type == "allow"
        return self.list_default == "allow"
