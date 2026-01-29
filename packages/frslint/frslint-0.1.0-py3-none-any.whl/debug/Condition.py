from __future__ import annotations

import re
from typing import TYPE_CHECKING, Dict, List, Tuple, Optional

from debug.Action import Action

if TYPE_CHECKING:
    from debug.Freeswitch import Freeswitch


class Condition:
    def __init__(self, field: Optional[str], expression: Optional[str], do_break: str = "on-false", require_nested: bool = True):
        self.field: str = field
        self.expression: str = expression
        self.do_break: str = do_break
        self.require_nested: bool = require_nested
        self.actions: List[Action] = []
        self.anti_actions: List[Action] = []

    def empty(self) -> bool:
        return self.actions == [] and self.anti_actions == []

    def eval_channel_variable(self, value: str, channel_variables: Dict[str, str]) -> str:
        pattern = r"\$\{([^}]+)\}"  # Matches ${var_name}
        return re.sub(pattern, lambda m: channel_variables.get(m.group(1), m.group(1)), value)

    def evaluate(self, channel_variables: Dict[str, str], freeswitch: Freeswitch) -> Tuple[bool, Dict[str, str]]:
        # empty conditions are always true
        if self.field is None and self.expression is None:
            return True, {}

        # example field: ${acl(192.168.1.1 acl_drei_at)}
        FUNCTION_PATTERN = r"^\$\{(\w+)\(([^)]*)\)?\}$"
        match = re.match(FUNCTION_PATTERN, self.field)
        if match:
            function_name = match.group(1)
            function_args = match.group(2).split(" ")
            function_args = [self.eval_channel_variable(arg, channel_variables) for arg in function_args]
            return freeswitch.evaluate_function(function_name, function_args), {}

        # TODO: other fun like wday and stuff
        variable = channel_variables.get(self.field)
        if variable is None:
            return False, {}

        match = re.match(self.expression, variable)
        result = match is not None
        capture_groups: Dict[str, str] = {}
        if match:
            capture_groups["$0"] = variable
            # enumerate groups
            for idx, group in enumerate(match.groups(), start=1):
                capture_groups[f"${idx}"] = group
        return result, capture_groups

    def add_action(self, action: Action) -> None:
        self.actions.append(action)

    def add_anti_action(self, anti_action: Action) -> None:
        self.anti_actions.append(anti_action)
