"""
PSIT -- Claim validation.
validate_claim() is the enforcement gate.
Claims that fail are blocked from reaching the UI.
"""
from urllib.parse import urlparse
from claim import ClaimObject, SOURCE_WHITELIST, ALLOWED_EVIDENCE_TYPES
 
 
class ValidationError(Exception):
    pass
 
 
def validate_claim(claim: ClaimObject) -> ClaimObject:
    """Validates a ClaimObject.
    Raises ValidationError on any violation.
    Returns the claim unchanged if valid."""
    errors = []
 
    if not claim.claim_text or not claim.claim_text.strip():
        errors.append('claim_text is required and cannot be empty')
 
    if not claim.source_url or not claim.source_url.strip():
        errors.append('source_url is required -- no URL, no claim')
 
    if not claim.source_name or not claim.source_name.strip():
        errors.append('source_name is required')
 
    if not claim.pull_timestamp or not claim.pull_timestamp.strip():
        errors.append('pull_timestamp is required')
 
    if claim.evidence_type not in ALLOWED_EVIDENCE_TYPES:
        errors.append(
            f'evidence_type must be one of {sorted(ALLOWED_EVIDENCE_TYPES)}'
        )
 
    # Source whitelist check
    if claim.source_url and claim.source_url.strip():
        netloc = urlparse(claim.source_url).netloc.lower()
        # Strip 'www.' prefix for comparison
        domain = netloc[4:] if netloc.startswith('www.') else netloc
        if not any(domain == w or domain.endswith('.' + w) for w in SOURCE_WHITELIST):
            errors.append(
                f"source domain '{domain}' is not on the approved whitelist"
            )
 
    if errors:
        raise ValidationError(f'Claim rejected: {" | ".join(errors)}')
 
    return claim
 
 
def validate_claims(claims: list) -> tuple[list, list]:
    """Validates a list of ClaimObjects.
    Returns (valid_claims, rejected_claims).
    rejected_claims is a list of (claim, reason_string) tuples."""
    valid, rejected = [], []
    for claim in claims:
        try:
            valid.append(validate_claim(claim))
        except ValidationError as e:
            rejected.append((claim, str(e)))
    return valid, rejected
