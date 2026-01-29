import ipaddress


class ModAclNode:
    def __init__(self, node_type: str, node_cidr: str):
        if node_type not in ["deny", "allow"]:
            raise ValueError(f"ACL-config: Invalid node type: {node_type}")
        self.node_type = node_type
        self.node_cidr = node_cidr

    def evaluate(self, network_address: str) -> bool:
        in_cidr = ipaddress.ip_address(network_address) in ipaddress.ip_network(self.node_cidr)
        return in_cidr
