from typing import List

from debug.Extension import Extension


class Context:
    def __init__(self, name: str, extensions: List[Extension]):
        self.name: str = name
        self.extensions: List[Extension] = extensions
