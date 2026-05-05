"""
PSIT -- Source whitelist.
Defines approved evidence domains and source tiers.
"""

from urllib.parse import urlparse


APPROVED_SOURCE_DOMAINS = {
    "clinicaltrials.gov": "Tier 1: ClinicalTrials.gov backbone",
    "www.clinicaltrials.gov": "Tier 1: ClinicalTrials.gov backbone",

    "fda.gov": "Tier 2: Regulatory overlay",
    "www.fda.gov": "Tier 2: Regulatory overlay",

    "ema.europa.eu": "Tier 2: Regulatory overlay",
    "www.ema.europa.eu": "Tier 2: Regulatory overlay",

    "statnews.com": "Tier 3: News overlay",
    "www.statnews.com": "Tier 3: News overlay",

    "endpoints.news": "Tier 3: News overlay",
    "www.endpoints.news": "Tier 3: News overlay",
}


def normalize_domain(url: str) -> str:
    if not url:
        return ""

    parsed = urlparse(url)
    return parsed.netloc.lower().replace("amp.", "")


def is_approved_source(url: str) -> bool:
    domain = normalize_domain(url)
    return domain in APPROVED_SOURCE_DOMAINS


def source_tier_for_url(url: str) -> str:
    domain = normalize_domain(url)
    return APPROVED_SOURCE_DOMAINS.get(domain, "Unapproved source")