from dataclasses import dataclass


@dataclass
class Trial:
    nct_id: str
    brief_title: str
    overall_status: str
    phase: str
    sponsor: str
    conditions: str
    interventions: str
    start_date: str
    primary_completion_date: str
    last_update_date: str
    study_type: str
    enrollment: str
    source_url: str
    pull_timestamp: str


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

CREATE_REGULATORY_SIGNALS = """
CREATE TABLE IF NOT EXISTS regulatory_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    published TEXT,
    pull_timestamp TEXT NOT NULL,
    signal_tier TEXT DEFAULT 'TIER_2'
)"""

CREATE_NEWS_SIGNALS = """
CREATE TABLE IF NOT EXISTS news_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    published TEXT,
    pull_timestamp TEXT NOT NULL,
    signal_tier TEXT DEFAULT 'TIER_3'
)"""
