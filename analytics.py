"""
PSIT -- Analytics layer.
All metrics derived from SQLite trial records.
No LLM calls. No HTTP requests. No unsupported claims.
"""
import pandas as pd
from db import get_connection
 
def load_trials_df() -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query('SELECT * FROM trials', conn)
 
def pipeline_density(df: pd.DataFrame) -> dict:
    """Trial counts and breakdowns for the Pipeline Density module."""
    return {
        'total_trials':       len(df),
        'by_phase':           df['phase'].value_counts().to_dict(),
        'by_status':          df['overall_status'].value_counts().to_dict(),
        'sponsor_leaderboard': df['sponsor'].value_counts().head(15).to_dict(),
    }
 
def pipeline_velocity(df: pd.DataFrame) -> dict:
    """Trial start trends and recent activity."""
    df = df.copy()
 
    # New starts by year
    df['start_year'] = pd.to_datetime(df['start_date'], errors='coerce').dt.year
    starts_by_year = (
        df.groupby('start_year').size()
        .dropna()
        .sort_index()
        .to_dict()
    )
 
    # Recent activity: updated in last 90 days
    df['last_update_dt'] = pd.to_datetime(df['last_update_date'], errors='coerce')
    cutoff = pd.Timestamp.now(tz='UTC').tz_localize(None) - pd.Timedelta(days=90)
    recent = (
        df[df['last_update_dt'] >= cutoff]
        .sort_values('last_update_dt', ascending=False)
    )
 
    return {
        'starts_by_year': {
            int(k): int(v) for k, v in starts_by_year.items() if pd.notna(k)
        },
        'recent_count': len(recent),
        'recent_trials': recent[[
            'nct_id', 'brief_title', 'overall_status',
            'sponsor', 'last_update_date', 'source_url'
        ]].head(25).to_dict('records'),
    }
