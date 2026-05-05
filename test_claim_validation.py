from urllib.parse import urlparse

import pytest

from claim_validator import (
    ALLOWED_TYPES,
    SOURCE_WHITELIST,
    ClaimObject,
    ValidationError,
    validate_claim,
)


def _whitelisted_url() -> str:
    allowed = next(iter(SOURCE_WHITELIST))
    parsed = urlparse(allowed if '://' in allowed else f'https://{allowed}')
    domain = parsed.netloc or parsed.path
    return f'https://{domain}/signals/example'


def _valid_claim(**overrides) -> ClaimObject:
    payload = {
        'claim_text': 'FDA granted approval for an ADC oncology therapy.',
        'source_url': _whitelisted_url(),
        'source_name': 'FDA',
        'evidence_type': next(iter(ALLOWED_TYPES)),
        'pull_timestamp': '2026-05-05T12:00:00Z',
    }
    payload.update(overrides)
    return ClaimObject(**payload)


def test_empty_claim_text_rejected():
    claim = _valid_claim(claim_text='')

    with pytest.raises(ValidationError, match='claim_text'):
        validate_claim(claim)


def test_empty_source_url_rejected():
    claim = _valid_claim(source_url='')

    with pytest.raises(ValidationError, match='source_url'):
        validate_claim(claim)


def test_empty_source_name_rejected():
    claim = _valid_claim(source_name='')

    with pytest.raises(ValidationError, match='source_name'):
        validate_claim(claim)


def test_empty_pull_timestamp_rejected():
    claim = _valid_claim(pull_timestamp='')

    with pytest.raises(ValidationError, match='pull_timestamp'):
        validate_claim(claim)


def test_invalid_evidence_type_rejected():
    claim = _valid_claim(evidence_type='NOT_ALLOWED')

    with pytest.raises(ValidationError, match='evidence_type'):
        validate_claim(claim)


def test_non_whitelisted_source_domain_rejected():
    claim = _valid_claim(source_url='https://not-in-whitelist.example.com/item')

    with pytest.raises(ValidationError, match='domain|whitelist|SOURCE_WHITELIST'):
        validate_claim(claim)


def test_valid_claim_passes():
    claim = _valid_claim()

    assert validate_claim(claim) is None


def test_batch_validation_separates_valid_and_rejected():
    claims = [
        _valid_claim(),
        _valid_claim(claim_text=''),
        _valid_claim(source_url='https://not-in-whitelist.example.com/item'),
    ]

    valid_claims = []
    rejected_claims = []

    for claim in claims:
        try:
            validate_claim(claim)
            valid_claims.append(claim)
        except ValidationError as exc:
            rejected_claims.append((claim, str(exc)))

    assert len(valid_claims) == 1
    assert valid_claims[0].claim_text == 'FDA granted approval for an ADC oncology therapy.'
    assert len(rejected_claims) == 2
    assert rejected_claims[0][0].claim_text == ''
    assert rejected_claims[1][0].source_url == 'https://not-in-whitelist.example.com/item'
