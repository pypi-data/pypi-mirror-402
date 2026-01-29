import re
from typing import List
from ..models import GuardrailFinding
from .base import Rule

class PiiRule(Rule):
    name = "PII_SANITIZER"
    category = "PRIVACY"

    EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_REGEX = r"\b(\+?\d{1,3}[- ]?)?\d{3}[- ]?\d{3}[- ]?\d{4}\b"

    def check(self, input_text: str) -> List[GuardrailFinding]:
        findings = []
        if re.search(self.EMAIL_REGEX, input_text):
            findings.append(GuardrailFinding(
                category=self.category,
                rule=self.name,
                severity=7,
                message="Email address detected"
            ))
        if re.search(self.PHONE_REGEX, input_text):
            findings.append(GuardrailFinding(
                category=self.category,
                rule=self.name,
                severity=7,
                message="Phone number detected"
            ))
        return findings

    def sanitize(self, input_text: str) -> str:
        sanitized = re.sub(self.EMAIL_REGEX, "[EMAIL_REDACTED]", input_text)
        sanitized = re.sub(self.PHONE_REGEX, "[PHONE_REDACTED]", sanitized)
        return sanitized
