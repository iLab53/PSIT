import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pytest
from claim import ClaimObject
 
TS = '2025-01-15T09:00:00'
 
@pytest.fixture
def trial_claim():
    return ClaimObject(
        claim_text='NCT04354259 is a Phase 3 ADC trial sponsored by AstraZeneca.',
        source_url='https://clinicaltrials.gov/study/NCT04354259',
        source_name='ClinicalTrials.gov',
        evidence_type='STRUCTURED_TRIAL',
        pull_timestamp=TS,
        nct_id='NCT04354259',
    )
 
@pytest.fixture
def regulatory_claim():
    return ClaimObject(
        claim_text='FDA granted Breakthrough Therapy Designation for trastuzumab deruxtecan.',
        source_url='https://www.fda.gov/drugs/resources-information-approved-drugs/oncology',
        source_name='FDA',
        evidence_type='REGULATORY',
        pull_timestamp=TS,
    )
 
@pytest.fixture
def news_claim():
    return ClaimObject(
        claim_text='DESTINY-Breast04 results showed significant OS improvement.',
        source_url='https://www.statnews.com/2022/06/04/adc-results',
        source_name='STAT News',
        evidence_type='NEWS',
        pull_timestamp=TS,
    )
 
@pytest.fixture
def all_claims(trial_claim, regulatory_claim, news_claim):
    return [trial_claim, regulatory_claim, news_claim]
