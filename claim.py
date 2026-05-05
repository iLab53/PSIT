"""
PSIT -- Claim schema and source whitelist.
Every piece of information rendered in the UI must be a validated ClaimObject.
No source URL = no claim. No approved source = no claim.
"""
from dataclasses import dataclass
from typing import Optional
 
# Approved public sources for the MVP.
# Claims referencing any other domain are blocked.
SOURCE_WHITELIST = {
    'clinicaltrials.gov',
    'fda.gov',
    'ema.europa.eu',
    'endpts.com',
    'statnews.com',
}
 
# Valid evidence types.
# Determines how the claim is tiered and displayed in the UI.
ALLOWED_EVIDENCE_TYPES = {
    'STRUCTURED_TRIAL',   # Derived from ClinicalTrials.gov structured fields
    'REGULATORY',         # From FDA or EMA official announcements
    'NEWS',               # From public news RSS (Tier 3 signal)
    'SUMMARY',            # LLM-generated summary of validated structured data
}
 
@dataclass
class ClaimObject:
    claim_text:    str            # The assertion being made
    source_url:    str            # Required -- no URL, no claim
    source_name:   str            # Human-readable source label
    evidence_type: str            # Must be in ALLOWED_EVIDENCE_TYPES
    pull_timestamp: str           # ISO-8601 UTC -- when was this data retrieved
    nct_id:        Optional[str] = None  # If claim relates to a specific trial
