import re
from typing import List
from ..models import GuardrailFinding
from .base import Rule

class PromptInjectionRule(Rule):
    name = "PROMPT_INJECTION"
    category = "SECURITY"

    PATTERNS = [
        r"ignore previous instructions",
        r"reveal system prompt",
        r"developer prompt",
        r"bypass policy",
        r"do anything now",
        r"answer as a",
        r"you are now",
        r"jailbroken",
        r"mode: enabled"
    ]

    def check(self, input_text: str) -> List[GuardrailFinding]:
        findings = []
        lower_text = input_text.lower()
        for pattern in self.PATTERNS:
            if re.search(pattern, lower_text):
                findings.append(GuardrailFinding(
                    category=self.category,
                    rule=self.name,
                    severity=10,
                    message=f"Prompt injection pattern detected: '{pattern}'"
                ))
        return findings
