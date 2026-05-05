"""
PSIT -- Build validated claims from existing evidence tables.
Creates a deterministic evidence_claims table from trial and overlay records.
"""

import pandas as pd

from claim_schema import EvidenceClaim
from citation_validator import validate_claim
from db import get_connection


def ensure_claims_table() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                claim_text TEXT,
                claim_type TEXT,
                source_tier TEXT,
                source_name TEXT,
                source_url TEXT,
                evidence_date TEXT,
                entity TEXT,
                status TEXT,
                validation_message TEXT
            )
        """)
        conn.commit()


def clear_claims_table() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM evidence_claims")
        conn.commit()


def _safe(value) -> str:
    if value is None:
        return "Not reported"
    if pd.isna(value):
        return "Not reported"
    text = str(value).strip()
    return text if text else "Not reported"


def build_trial_claims() -> list[EvidenceClaim]:
    with get_connection() as conn:
        trials = pd.read_sql_query("SELECT * FROM trials", conn)

    claims = []

    for _, row in trials.iterrows():
        nct_id = _safe(row.get("nct_id"))
        title = _safe(row.get("brief_title"))
        sponsor = _safe(row.get("sponsor"))
        phase = _safe(row.get("phase"))
        status = _safe(row.get("overall_status"))
        source_url = _safe(row.get("source_url"))

        claim_text = (
            f"{nct_id}: {title} is listed on ClinicalTrials.gov "
            f"with sponsor {sponsor}, phase {phase}, and status {status}."
        )

        claims.append(EvidenceClaim(
            claim_text=claim_text,
            claim_type="trial_record",
            source_tier="Tier 1: ClinicalTrials.gov backbone",
            source_name="ClinicalTrials.gov",
            source_url=source_url,
            evidence_date=_safe(row.get("last_update_date")),
            entity=nct_id,
        ))

    return claims


def build_regulatory_claims() -> list[EvidenceClaim]:
    with get_connection() as conn:
        try:
            rows = pd.read_sql_query("SELECT * FROM regulatory_signals", conn)
        except Exception:
            rows = pd.DataFrame()

    claims = []

    for _, row in rows.iterrows():
        title = _safe(row.get("title"))
        source_name = _safe(row.get("source_name"))
        source_url = _safe(row.get("source_url"))

        claim_text = f"{source_name} published a regulatory signal titled: {title}"

        claims.append(EvidenceClaim(
            claim_text=claim_text,
            claim_type="regulatory_signal",
            source_tier="Tier 2: Regulatory overlay",
            source_name=source_name,
            source_url=source_url,
            evidence_date=_safe(row.get("published_date", row.get("published"))),
            entity=title,
        ))

    return claims


def build_news_claims() -> list[EvidenceClaim]:
    with get_connection() as conn:
        try:
            rows = pd.read_sql_query("SELECT * FROM news_signals", conn)
        except Exception:
            rows = pd.DataFrame()

    claims = []

    for _, row in rows.iterrows():
        title = _safe(row.get("title"))
        source_name = _safe(row.get("source_name"))
        source_url = _safe(row.get("source_url"))

        claim_text = f"{source_name} published a news signal titled: {title}"

        claims.append(EvidenceClaim(
            claim_text=claim_text,
            claim_type="news_signal",
            source_tier="Tier 3: News overlay",
            source_name=source_name,
            source_url=source_url,
            evidence_date=_safe(row.get("published_date", row.get("published"))),
            entity=title,
        ))

    return claims


def insert_claims(claims: list[EvidenceClaim]) -> int:
    rows = [validate_claim(claim).to_dict() for claim in claims]

    if not rows:
        return 0

    with get_connection() as conn:
        pd.DataFrame(rows).to_sql(
            "evidence_claims",
            conn,
            if_exists="append",
            index=False,
        )

    return len(rows)


def main() -> None:
    ensure_claims_table()
    clear_claims_table()

    claims = []
    claims.extend(build_trial_claims())
    claims.extend(build_regulatory_claims())
    claims.extend(build_news_claims())

    inserted = insert_claims(claims)

    print("PSIT -- Evidence Claim Builder")
    print("=" * 52)
    print(f"Claims built: {len(claims)}")
    print(f"Claims inserted: {inserted}")


if __name__ == "__main__":
    main()