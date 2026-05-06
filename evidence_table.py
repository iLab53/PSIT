import streamlit as st
import pandas as pd
from claim import ClaimObject
 
TIER_LABELS = {
    'STRUCTURED_TRIAL': 'T1 - Trial Registry',
    'REGULATORY':       'T2 - Regulatory',
    'NEWS':             'T3 - News Signal',
    'SUMMARY':          'LLM Summary',
}
 
def render_evidence_table(claims: list) -> None:
    if not claims:
        st.info('No validated claims available. Run the pipeline to populate.')
        return
    rows = []
    for c in claims:
        txt = c.claim_text[:140] + ('...' if len(c.claim_text) > 140 else '')
        rows.append({
            'Tier':       TIER_LABELS.get(c.evidence_type, c.evidence_type),
            'Source':     c.source_name,
            'Claim':      txt,
            'NCT ID':     c.nct_id or '-',
            'Pulled':     c.pull_timestamp[:10],
            'Source URL': c.source_url,
        })
    df = pd.DataFrame(rows)
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            'Source URL': st.column_config.LinkColumn('Source URL', width='medium'),
            'Claim':      st.column_config.TextColumn('Claim', width='large'),
        },
    )
    st.caption(f'Total validated claims: {len(claims)}')
    col1, col2, col3, col4 = st.columns(4)
    for col, ev_type, label in [
        (col1, 'STRUCTURED_TRIAL', 'T1 Trial'),
        (col2, 'REGULATORY',       'T2 Regulatory'),
        (col3, 'NEWS',             'T3 News'),
        (col4, 'SUMMARY',          'LLM Summary'),
    ]:
        col.metric(label, sum(1 for c in claims if c.evidence_type == ev_type))
