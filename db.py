"""
PSIT -- SQLite connection, initialization, and insert helpers.
"""
import sqlite3, json, pathlib
from models import Trial

CREATE_TRIALS = """
CREATE TABLE IF NOT EXISTS trials (
    nct_id TEXT PRIMARY KEY,
    brief_title TEXT,
    overall_status TEXT,
    phase TEXT,
    sponsor TEXT,
    conditions TEXT,
    interventions TEXT,
    start_date TEXT,
    primary_completion_date TEXT,
    last_update_date TEXT,
    study_type TEXT,
    enrollment TEXT,
    source_url TEXT,
    pull_timestamp TEXT
)"""

CREATE_SOURCE_META = """
CREATE TABLE IF NOT EXISTS source_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_url TEXT,
    query_params TEXT,
    pull_timestamp TEXT,
    record_count INTEGER
)"""

DB_PATH = pathlib.Path('psit.db')

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute(CREATE_TRIALS)
        conn.execute(CREATE_SOURCE_META)
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