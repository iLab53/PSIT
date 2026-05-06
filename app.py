"""
PSIT -- Streamlit application.
Day 2: Pipeline Density + Velocity modules.
Design principle: every metric traces to a public source record.
"""
import streamlit as st
import pandas as pd
from narrator import generate_summary
from db import get_connection, insert_validated_claims, load_latest_claims
from analytics import (
    load_trials_df,
    pipeline_density,
    pipeline_velocity,
    differentiation_signals,
    catalyst_calendar,
)
 
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
diff_df = differentiation_signals(df)
cat_df = catalyst_calendar(df)
 
# ── Summary metrics ───────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
c1.metric('Total Registered Trials',   density['total_trials'])
c2.metric('Active Sponsors',           len(density['sponsor_leaderboard']))
c3.metric('Updated in Last 90 Days',   velocity['recent_count'])

# Strategic Summary (validated claims from narrator)
st.header('Strategic Summary')
st.caption(
    'LLM-generated summary of ClinicalTrials.gov structured data. '
    'Every claim passed schema validation and source whitelisting before display.'
)

cached = load_latest_claims(n=6)

if st.button('Regenerate Summary', key='regen'):
    with st.spinner('Generating validated summary...'):
        new_claims = generate_summary(density, row['pull_timestamp'])
        if new_claims:
            insert_validated_claims(new_claims)
            cached = [vars(c) for c in new_claims]
        else:
            st.warning('No validated claims generated. Check narrator logs.')

if cached:
    for item in cached:
        st.markdown(
            f"- {item['claim_text']} "
            f"([{item['source_name']}]({item['source_url']}))",
            unsafe_allow_html=False
        )
else:
    st.info(
        'No summary available. Click Regenerate Summary to generate '
        'a citation-backed strategic overview from the current trial data.'
    )
 
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

st.divider()

# MODULE 3: Differentiation Signals
st.header('Differentiation Signals')
st.caption('Source: ClinicalTrials.gov | Fields absent from the public record show as Not reported')

col_a, col_b = st.columns(2)
with col_a:
    sponsors = ['All'] + sorted(diff_df['sponsor'].unique().tolist())
    sel_sponsor = st.selectbox('Filter by Sponsor', sponsors, key='diff_sponsor')
with col_b:
    phases = ['All'] + sorted(diff_df['phase'].unique().tolist())
    sel_phase = st.selectbox('Filter by Phase', phases, key='diff_phase')

filtered_diff = diff_df.copy()
if sel_sponsor != 'All':
    filtered_diff = filtered_diff[filtered_diff['sponsor'] == sel_sponsor]
if sel_phase != 'All':
    filtered_diff = filtered_diff[filtered_diff['phase'] == sel_phase]

st.dataframe(
    filtered_diff.rename(columns={
        'nct_id': 'NCT ID',
        'brief_title': 'Trial Title',
        'overall_status': 'Status',
        'phase': 'Phase',
        'sponsor': 'Sponsor',
        'primary_condition': 'Primary Condition',
        'primary_intervention': 'Primary Intervention',
        'start_date': 'Start',
        'primary_completion_date': 'Primary Completion',
        'source_url': 'Source',
    }),
    use_container_width=True
)
st.caption(f'{len(filtered_diff)} trials shown')

st.divider()

# MODULE 4: Catalyst Calendar
st.header('Catalyst Calendar')
st.caption('Upcoming primary completion dates (next 18 months) | Source: ClinicalTrials.gov')

near_count = len(cat_df[cat_df['horizon'].str.startswith('Near')])
c1, c2, c3 = st.columns(3)
c1.metric('Total Upcoming Readouts (18 mo)', len(cat_df))
c2.metric('Near-term (< 6 months)', near_count)
c3.metric('Mid-term (6-12 months)', len(cat_df[cat_df['horizon'].str.startswith('Mid')]))

horizons = ['All'] + sorted(cat_df['horizon'].unique().tolist())
sel_hz = st.selectbox('Filter by Horizon', horizons, key='cat_hz')
filtered_cat = cat_df if sel_hz == 'All' else cat_df[cat_df['horizon'] == sel_hz]

st.dataframe(
    filtered_cat.rename(columns={
        'nct_id': 'NCT ID',
        'brief_title': 'Trial Title',
        'sponsor': 'Sponsor',
        'phase': 'Phase',
        'overall_status': 'Status',
        'primary_completion_date': 'Primary Completion',
        'horizon': 'Horizon',
        'source_url': 'Source',
    }),
    use_container_width=True
)

