"""
PSIT -- Claim schema.
Defines source-backed claim records for reliability validation.
No LLM calls. No HTTP requests.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EvidenceClaim:
    claim_text: str
    claim_type: str
    source_tier: str
    source_name: str
    source_url: str
    evidence_date: Optional[str] = None
    entity: Optional[str] = None
    status: str = "unvalidated"
    validation_message: str = "Not yet validated"

    def to_dict(self) -> dict:
        return {
            "claim_text": self.claim_text,
            "claim_type": self.claim_type,
            "source_tier": self.source_tier,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "evidence_date": self.evidence_date,
            "entity": self.entity,
            "status": self.status,
            "validation_message": self.validation_message,
        }