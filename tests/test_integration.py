import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pytest
from claim import ClaimObject
from validator import validate_claim, ValidationError
 
def test_valid_trial_claim_passes(trial_claim):
    result = validate_claim(trial_claim)
    assert result.source_url == trial_claim.source_url
    assert result.evidence_type == 'STRUCTURED_TRIAL'
 
def test_valid_regulatory_claim_passes(regulatory_claim):
    result = validate_claim(regulatory_claim)
    assert result.evidence_type == 'REGULATORY'
 
def test_valid_news_claim_passes(news_claim):
    result = validate_claim(news_claim)
    assert result.evidence_type == 'NEWS'
 
def test_invalid_domain_is_rejected():
    bad = ClaimObject(
        claim_text='Some fabricated market insight about an ADC program.',
        source_url='https://made-up-source.com/article/123',
        source_name='Unknown Source',
        evidence_type='NEWS',
        pull_timestamp='2025-01-15T09:00:00',
    )
    with pytest.raises(ValidationError, match='not on the approved whitelist'):
        validate_claim(bad)
 
def test_missing_source_url_is_rejected():
    no_url = ClaimObject(
        claim_text='A claim with no source URL attached.',
        source_url='',
        source_name='No Source',
        evidence_type='STRUCTURED_TRIAL',
        pull_timestamp='2025-01-15T09:00:00',
    )
    with pytest.raises(ValidationError, match='source_url is required'):
        validate_claim(no_url)
