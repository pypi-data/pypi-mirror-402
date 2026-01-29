from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class GuardrailAction(str, Enum):
    ALLOW = "ALLOW"
    SANITIZE = "SANITIZE"
    BLOCK = "BLOCK"

class GuardrailFinding(BaseModel):
    category: str
    rule: str
    severity: int
    message: str

class GuardrailResult(BaseModel):
    action: GuardrailAction
    risk_score: int = Field(ge=0, le=100)
    findings: List[GuardrailFinding] = []
    safe_text: Optional[str] = None
    message_to_user: Optional[str] = None
