"""
PSIT -- Citation validation layer.
Rejects unsupported or non-whitelisted claims.
No LLM calls. No HTTP requests.
"""

from claim_schema import EvidenceClaim
from source_whitelist import is_approved_source, source_tier_for_url


REQUIRED_FIELDS = [
    "claim_text",
    "claim_type",
    "source_name",
    "source_url",
]


def validate_claim(claim: EvidenceClaim) -> EvidenceClaim:
    missing = []

    for field in REQUIRED_FIELDS:
        value = getattr(claim, field, None)
        if value is None or str(value).strip() == "":
            missing.append(field)

    if missing:
        claim.status = "rejected"
        claim.validation_message = f"Missing required field(s): {', '.join(missing)}"
        return claim

    if not is_approved_source(claim.source_url):
        claim.status = "rejected"
        claim.validation_message = "Source URL is not on the approved source whitelist"
        claim.source_tier = "Unapproved source"
        return claim

    claim.status = "validated"
    claim.source_tier = source_tier_for_url(claim.source_url)
    claim.validation_message = "Claim passed citation validation"
    return claim


def validate_claims(claims: list[EvidenceClaim]) -> list[EvidenceClaim]:
    return [validate_claim(claim) for claim in claims]