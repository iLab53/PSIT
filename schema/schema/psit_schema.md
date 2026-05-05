"""
PSIT -- Trial schema and SQLite table definitions.
source_url is non-nullable: every trial must trace to a public source.
"""
from dataclasses import dataclass
from typing import Optional
 
@dataclass
class Trial:
    nct_id:                  str
    brief_title:             str
    overall_status:          str
    phase:                   str
    sponsor:                 str
    conditions:              str          # pipe-separated
    interventions:           str          # pipe-separated
    start_date:              Optional[str]
    primary_completion_date: Optional[str]
    last_update_date:        Optional[str]
    study_type:              str
    enrollment:              Optional[int]
    source_url:              str          # required -- no claim without URL
    pull_timestamp:          str          # ISO-8601 UTC
 
CREATE_TRIALS = '''
CREATE TABLE IF NOT EXISTS trials (
    nct_id                  TEXT PRIMARY KEY,
    brief_title             TEXT,
    overall_status          TEXT,
    phase                   TEXT,
    sponsor                 TEXT,
    conditions              TEXT,
    interventions           TEXT,
    start_date              TEXT,
    primary_completion_date TEXT,
    last_update_date        TEXT,
    study_type              TEXT,
    enrollment              INTEGER,
    source_url              TEXT NOT NULL,
    pull_timestamp          TEXT NOT NULL
);
'''
 
CREATE_SOURCE_META = '''
CREATE TABLE IF NOT EXISTS source_meta (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name    TEXT NOT NULL,
    source_url     TEXT NOT NULL,
    query_params   TEXT,
    pull_timestamp TEXT NOT NULL,
