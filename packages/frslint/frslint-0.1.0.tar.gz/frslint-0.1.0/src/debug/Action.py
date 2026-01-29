import re
from typing import Dict


class Action:
    def __init__(self, application, data=None):
        self.application = application
        self.data = data

    def var_evaluated(self, variables: Dict[str, str], global_variables: Dict[str, str]) -> "Action":
        if not self.data:
            return self
        local_pattern = r"\$\{([^}]+)\}"  # Matches ${var_name}
        global_pattern = r"\$\$\{([^}]+)\}"  # Matches $${var_name}
        self.data = re.sub(local_pattern, lambda m: variables.get(m.group(1), m.group(1)), self.data)
        self.data = re.sub(global_pattern, lambda m: global_variables.get(m.group(1), m.group(1)), self.data)
        return self

    def to_string(self) -> str:
        if self.data:
            return f"{self.application}: {self.data}"
        return f"{self.application}"
