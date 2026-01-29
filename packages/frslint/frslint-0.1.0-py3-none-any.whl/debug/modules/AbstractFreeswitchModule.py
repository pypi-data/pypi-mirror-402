import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import List


class AbstractFreeswitchModule(ABC):
    @abstractmethod
    def supports_function(self, function_name: str) -> bool:
        pass

    @abstractmethod
    def evaluate(self, function_name: str, args: List[str]) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def parse_configuration(element: ET.Element) -> "AbstractFreeswitchModule":
        pass
