"""
PSIT -- ISPOR 2026 HEOR Intelligence Tab.
Renders the T6 HEOR Outcomes evidence layer in the Streamlit dashboard.
Reads from the ispor_posters table populated by ispor_connector.py.
"""

import sqlite3
import pandas as pd
import streamlit as st

TIER_COLORS = {
    "HIGH":   "🔴",
    "MEDIUM": "🟡",
    "LOW":    "🟢",
}

CATEGORY_LABELS = {
    "EE":  "Economic Evaluation",
    "HTA": "Health Technology Assessment",
    "CO":  "Clinical Outcomes / RWE",
    "RWD": "Real-World Data",
    "MSR": "Methodology / AI-ML",
    "EPH": "Epidemiology",
    "HSD": "Health Services & Delivery",
    "HPR": "Health Policy Research",
    "PCR": "Patient-Centered Research",
    "SA":  "Systematic Analysis",
}


def render_ispor_tab(conn: sqlite3.Connection) -> None:
    st.header("HEOR Intelligence — ISPOR 2026")
    st.caption(
        "Source: ISPOR 2026 Annual Meeting poster presentations | "
        "T6 Evidence Tier — Health Economics & Outcomes Research | "
        "ADC oncology relevance scored by drug, target antigen, and poster category"
    )

    # ── Load data ──────────────────────────────────────────────────────────────
    try:
        df = pd.read_sql_query(
            "SELECT * FROM ispor_posters ORDER BY relevance_tier, category, poster_id",
            conn,
        )
    except Exception:
        st.info(
            "No ISPOR data loaded. Run:\n\n"
            "```\npython ispor_connector.py "
            '--path "C:/Users/kaibo/OneDrive/Desktop/ISPOR"\n```'
        )
        return

    if df.empty:
        st.info("ISPOR table exists but is empty. Run ispor_connector.py to populate.")
        return

    # ── Summary metrics ────────────────────────────────────────────────────────
    total    = len(df)
    high     = len(df[df["relevance_tier"] == "HIGH"])
    med      = len(df[df["relevance_tier"] == "MEDIUM"])
    adc_only = df[df["drug_tags"] != ""]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total HEOR Posters",        total)
    c2.metric("HIGH ADC Relevance",         high)
    c3.metric("MEDIUM Relevance",           med)
    c4.metric("Posters with Drug Tags",     len(adc_only))

    st.divider()

    # ── Sidebar-style filters ──────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        categories = ["All"] + sorted(df["category"].dropna().unique().tolist())
        sel_cat = st.selectbox("Evidence Category", categories, key="ispor_cat")

    with col_b:
        tiers = ["All", "HIGH", "MEDIUM", "LOW"]
        sel_tier = st.selectbox("ADC Relevance Tier", tiers, key="ispor_tier")

    with col_c:
        # Collect all unique drug tags
        all_drugs = set()
        for tags in df["drug_tags"].dropna():
            for d in tags.split(", "):
                if d.strip():
                    all_drugs.add(d.strip())
        drug_options = ["All"] + sorted(all_drugs)
        sel_drug = st.selectbox("Drug / ADC", drug_options, key="ispor_drug")

    # ── Apply filters ──────────────────────────────────────────────────────────
    filtered = df.copy()
    if sel_cat != "All":
        filtered = filtered[filtered["category"] == sel_cat]
    if sel_tier != "All":
        filtered = filtered[filtered["relevance_tier"] == sel_tier]
    if sel_drug != "All":
        filtered = filtered[filtered["drug_tags"].str.contains(sel_drug, na=False)]

    st.caption(f"{len(filtered)} posters shown")

    # ── HIGH relevance spotlight ───────────────────────────────────────────────
    high_df = filtered[filtered["relevance_tier"] == "HIGH"]
    if not high_df.empty:
        with st.expander(f"🔴 HIGH ADC Relevance — {len(high_df)} posters", expanded=True):
            st.caption("Posters citing a specific ADC drug AND a target antigen")
            for _, row in high_df.iterrows():
                cat_label = CATEGORY_LABELS.get(row["category"], row["category"])
                st.markdown(
                    f"**{row['poster_id']}** &nbsp;`{cat_label}`\n\n"
                    f"_{row['title']}_\n\n"
                    f"💊 **Drugs:** {row['drug_tags'] or '—'}  \n"
                    f"🎯 **Targets:** {row['target_tags'] or '—'}"
                )
                if row.get("abstract_text"):
                    with st.expander("View extracted text"):
                        st.text(row["abstract_text"][:800])
                st.divider()

    # ── Full table ─────────────────────────────────────────────────────────────
    with st.expander("All Filtered Posters — Table View", expanded=False):
        display_df = filtered[[
            "poster_id", "category", "evidence_type", "relevance_tier",
            "drug_tags", "target_tags", "title"
        ]].rename(columns={
            "poster_id":      "ID",
            "category":       "Cat",
            "evidence_type":  "Evidence Type",
            "relevance_tier": "ADC Relevance",
            "drug_tags":      "Drugs",
            "target_tags":    "Targets",
            "title":          "Title",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Category breakdown ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("Poster Distribution by Evidence Category")
    cat_counts = (
        filtered.groupby("category")
        .size()
        .reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )
    cat_counts["Category"] = cat_counts["category"].map(
        lambda c: CATEGORY_LABELS.get(c, c)
    )
    st.bar_chart(cat_counts.set_index("Category")["Count"], height=260)

    # ── Drug frequency ─────────────────────────────────────────────────────────
    if not filtered[filtered["drug_tags"] != ""].empty:
        st.subheader("ADC Drug Mentions")
        drug_counts: dict[str, int] = {}
        for tags in filtered["drug_tags"].dropna():
            for d in tags.split(", "):
                if d.strip():
                    drug_counts[d.strip()] = drug_counts.get(d.strip(), 0) + 1
        drug_df = (
            pd.DataFrame(drug_counts.items(), columns=["Drug", "Posters"])
            .sort_values("Posters", ascending=False)
        )
        st.dataframe(drug_df, use_container_width=True, hide_index=True)

    st.caption(
        "T6 Evidence Tier — HEOR/Outcomes | Source: ISPOR 2026 Annual Meeting | "
        "Supplements but does not replace T1–T5 structured clinical evidence. "
        "Poster abstracts represent conference presentations, not peer-reviewed publications."
    )
