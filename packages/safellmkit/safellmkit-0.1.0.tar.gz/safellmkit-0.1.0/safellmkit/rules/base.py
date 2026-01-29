from abc import ABC, abstractmethod
from typing import List
from ..models import GuardrailFinding

class Rule(ABC):
    name: str = "GenericRule"
    category: str = "General"

    @abstractmethod
    def check(self, input_text: str) -> List[GuardrailFinding]:
        pass

    def sanitize(self, input_text: str) -> str:
        return input_text
