from typing import List
from ..models import GuardrailFinding
from .base import Rule

class ToxicityRule(Rule):
    name = "TOXICITY"
    category = "CONTENT_SAFETY"

    # Minimal list for demonstration
    BAD_WORDS = ["idiot", "stupid", "dumb", "hate", "kill"]

    def check(self, input_text: str) -> List[GuardrailFinding]:
        findings = []
        lower = input_text.lower()
        for word in self.BAD_WORDS:
            if word in lower.split(): # simple tokenization check
                findings.append(GuardrailFinding(
                    category=self.category,
                    rule=self.name,
                    severity=5,
                    message=f"Toxic language detected: {word}"
                ))
        return findings

    def sanitize(self, input_text: str) -> str:
        words = input_text.split()
        sanitized = []
        for w in words:
            if w.lower() in self.BAD_WORDS:
                sanitized.append("*" * len(w))
            else:
                sanitized.append(w)
        return " ".join(sanitized)