st.divider()

# OVERLAY: Regulatory Signals (Tier 2)
with st.expander('Regulatory Signals -- FDA / EMA  (Tier 2 Overlay)', expanded=False):
    st.caption(
        'Sources: FDA press releases, EMA news RSS | Filtered for ADC-oncology relevance | '
        'Tier 2 overlay -- supplements but does not replace structured trial data'
    )
    with get_connection() as conn:
        reg_df = pd.read_sql_query(
    """
    SELECT source_name, title, summary, published, source_url, signal_tier
    FROM regulatory_signals
    ORDER BY id DESC
    LIMIT 50
    """,
    conn
)
    if reg_df.empty:
        st.info('No regulatory signals loaded. Run: python overlay_refresh.py')
    else:
        st.dataframe(reg_df, use_container_width=True)
        st.caption(f'{len(reg_df)} regulatory signals shown')

# OVERLAY: News Signals (Tier 3)
with st.expander('News Signals -- Endpoints / STAT  (Tier 3 Overlay)', expanded=False):
    st.caption(
        'Sources: Endpoints News, STAT News (public RSS) | Filtered for ADC-oncology relevance | '
        'Tier 3 overlay -- contextual signal only, not an analytical claim'
    )
    with get_connection() as conn:
        news_df = pd.read_sql_query(
    """
    SELECT source_name, title, summary, published, source_url, signal_tier
    FROM news_signals
    ORDER BY id DESC
    LIMIT 50
    """,
    conn
    )
    if news_df.empty:
        st.info('No news signals loaded. Run: python overlay_refresh.py')
    else:
        st.dataframe(news_df, use_container_width=True)
        st.caption(f'{len(news_df)} news signals shown')
st.divider()

# MODULE 7: Evidence Claims
st.header("Evidence Claims")
st.caption(
    "Citation validation layer | Claims are accepted only if they include a whitelisted source URL"
)

with get_connection() as conn:
    evidence_df = pd.read_sql_query(
        """
        SELECT claim_type, source_tier, source_name, claim_text,
               evidence_date, source_url, status, validation_message
        FROM evidence_claims
        ORDER BY id DESC
        LIMIT 100
        """,
        conn,
    )

if evidence_df.empty:
    st.info("No evidence claims have been built yet. Run: python build_claims.py")
else:
    status_filter = st.selectbox(
        "Filter by Validation Status",
        ["All"] + sorted(evidence_df["status"].dropna().unique().tolist()),
        key="evidence_status",
    )

    filtered_evidence = evidence_df.copy()
    if status_filter != "All":
        filtered_evidence = filtered_evidence[filtered_evidence["status"] == status_filter]

    valid_count = len(evidence_df[evidence_df["status"] == "validated"])
    rejected_count = len(evidence_df[evidence_df["status"] == "rejected"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Evidence Claims", len(evidence_df))
    c2.metric("Validated", valid_count)
    c3.metric("Rejected", rejected_count)

    st.dataframe(
        filtered_evidence.rename(columns={
            "claim_type": "Claim Type",
            "source_tier": "Source Tier",
            "source_name": "Source",
            "claim_text": "Claim",
            "evidence_date": "Evidence Date",
            "source_url": "Source URL",
            "status": "Validation Status",
            "validation_message": "Validation Message",
        }),
        width="stretch",
    )
# Add to imports
from evidence_table import render_evidence_table
from db import load_latest_claims
from datetime import datetime
 
# Update tab list
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    'Overview', 'Signals', 'Regulatory', 'Summary', 'Evidence'
])
 
# New Evidence tab block
with tab5:
    st.subheader('Evidence Table -- All Validated Claims')
    claims = load_latest_claims(conn)
    render_evidence_table(claims)
    if claims:
        df_export = pd.DataFrame([{
            'tier':   c.evidence_type,   'source': c.source_name,
            'claim':  c.claim_text,       'url':    c.source_url,
            'nct_id': c.nct_id or '',     'pulled': c.pull_timestamp,
        } for c in claims])
        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        today = datetime.now().strftime('%Y%m%d')
        st.download_button(
            label='Export Evidence to CSV',
            data=csv_bytes,
            file_name=f'psit_evidence_{today}.csv',
            mime='text/csv',
            use_container_width=True,
        )

