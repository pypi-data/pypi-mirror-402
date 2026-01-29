from typing import List

from debug.Condition import Condition


class Extension:
    def __init__(self, name: str, do_continue: bool = False):
        self.name: str = name
        self.do_continue: bool = do_continue
        self.conditions: List[Condition] = []

    def add_condition(self, condition: Condition) -> None:
        self.conditions.append(condition)
