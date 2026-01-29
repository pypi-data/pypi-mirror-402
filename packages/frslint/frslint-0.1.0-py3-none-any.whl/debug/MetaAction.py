from debug.Action import Action
from typing import Optional


class MetaAction(Action):
    def __init__(self, application: str, data: str, color: Optional[str] = None):
        super().__init__(application, data)
        self.color = color

    def to_string(self) -> str:
        colormap = {
            "red": 31,
            "green": 32,
            "yellow": 33,
            "blue": 34,
            "magenta": 35,
            "cyan": 36,
            "white": 37,
        }
        if self.color is None or self.color not in colormap:
            return f"> {super().to_string()}"
        return f"\033[{colormap[self.color]}m{super().to_string()}\033[0m"
