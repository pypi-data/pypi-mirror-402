from typing import List
from ..models import GuardrailFinding
from .base import Rule

class SignalJailbreakRule(Rule):
    name = "SIGNAL_JAILBREAK"
    category = "SECURITY"

    # Default signals map
    SIGNALS = {
        "ignore previous instructions": 10,
        "do anything now": 10,
        "DAN": 9,
        "always answer": 5,
        "no rules": 8,
        "unfiltered": 7,
        "developer mode": 9,
        "act as": 3
    }

    def check(self, input_text: str) -> List[GuardrailFinding]:
        score = 0
        detected = []
        lower = input_text.lower()
        
        for phrase, weight in self.SIGNALS.items():
            if phrase.lower() in lower:
                score += weight
                detected.append(phrase)
        
        if score > 0:
            severity = 10 if score >= 10 else 5
            return [GuardrailFinding(
                category=self.category,
                rule=self.name,
                severity=severity,
                message=f"Jailbreak signals detected: {', '.join(detected)} (Score: {score})"
            )]
        return []
