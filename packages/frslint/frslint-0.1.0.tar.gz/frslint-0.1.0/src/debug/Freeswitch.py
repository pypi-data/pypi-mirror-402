from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from debug.modules.AbstractFreeswitchModule import AbstractFreeswitchModule

if TYPE_CHECKING:
    from debug.Context import Context
import re

from log.Loggable import Loggable


class Freeswitch(Loggable):
    def __init__(
        self,
        verbose: bool,
        variables: Dict[str, str],
        configurations: Dict[str, AbstractFreeswitchModule],
        context_instructions: Dict[str, Context],
    ):
        super().__init__(verbose=verbose)
        self.variables: Dict[str, str] = variables
        self.configurations: Dict[str, AbstractFreeswitchModule] = configurations
        self.context_instructions: Dict[str, Context] = context_instructions

    def evaluate_function(self, function_name: str, args: List[str]) -> bool:
        for arg in args:
            n_arg = self.eval_value(arg)
            args[args.index(arg)] = n_arg

        for configuration in self.configurations.values():
            if configuration.supports_function(function_name):
                return configuration.evaluate(function_name, args)

        return False

    def eval_value(self, value: str) -> str:
        """Expand $${var_name} references in a string."""
        pattern = r"\$\$\{([^}]+)\}"

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in self.variables:
                return self.variables[var_name]
            self._log(f"  [WARN] Unknown variable: {var_name}")
            return match.group(0) # keep original if not found

        return re.sub(pattern, replacer, value)
