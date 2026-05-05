"""
PSIT -- Claim validation test suite.
Every rejection case has a corresponding test.
Run: pytest tests/ -v
"""
import pytest
from claim import ClaimObject
from validator import validate_claim, validate_claims, ValidationError
 
# --- Fixtures ---
VALID = ClaimObject(
    claim_text='There are 312 ADC oncology trials registered in ClinicalTrials.gov.',
    source_url='https://clinicaltrials.gov/api/v2/studies',
    source_name='ClinicalTrials.gov',
    evidence_type='STRUCTURED_TRIAL',
    pull_timestamp='2026-04-30T12:00:00Z',
)
 
# --- Valid claim passes ---
def test_valid_claim_passes():
    result = validate_claim(VALID)
    assert result.claim_text == VALID.claim_text
 
# --- Required field rejections ---
def test_empty_claim_text_rejected():
    bad = ClaimObject('', VALID.source_url, VALID.source_name,
                      VALID.evidence_type, VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='claim_text is required'):
        validate_claim(bad)
 
def test_empty_source_url_rejected():
    bad = ClaimObject(VALID.claim_text, '', VALID.source_name,
                      VALID.evidence_type, VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='source_url is required'):
        validate_claim(bad)
 
def test_empty_source_name_rejected():
    bad = ClaimObject(VALID.claim_text, VALID.source_url, '',
                      VALID.evidence_type, VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='source_name is required'):
        validate_claim(bad)
 
def test_empty_pull_timestamp_rejected():
    bad = ClaimObject(VALID.claim_text, VALID.source_url, VALID.source_name,
                      VALID.evidence_type, '')
    with pytest.raises(ValidationError, match='pull_timestamp is required'):
        validate_claim(bad)
 
def test_invalid_evidence_type_rejected():
    bad = ClaimObject(VALID.claim_text, VALID.source_url, VALID.source_name,
                      'MADE_UP_TYPE', VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='evidence_type must be one of'):
        validate_claim(bad)
 
# --- Source whitelist rejections ---
def test_non_whitelisted_domain_rejected():
    bad = ClaimObject(VALID.claim_text, 'https://randomsite.com/article',
                      'Random Site', VALID.evidence_type, VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='not on the approved whitelist'):
        validate_claim(bad)
 
def test_lookalike_domain_rejected():
    # 'evil-clinicaltrials.gov' must NOT pass whitelist
    bad = ClaimObject(VALID.claim_text,
                      'https://evil-clinicaltrials.gov/study/NCT123',
                      'Fake Source', VALID.evidence_type, VALID.pull_timestamp)
    with pytest.raises(ValidationError, match='not on the approved whitelist'):
        validate_claim(bad)
 
def test_www_prefix_passes_whitelist():
    # www.clinicaltrials.gov must pass
    claim = ClaimObject(VALID.claim_text,
                        'https://www.clinicaltrials.gov/study/NCT123',
                        VALID.source_name, VALID.evidence_type, VALID.pull_timestamp)
    result = validate_claim(claim)
    assert result is not None
 
# --- Batch validation ---
def test_batch_separates_valid_and_rejected():
    bad = ClaimObject('', VALID.source_url, VALID.source_name,
                      VALID.evidence_type, VALID.pull_timestamp)
    valid, rejected = validate_claims([VALID, bad])
    assert len(valid) == 1
    assert len(rejected) == 1
    assert rejected[0][0] is bad
 
def test_batch_all_valid():
    valid, rejected = validate_claims([VALID, VALID])
    assert len(valid) == 2
    assert len(rejected) == 0
 
def test_batch_all_rejected():
    bad = ClaimObject('', '', '', 'BAD_TYPE', '')
    valid, rejected = validate_claims([bad])
    assert len(valid) == 0
    assert len(rejected) == 1
