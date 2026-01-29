import json
import os
import logging
from typing import List, Optional, Dict
from pathlib import Path
import pkg_resources

from .models import GuardrailResult, GuardrailAction, GuardrailFinding
from .rules import Rule, PromptInjectionRule, SignalJailbreakRule, PiiRule, ToxicityRule
from .ml import OnnxJailbreakClassifier

# Rule registry
RULE_MAP = {
    "PromptInjectionRule": PromptInjectionRule,
    "SignalJailbreakRule": SignalJailbreakRule,
    "PiiRule": PiiRule,
    "ToxicityRule": ToxicityRule
}

class Policy:
    def __init__(self, config: dict):
        self.config = config

    @property
    def input_rules(self) -> List[dict]:
        return self.config.get("input_rules", [])

class StrictPolicy(Policy):
    def __init__(self):
        content = pkg_resources.resource_string(__name__, "policies/strict.json")
        super().__init__(json.loads(content))

class RelaxedPolicy(Policy):
    def __init__(self):
        content = pkg_resources.resource_string(__name__, "policies/relaxed.json")
        super().__init__(json.loads(content))

class GuardrailsEngine:
    def __init__(self, policy: Policy, classifier: Optional[OnnxJailbreakClassifier] = None):
        self.policy = policy
        self.classifier = classifier
        self.rules_instances: Dict[str, Rule] = {}
        
        # Instantiate rules defined in policy
        for entry in policy.input_rules:
            r_type = entry["rule_type"]
            if r_type in RULE_MAP and r_type not in self.rules_instances:
                self.rules_instances[r_type] = RULE_MAP[r_type]()

    def validate_input(self, text: str) -> GuardrailResult:
        findings: List[GuardrailFinding] = []
        action = GuardrailAction.ALLOW
        max_severity = 0
        safe_text = text

        # 1. Run Rules
        for entry in self.policy.input_rules:
            r_type = entry["rule_type"]
            rule_action = entry["action_mode"] # BLOCK, SANITIZE, ALLOW
            min_severity = entry.get("min_severity", 0)
            
            rule = self.rules_instances.get(r_type)
            if not rule:
                continue

            # Check
            rule_findings = rule.check(text)
            findings.extend(rule_findings)
            
            # Action determination
            for f in rule_findings:
                if f.severity > max_severity:
                    max_severity = f.severity
                
                if f.severity >= min_severity:
                    if rule_action == "BLOCK":
                        action = GuardrailAction.BLOCK
                    elif rule_action == "SANITIZE" and action != GuardrailAction.BLOCK:
                        action = GuardrailAction.SANITIZE

            # Sanitize if needed (and action is SANITIZE or ALLOW, but usually SANITIZE implies modify)
            # If we block, we don't care about safe_text usually, but good to have
            if rule_action == "SANITIZE":
                # We sanitize REGARDLESS of findings? Or only if findings?
                # Usually PiiRule.sanitize runs always on output_text.
                # Logic: apply sanitize if configured to sanitize.
                safe_text = rule.sanitize(safe_text)

        # 2. Run ML (Optional) -> merge
        if self.classifier:
             is_jailbreak, prob = self.classifier.predict(text)
             # Thresholds from requirements: >= 0.85 BLOCK, >= 0.55 SANITIZE
             ml_sev = int(prob * 10)
             if ml_sev > max_severity:
                 max_severity = ml_sev
             
             if is_jailbreak or prob >= 0.55:
                 findings.append(GuardrailFinding(
                     category="ML_CLASSIFIER",
                     rule="OnnxJailbreakClassifier",
                     severity=ml_sev,
                     message=f"ML Model detected jailbreak probability {prob:.2f}"
                 ))
                 if prob >= 0.85:
                     action = GuardrailAction.BLOCK
                 elif prob >= 0.55 and action != GuardrailAction.BLOCK:
                     action = GuardrailAction.SANITIZE

        # Calculate risk score (0..100)
        risk_score = min(max_severity * 10, 100)
        
        msg = None
        if action == GuardrailAction.BLOCK:
            msg = "Input blocked by security policy."
            safe_text = None
        
        return GuardrailResult(
            action=action,
            risk_score=risk_score,
            findings=findings,
            safe_text=safe_text,
            message_to_user=msg
        )
