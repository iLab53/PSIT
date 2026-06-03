"""
PSIT -- Company Archetype Tab.
Displays HEOR strategy archetypes derived from ISPOR 2026 poster analysis.
Reads from the company_profiles table built by build_archetypes.py.
"""

import sqlite3
import pandas as pd
import streamlit as st

ARCHETYPE_META = {
    "Payer-Ready": {
        "icon":  "💰",
        "color": "#1a6b3c",
        "badge": "#d4edda",
        "desc":  "Heavy Economic Evaluation + HTA. Building reimbursement dossier. "
                 "Expect regulatory submission or launch within 12-18 months.",
    },
    "RWE Builder": {
        "icon":  "📊",
        "color": "#155a8a",
        "badge": "#cce5ff",
        "desc":  "Heavy Real-World Data + Clinical Outcomes. Post-approval evidence generation. "
                 "Seeking label expansion or broader payer coverage.",
    },
    "Disease Burden Establisher": {
        "icon":  "🏥",
        "color": "#7b3f00",
        "badge": "#fff3cd",
        "desc":  "Heavy Epidemiology + Patient-Centered Research. Framing unmet need "
                 "pre-approval to prime payers and policy makers.",
    },
    "Methods Innovator": {
        "icon":  "🔬",
        "color": "#4a235a",
        "badge": "#e8d5f5",
        "desc":  "Heavy Methodology. Investing in HEOR infrastructure and methodological "
                 "leadership. Complex submission preparation.",
    },
    "Systematic Evidence Aggregator": {
        "icon":  "📋",
        "color": "#5d4037",
        "badge": "#efebe9",
        "desc":  "Heavy Systematic Analysis. Building comparative effectiveness arguments "
                 "through indirect treatment comparisons and network meta-analyses.",
    },
    "Balanced Generalist": {
        "icon":  "⚖️",
        "color": "#263238",
        "badge": "#eceff1",
        "desc":  "Broad portfolio across evidence categories. Mature, diversified HEOR function.",
    },
    "Minimal Presenter": {
        "icon":  "📌",
        "color": "#616161",
        "badge": "#f5f5f5",
        "desc":  "Fewer than 3 posters. Limited HEOR footprint or primarily academic partnerships.",
    },
    "Academic/Unaffiliated": {
        "icon":  "🎓",
        "color": "#37474f",
        "badge": "#f5f5f5",
        "desc":  "Academic institutions, independent researchers, or unaffiliated presenters.",
    },
}


def _load_profiles(conn: sqlite3.Connection) -> pd.DataFrame:
    try:
        return pd.read_sql_query(
            "SELECT * FROM company_profiles ORDER BY total_posters DESC",
            conn,
        )
    except Exception:
        return pd.DataFrame()


