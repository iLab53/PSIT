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


def differentiation_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Structured differentiation table for competing ADC trials.
    Fields absent from the public record display as 'Not reported'.
    No fields are inferred or imputed."""
    COLS = [
        'nct_id', 'brief_title', 'overall_status', 'phase',
        'sponsor', 'conditions', 'interventions',
        'start_date', 'primary_completion_date', 'source_url'
    ]

    out = df[COLS].copy()

    out['primary_condition'] = out['conditions'].apply(
    lambda x: str(x).split('|')[0].strip() if pd.notna(x) and str(x).strip() else 'Not reported'
)

    out['primary_intervention'] = out['interventions'].apply(
    lambda x: str(x).split('|')[0].strip() if pd.notna(x) and str(x).strip() else 'Not reported'
)

    for col in ['phase', 'sponsor', 'start_date', 'primary_completion_date']:
        out[col] = out[col].replace('', 'Not reported').fillna('Not reported')

    return (
        out[['nct_id', 'brief_title', 'overall_status', 'phase',
             'sponsor', 'primary_condition', 'primary_intervention',
             'start_date', 'primary_completion_date', 'source_url']]
        .sort_values(['sponsor', 'phase'])
        .reset_index(drop=True)
    )


def catalyst_calendar(df: pd.DataFrame, months_ahead: int = 18) -> pd.DataFrame:
    """Upcoming primary completion dates sorted forward in time.
    Bucketed by horizon. Each row links to its source trial record.
    Trials beyond months_ahead or with missing dates are excluded."""
    df = df.copy()
    df['pcd'] = pd.to_datetime(df['primary_completion_date'], errors='coerce')

    today = pd.Timestamp.now()
    cutoff = today + pd.DateOffset(months=months_ahead)
    upcoming = df[(df['pcd'] >= today) & (df['pcd'] <= cutoff)].copy()
    upcoming = upcoming.sort_values('pcd')

    def _horizon(dt):
        if pd.isna(dt):
            return 'Unknown'
        months = (dt.year - today.year) * 12 + (dt.month - today.month)
        if months <= 6:
            return 'Near-term  (< 6 months)'
        elif months <= 12:
            return 'Mid-term   (6-12 months)'
        else:
            return 'Long-term  (12-18 months)'

    upcoming['horizon'] = upcoming['pcd'].apply(_horizon)

    return upcoming[[
        'nct_id', 'brief_title', 'sponsor', 'phase',
        'overall_status', 'primary_completion_date', 'horizon', 'source_url'
    ]].reset_index(drop=True)
