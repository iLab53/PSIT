"""
PSIT -- Populate validated_claims from trials table.
Converts structured trial records into ClaimObject instances
and inserts them into the validated_claims table.
"""
from db import get_connection, insert_validated_claims
from claim import ClaimObject


def main():
    with get_connection() as conn:
        rows = conn.execute('SELECT * FROM trials').fetchall()

    claims = []
    for row in rows:
        nct_id   = row['nct_id']   or ''
        title    = row['brief_title'] or 'Untitled'
        sponsor  = row['sponsor']  or 'Not reported'
        phase    = row['phase']    or 'Not reported'
        status   = row['overall_status'] or 'Not reported'
        src_url  = row['source_url'] or ''
        pull_ts  = row['pull_timestamp'] or ''

        claim_text = (
            f"{nct_id}: {title} — sponsor: {sponsor}, "
            f"phase: {phase}, status: {status}."
        )

        claims.append(ClaimObject(
            claim_text=claim_text,
            source_url=src_url,
            source_name='ClinicalTrials.gov',
            evidence_type='STRUCTURED_TRIAL',
            pull_timestamp=pull_ts,
            nct_id=nct_id,
        ))

    insert_validated_claims(claims)
    print(f'PSIT -- Validated Claims Populated')
    print(f'  Inserted {len(claims)} claims into validated_claims.')


if __name__ == '__main__':
    main()
