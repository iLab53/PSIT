"""
PSIT -- SQLite connection, initialization, and insert helpers.
"""
import sqlite3, json, pathlib
from schema import (
    Trial,
    CREATE_TRIALS,
    CREATE_SOURCE_META,
    CREATE_REGULATORY_SIGNALS,
    CREATE_NEWS_SIGNALS,
    CREATE_VALIDATED_CLAIMS,
)

DB_PATH = pathlib.Path('psit.db')

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(CREATE_TRIALS)
        conn.execute(CREATE_SOURCE_META)
        conn.execute(CREATE_REGULATORY_SIGNALS)
        conn.execute(CREATE_NEWS_SIGNALS)
        conn.execute(CREATE_VALIDATED_CLAIMS)
        conn.commit()
    print('  Database initialized: psit.db')

def upsert_trials(trials: list):
    rows = [(
        t.nct_id, t.brief_title, t.overall_status, t.phase,
        t.sponsor, t.conditions, t.interventions,
        t.start_date, t.primary_completion_date, t.last_update_date,
        t.study_type, t.enrollment, t.source_url, t.pull_timestamp
    ) for t in trials]
    with get_connection() as conn:
        conn.executemany(
            'INSERT OR REPLACE INTO trials VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
            rows
        )
        conn.commit()
    print(f'  Upserted {len(rows)} trials into SQLite.')

def log_source_pull(source_name, source_url, query_params, pull_ts, count):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO source_meta
               (source_name, source_url, query_params, pull_timestamp, record_count)
               VALUES (?,?,?,?,?)""",
            (source_name, source_url, query_params, pull_ts, count)
        )
        conn.commit()

def insert_regulatory_signals(signals: list):
    if not signals:
        print('  No regulatory signals to insert.')
        return
    rows = [(s['source_name'], s['source_url'], s['title'], s['summary'],
             s['published'], s['pull_timestamp'], s['signal_tier']) for s in signals]
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO regulatory_signals
               (source_name, source_url, title, summary, published,
                pull_timestamp, signal_tier) VALUES (?,?,?,?,?,?,?)""",
            rows
        )
        conn.commit()
    print(f'  Inserted {len(rows)} regulatory signals.')

def insert_news_signals(signals: list):
    if not signals:
        print('  No news signals to insert.')
        return
    rows = [(s['source_name'], s['source_url'], s['title'], s['summary'],
             s['published'], s['pull_timestamp'], s['signal_tier']) for s in signals]
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO news_signals
               (source_name, source_url, title, summary, published,
                pull_timestamp, signal_tier) VALUES (?,?,?,?,?,?,?)""",
            rows
        )
        conn.commit()
    print(f'  Inserted {len(rows)} news signals.')

def insert_validated_claims(claims: list) -> None:
    import datetime
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    rows = [(c.claim_text, c.source_url, c.source_name, c.evidence_type,
             c.pull_timestamp, c.nct_id, now) for c in claims]
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO validated_claims
               (claim_text, source_url, source_name, evidence_type,
                pull_timestamp, nct_id, created_at) VALUES (?,?,?,?,?,?,?)""",
            rows
        )
        conn.commit()
    print(f'  Cached {len(rows)} validated claims.')

def load_latest_claims(n: int = 500) -> list:
    """Return the n most recent validated claims as ClaimObject instances."""
    from claim import ClaimObject
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM validated_claims ORDER BY id DESC LIMIT ?",
            (n,)
        ).fetchall()
    return [
        ClaimObject(
            claim_text=r['claim_text'],
            source_url=r['source_url'],
            source_name=r['source_name'],
            evidence_type=r['evidence_type'],
            pull_timestamp=r['pull_timestamp'],
            nct_id=r['nct_id'],
        )
        for r in rows
    ]
