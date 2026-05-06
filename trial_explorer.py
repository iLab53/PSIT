"""
Trial Explorer -- SQLite-backed trial metadata lookup and Streamlit renderer.

get_trial_by_nct_id(conn, nct_id) -> dict | None
render_trial_explorer(conn, nct_ids)   -> None  (renders expanders in-place)

Design: reads from the 'trials' table populated by the CT.gov fetcher.
Missing NCT IDs show a non-blocking st.warning() rather than crashing.
"""
import streamlit as st


def get_trial_by_nct_id(conn, nct_id: str):
    """Return a column->value dict for the given NCT ID, or None if not found."""
    cur = conn.execute(
        'SELECT * FROM trials WHERE nct_id = ? LIMIT 1', (nct_id,)
    )
    row = cur.fetchone()
    if row is None:
        return None
    cols = [d[0] for d in cur.description]
    return dict(zip(cols, row))


def render_trial_explorer(conn, nct_ids: list) -> None:
    """
    Render one st.expander per unique NCT ID in nct_ids.

    Each expander shows:
      - Phase and Status as column metrics
      - Sponsor, Condition, Intervention as labelled lines
      - Start date and Completion date

    If the NCT ID is not in the trials table, shows st.warning() inside
    the expander rather than raising a KeyError.
    """
    # Deduplicate while preserving order
    seen: list[str] = []
    for nid in nct_ids:
        if nid and nid not in seen:
            seen.append(nid)

    if not seen:
        return

    st.subheader('Trial Explorer')

    for nct_id in seen:
        trial = get_trial_by_nct_id(conn, nct_id)

        if trial:
            status = trial.get('overall_status') or trial.get('status', 'unknown')
            label = f'{nct_id} — {status}'
        else:
            label = nct_id

        with st.expander(label):
            if trial is None:
                st.warning(
                    'Trial metadata not cached — run pipeline to refresh.'
                )
            else:
                c1, c2 = st.columns(2)
                c1.metric('Phase',  trial.get('phase', '-') or '-')
                c2.metric('Status', trial.get('overall_status') or trial.get('status', '-') or '-')

                sponsor     = trial.get('sponsor', '-') or '-'
                condition   = trial.get('primary_condition') or trial.get('condition', '-') or '-'
                intervention = (
                    trial.get('primary_intervention')
                    or trial.get('intervention', '-')
                    or '-'
                )
                start_date      = trial.get('start_date', '-') or '-'
                completion_date = (
                    trial.get('primary_completion_date')
                    or trial.get('completion_date', '-')
                    or '-'
                )

                st.write(f'**Sponsor:** {sponsor}')
                st.write(f'**Condition:** {condition}')
                st.write(f'**Intervention:** {intervention}')
                st.write(f'**Start:** {start_date} | **Completion:** {completion_date}')
