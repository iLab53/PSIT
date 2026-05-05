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