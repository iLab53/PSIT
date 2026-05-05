"""
PSIT -- Streamlit application.
Day 2: Pipeline Density + Velocity modules.
Design principle: every metric traces to a public source record.
"""
import streamlit as st
import pandas as pd
from db import get_connection
from analytics import load_trials_df, pipeline_density, pipeline_velocity
 
st.set_page_config(
    page_title='Pharma Strategic Intelligence | ADC Oncology',
    page_icon='🔬',
    layout='wide'
)
 
# ── Header ────────────────────────────────────────────────────────────────
st.title('Pharmaceutical Strategic Intelligence Tool')
st.markdown('**Therapeutic Area:** Antibody-Drug Conjugates (ADCs) in Oncology')
 
# ── Scope disclaimer ──────────────────────────────────────────────────────
st.info(
    '**Scope:** This dashboard reflects publicly registered clinical trials '
    'from ClinicalTrials.gov. It does not include proprietary pipeline data, '
    'revenue forecasts, or investment recommendations. '
    'Every displayed metric links to a verifiable public source.'
)
 
# ── Data freshness guard ──────────────────────────────────────────────────
with get_connection() as conn:
    row = conn.execute(
        'SELECT pull_timestamp, record_count FROM source_meta'
        ' ORDER BY id DESC LIMIT 1'
    ).fetchone()
 
if not row:
    st.warning('No data loaded. Run psit_hello.py first.')
    st.stop()
 
st.caption(
    f'Data last refreshed: {row["pull_timestamp"]} | '
    f'{row["record_count"]} trials loaded from ClinicalTrials.gov'
)
 
# ── Load data ─────────────────────────────────────────────────────────────
df      = load_trials_df()
density = pipeline_density(df)
velocity = pipeline_velocity(df)
 
# ── Summary metrics ───────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric('Total Registered Trials',   density['total_trials'])
c2.metric('Active Sponsors',           len(density['sponsor_leaderboard']))
c3.metric('Updated in Last 90 Days',   velocity['recent_count'])
 
st.divider()
 
# ── MODULE 1: Pipeline Density ────────────────────────────────────────────
st.header('Pipeline Density')
st.caption('Source: ClinicalTrials.gov | Trials matching: antibody-drug conjugate + oncology conditions')
 
st.subheader('Sponsor Leaderboard')
sponsor_df = (
    pd.DataFrame(density['sponsor_leaderboard'].items(), columns=['Sponsor', 'Trials'])
    .sort_values('Trials', ascending=False)
)
st.bar_chart(sponsor_df.set_index('Sponsor'), height=320)
 
col_l, col_r = st.columns(2)
with col_l:
    st.subheader('Trials by Phase')
    phase_df = pd.DataFrame(density['by_phase'].items(), columns=['Phase','Count'])
    st.bar_chart(phase_df.set_index('Phase'), height=260)
 
with col_r:
    st.subheader('Trials by Status')
    status_df = pd.DataFrame(density['by_status'].items(), columns=['Status','Count'])
    st.bar_chart(status_df.set_index('Status'), height=260)
 
st.divider()
 
# ── MODULE 2: Pipeline Velocity ───────────────────────────────────────────
st.header('Pipeline Velocity')
st.caption('Based on trial start dates and sponsor update timestamps from ClinicalTrials.gov')
 
st.subheader('New Trial Starts by Year')
year_df = (
    pd.DataFrame(velocity['starts_by_year'].items(), columns=['Year','Trials'])
    .sort_values('Year')
)
st.bar_chart(year_df.set_index('Year'), height=260)
 
st.subheader(f'Recently Updated Trials (last 90 days)')
recent = velocity['recent_trials']
if recent:
    recent_df = pd.DataFrame(recent)
    recent_df['NCT Link'] = recent_df['source_url'].apply(
        lambda u: f'[{u.split("/")[-1]}]({u})'
    )
    st.dataframe(
        recent_df[['brief_title','overall_status','sponsor','last_update_date','NCT Link']]
        .rename(columns={
            'brief_title':   'Trial Title',
            'overall_status':'Status',
            'sponsor':       'Sponsor',
            'last_update_date': 'Last Updated',
        }),
        use_container_width=True
    )
else:
    st.info('No trials updated in the last 90 days.')
