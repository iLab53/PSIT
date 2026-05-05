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
        conn.commit()
    print('  Database initialized: psit.db')

def upsert_trials(trials: list[Trial]):
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

def log_source_pull(
    source_name: str, source_url: str,
    query_params: str, pull_ts: str, count: int
):
    with get_connection() as conn:
        conn.execute(
            '''INSERT INTO source_meta
               (source_name, source_url, query_params, pull_timestamp, record_count)
               VALUES (?,?,?,?,?)''',
            (source_name, source_url, query_params, pull_ts, count)
        )
        conn.commit()


def insert_regulatory_signals(signals: list[dict]):
    if not signals:
        print('  No regulatory signals to insert.')
        return

    rows = [(
        s['source_name'],
        s['source_url'],
        s['title'],
        s['summary'],
        s['published'],
        s['pull_timestamp'],
        s['signal_tier'],
    ) for s in signals]

    with get_connection() as conn:
        conn.executemany(
            '''INSERT INTO regulatory_signals
               (source_name, source_url, title, summary, published,
                pull_timestamp, signal_tier) VALUES (?,?,?,?,?,?,?)''',
            rows
        )
        conn.commit()
    print(f'  Inserted {len(rows)} regulatory signals.')


def insert_news_signals(signals: list[dict]):
    if not signals:
        print('  No news signals to insert.')
        return

    rows = [(
        s['source_name'],
        s['source_url'],
        s['title'],
        s['summary'],
        s['published'],
        s['pull_timestamp'],
        s['signal_tier'],
    ) for s in signals]

    with get_connection() as conn:
        conn.executemany(
            '''INSERT INTO news_signals
               (source_name, source_url, title, summary, published,
                pull_timestamp, signal_tier) VALUES (?,?,?,?,?,?,?)''',
            rows
        )
        conn.commit()
    print(f'  Inserted {len(rows)} news signals.')