def render_archetype_tab(conn: sqlite3.Connection) -> None:
    st.header("Company HEOR Archetypes — ISPOR 2026")
    st.caption(
        "Source: ISPOR 2026 Annual Meeting — all 1,391 posters | "
        "Archetypes derived from poster category mix per sponsoring organization | "
        "T6 Competitive Intelligence Layer"
    )

    df = _load_profiles(conn)

    if df.empty:
        st.info(
            "No archetype data loaded. Run:\n\n"
            "```\npython build_archetypes.py "
            '--path "C:/Users/kaibo/OneDrive/Desktop/ISPOR"\n```'
        )
        return

    # ── Summary metrics ────────────────────────────────────────────────────────
    total_companies = len(df[df["company_name"] != "Academic/Unaffiliated"])
    total_posters   = df["total_posters"].sum()
    pharma_only     = df[~df["company_name"].isin(["Academic/Unaffiliated"])]
    payer_ready     = len(df[df["archetype"] == "Payer-Ready"])
    onc_companies   = len(df[df["oncology_count"] > 0])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Companies Identified",   total_companies)
    c2.metric("Total Posters Mapped",   int(total_posters))
    c3.metric("Payer-Ready Companies",  payer_ready)
    c4.metric("With Oncology Posters",  onc_companies)

    st.divider()

    # ── Archetype filter ───────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        archetypes = ["All"] + sorted(df["archetype"].dropna().unique().tolist())
        sel_arch = st.selectbox("Filter by Archetype", archetypes, key="arch_filter")
    with col_b:
        onc_only = st.checkbox("Oncology posters only", value=False, key="arch_onc")

    filtered = df.copy()
    if sel_arch != "All":
        filtered = filtered[filtered["archetype"] == sel_arch]
    if onc_only:
        filtered = filtered[filtered["oncology_count"] > 0]
    filtered = filtered[filtered["company_name"] != "Academic/Unaffiliated"]

    st.caption(f"{len(filtered)} companies shown")

    # ── Archetype legend ───────────────────────────────────────────────────────
    with st.expander("Archetype Definitions", expanded=False):
        for arch, meta in ARCHETYPE_META.items():
            if arch == "Academic/Unaffiliated":
                continue
            st.markdown(f"**{meta['icon']} {arch}** — {meta['desc']}")

    st.divider()

    # ── Company cards ──────────────────────────────────────────────────────────
    for _, row in filtered.iterrows():
        arch = row.get("archetype", "Unknown")
        meta = ARCHETYPE_META.get(arch, {"icon": "•", "color": "#333", "badge": "#eee", "desc": ""})

        with st.expander(
            f"{meta['icon']} **{row['company_name']}** — {arch} "
            f"({int(row['total_posters'])} posters)",
            expanded=False,
        ):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Archetype Rationale**")
                st.markdown(row.get("archetype_rationale", "—"))

                # Category breakdown bar
                cat_cols = {
                    "EE": "Economic Eval",
                    "HTA": "HTA",
                    "CO": "Clinical Outcomes",
                    "RWD": "Real-World Data",
                    "MSR": "Methodology",
                    "EPH": "Epidemiology",
                    "PCR": "Patient Research",
                    "SA": "Systematic Analysis",
                    "HSD": "Health Services",
                    "HPR": "Health Policy",
                }
                cat_data = {
                    label: int(row.get(f"{code.lower()}_count", 0))
                    for code, label in cat_cols.items()
                    if int(row.get(f"{code.lower()}_count", 0)) > 0
                }
                if cat_data:
                    cat_df = pd.DataFrame(
                        cat_data.items(), columns=["Category", "Posters"]
                    ).sort_values("Posters", ascending=False)
                    st.bar_chart(cat_df.set_index("Category"), height=180)

            with col2:
                st.metric("Total Posters",    int(row["total_posters"]))
                st.metric("Oncology Posters", int(row.get("oncology_count", 0)))
                total = int(row["total_posters"])
                ee_hta = int(row.get("ee_count", 0)) + int(row.get("hta_count", 0))
                if total > 0:
                    st.metric("Payer Evidence %",
                              f"{round(ee_hta/total*100)}%")

    # ── Archetype distribution chart ───────────────────────────────────────────
    st.divider()
    st.subheader("Archetype Distribution")
    arch_counts = (
        filtered.groupby("archetype")
        .size()
        .reset_index(name="Companies")
        .sort_values("Companies", ascending=False)
    )
    st.bar_chart(arch_counts.set_index("archetype"), height=280)

    # ── Poster volume leaderboard ──────────────────────────────────────────────
    st.subheader("Poster Volume Leaderboard")
    leaderboard = filtered[[
        "company_name", "total_posters", "oncology_count", "archetype"
    ]].rename(columns={
        "company_name":    "Company",
        "total_posters":   "Total Posters",
        "oncology_count":  "Oncology Posters",
        "archetype":       "HEOR Archetype",
    }).head(25)
    st.dataframe(leaderboard, use_container_width=True, hide_index=True)

    st.caption(
        "Company detection based on keyword matching of author affiliations and poster text. "
        "Multi-author posters may be attributed to multiple organizations. "
        "Academic institutions excluded from archetype analysis. "
        "Source: ISPOR 2026 Annual Meeting."
    )
