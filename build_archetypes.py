"""
PSIT -- Company Archetype Builder.
Processes ALL ISPOR 2026 posters (not just oncology subset),
extracts company affiliations, aggregates category mix per company,
and classifies each company into a HEOR strategy archetype.

Run AFTER ispor_connector.py:
    python build_archetypes.py --path "C:/Users/kaibo/OneDrive/Desktop/ISPOR"

Archetypes:
  Payer-Ready          -- Heavy EE + HTA: building reimbursement dossier
  RWE Builder          -- Heavy RWD + CO: post-approval evidence generation
  Disease Burden Est.  -- Heavy EPH + PCR: pre-approval unmet need framing
  Methods Innovator    -- Heavy MSR: investing in HEOR methodology
  Systematic Aggregator-- Heavy SA: building comparative effectiveness case
  Balanced Generalist  -- Broad portfolio across categories
  Minimal Presenter    -- Fewer than 3 posters; limited HEOR footprint
"""

import argparse
import pathlib
import re
import sqlite3
from datetime import datetime, timezone

try:
    import pdfplumber
except ImportError:
    raise ImportError("Run: pip install pdfplumber")

# ── Database ───────────────────────────────────────────────────────────────────

DB_PATH = pathlib.Path("psit.db")

CREATE_COMPANY_PROFILES = """
CREATE TABLE IF NOT EXISTS company_profiles (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name        TEXT NOT NULL UNIQUE,
    total_posters       INTEGER DEFAULT 0,
    ee_count            INTEGER DEFAULT 0,
    hta_count           INTEGER DEFAULT 0,
    co_count            INTEGER DEFAULT 0,
    rwd_count           INTEGER DEFAULT 0,
    msr_count           INTEGER DEFAULT 0,
    eph_count           INTEGER DEFAULT 0,
    hsd_count           INTEGER DEFAULT 0,
    hpr_count           INTEGER DEFAULT 0,
    pcr_count           INTEGER DEFAULT 0,
    sa_count            INTEGER DEFAULT 0,
    other_count         INTEGER DEFAULT 0,
    oncology_count      INTEGER DEFAULT 0,
    archetype           TEXT,
    archetype_rationale TEXT,
    poster_ids          TEXT,
    pull_timestamp      TEXT
)
"""

CREATE_POSTER_COMPANIES = """
CREATE TABLE IF NOT EXISTS poster_companies (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    poster_id   TEXT,
    category    TEXT,
    title       TEXT,
    company     TEXT,
    is_oncology INTEGER DEFAULT 0
)
"""

# ── Company name registry ──────────────────────────────────────────────────────
# keyword (lowercase) → canonical name
PHARMA_COMPANIES = {
    # Big Pharma
    "astrazeneca":              "AstraZeneca",
    "daiichi sankyo":           "Daiichi Sankyo",
    "pfizer":                   "Pfizer",
    "roche":                    "Roche",
    "genentech":                "Roche/Genentech",
    "hoffmann-la roche":        "Roche",
    "novartis":                 "Novartis",
    "bristol myers squibb":     "Bristol Myers Squibb",
    "bristol-myers squibb":     "Bristol Myers Squibb",
    "bms":                      "Bristol Myers Squibb",
    "merck & co":               "Merck",
    "merck sharp":              "Merck",
    "msd":                      "Merck/MSD",
    "johnson & johnson":        "Johnson & Johnson",
    "janssen":                  "J&J/Janssen",
    "abbvie":                   "AbbVie",
    "eli lilly":                "Eli Lilly",
    "lilly":                    "Eli Lilly",
    "sanofi":                   "Sanofi",
    "gsk":                      "GSK",
    "glaxosmithkline":          "GSK",
    "amgen":                    "Amgen",
    "gilead":                   "Gilead Sciences",
    "regeneron":                "Regeneron",
    "biogen":                   "Biogen",
    "bayer":                    "Bayer",
    "boehringer ingelheim":     "Boehringer Ingelheim",
    "takeda":                   "Takeda",
    "astellas":                 "Astellas",
    "eisai":                    "Eisai",
    "novo nordisk":             "Novo Nordisk",
    "vertex":                   "Vertex Pharmaceuticals",
    "moderna":                  "Moderna",
    "biontec":                  "BioNTech",
    "shire":                    "Takeda/Shire",
    "alexion":                  "AstraZeneca/Alexion",
    "horizon":                  "Horizon Therapeutics",
    "incyte":                   "Incyte",
    "exelixis":                 "Exelixis",
    "blueprint medicines":      "Blueprint Medicines",
    "mirati":                   "Mirati Therapeutics",
    "iovance":                  "Iovance",
    "macrogenics":              "MacroGenics",
    "seagen":                   "Seagen",
    "immunogen":                "ImmunoGen",
    "adc therapeutics":         "ADC Therapeutics",
    "mersana":                  "Mersana",
    "sutro":                    "Sutro Biopharma",
    "zymeworks":                "Zymeworks",
    "elevation oncology":       "Elevation Oncology",
    "revolution medicines":     "Revolution Medicines",
    "relay therapeutics":       "Relay Therapeutics",
    "turning point":            "Turning Point Therapeutics",
    "nuvation":                 "Nuvation Bio",
    "inhibrx":                  "Inhibrx",
    "bolt biotherapeutics":     "Bolt Biotherapeutics",
    "agenus":                   "Agenus",
    "alkermes":                 "Alkermes",
    "jazz pharmaceuticals":     "Jazz Pharmaceuticals",
    "ultragenyx":               "Ultragenyx",
    "biomarin":                 "BioMarin",
    "sarepta":                  "Sarepta Therapeutics",
    "ionis":                    "Ionis Pharmaceuticals",
    "alnylam":                  "Alnylam Pharmaceuticals",
    "regeneron":                "Regeneron",
    "ucb":                      "UCB",
    "ipsen":                    "Ipsen",
    "menarini":                 "Menarini",
    "chiesi":                   "Chiesi",
    "recordati":                "Recordati",
    "lundbeck":                 "Lundbeck",
    "ferring":                  "Ferring Pharmaceuticals",
    "otsuka":                   "Otsuka",
    "dova":                     "Dova Pharmaceuticals",
    "actelion":                 "Actelion/J&J",
    # CROs / HEOR Consultancies
    "iqvia":                    "IQVIA",
    "parexel":                  "PAREXEL",
    "covance":                  "Labcorp/Covance",
    "labcorp":                  "Labcorp",
    "icon plc":                 "ICON",
    "pra health":               "PRA Health Sciences",
    "evidera":                  "Evidera",
    "analysis group":           "Analysis Group",
    "precision xtract":         "Precision XTRACT",
    "health economics research":"HER",
    "optum":                    "Optum",
    "medscape":                 "Medscape",
    "mapi":                     "Mapi Group",
    # Payer/HTA Bodies
    "nice":                     "NICE (UK)",
    "icer":                     "ICER (US)",
    "cadth":                    "CADTH (Canada)",
    "g-ba":                     "G-BA (Germany)",
    "has":                      "HAS (France)",
}

ONCOLOGY_KEYWORDS = [
    "oncol", "cancer", "tumor", "tumour", "carcinoma", "lymphoma",
    "leukemia", "myeloma", "melanoma", "glioma", "sarcoma",
    "breast", "ovarian", "gastric", "cervical", "endometrial",
    "prostate", "colorectal", "hepatocellular", "renal cell",
    "non-small cell", "nsclc", "adc", "antibody-drug",
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _detect_companies(text: str) -> list[str]:
    text_lower = text.lower()
    found = set()
    # Sort by length descending to match longer phrases first
    for keyword in sorted(PHARMA_COMPANIES.keys(), key=len, reverse=True):
        if keyword in text_lower:
            found.add(PHARMA_COMPANIES[keyword])
    return sorted(found)


def _is_oncology(title: str, text: str) -> bool:
    combined = (title + " " + text).lower()
    return any(kw in combined for kw in ONCOLOGY_KEYWORDS)


def _parse_filename(filename: str) -> tuple[str, str, str]:
    stem = filename.replace(".pdf", "").strip()
    match = re.match(r'^([A-Z]+\d+)\s*-\s*(.+)$', stem)
    if match:
        poster_id = match.group(1)
        title = match.group(2).strip()
        category = re.match(r'^([A-Z]+)', poster_id).group(1)
    else:
        poster_id = stem[:10]
        title = stem
        category = "XX"
    return poster_id, category, title


def _extract_text(pdf_path: str, max_chars: int = 800) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return ""
            text = re.sub(r'\s+', ' ', pdf.pages[0].extract_text() or "").strip()
            is_prisma = "prisma" in text.lower() or "flow diagram" in text.lower()
            if (len(text) < 300 or is_prisma) and len(pdf.pages) > 1:
                text2 = re.sub(r'\s+', ' ', pdf.pages[1].extract_text() or "").strip()
                if len(text2) > len(text):
                    text = text2
            return text[:max_chars]
    except Exception:
        return ""


# ── Archetype classification ───────────────────────────────────────────────────

def _classify_archetype(counts: dict, total: int) -> tuple[str, str]:
    if total < 3:
        return "Minimal Presenter", f"Only {total} poster(s) — limited HEOR footprint at ISPOR 2026."

    pct = {k: round(v / total * 100) for k, v in counts.items()}

    ee_hta = pct.get("EE", 0) + pct.get("HTA", 0)
    rwd_co = pct.get("RWD", 0) + pct.get("CO", 0)
    eph_pcr = pct.get("EPH", 0) + pct.get("PCR", 0)
    msr = pct.get("MSR", 0)
    sa = pct.get("SA", 0)

    if ee_hta >= 45:
        return (
            "Payer-Ready",
            f"{ee_hta}% of posters are Economic Evaluation or HTA — active value dossier "
            f"construction. Likely within 12-18 months of a regulatory submission or launch."
        )
    if rwd_co >= 50:
        return (
            "RWE Builder",
            f"{rwd_co}% in Real-World Data and Clinical Outcomes — post-approval evidence "
            f"generation strategy. Likely seeking label expansion or payer coverage broadening."
        )
    if eph_pcr >= 40:
        return (
            "Disease Burden Establisher",
            f"{eph_pcr}% in Epidemiology and Patient-Centered Research — framing unmet need "
            f"and disease burden. Typically pre-approval behavior to prime payers and policy makers."
        )
    if msr >= 30:
        return (
            "Methods Innovator",
            f"{msr}% in Methodology — investing in HEOR infrastructure and methodological "
            f"leadership. Signals internal capability building or complex submission preparation."
        )
    if sa >= 25:
        return (
            "Systematic Evidence Aggregator",
            f"{sa}% in Systematic Analysis — building comparative effectiveness arguments "
            f"through indirect treatment comparisons and network meta-analyses."
        )
    # Balanced
    top_cats = sorted(pct.items(), key=lambda x: x[1], reverse=True)[:2]
    top_str = " and ".join(f"{c} ({p}%)" for c, p in top_cats)
    return (
        "Balanced Generalist",
        f"Broad portfolio across evidence categories. Top categories: {top_str}. "
        f"Indicates mature, diversified HEOR function."
    )


# ── Main ───────────────────────────────────────────────────────────────────────

def run(ispor_path: str):
    folder = pathlib.Path(ispor_path)
    pdfs = sorted(folder.glob("*.pdf"))
    now = datetime.now(timezone.utc).isoformat()

    print(f"\nPSIT -- Company Archetype Builder")
    print("=" * 52)
    print(f"  Total PDFs to process: {len(pdfs)}")
    print(f"  This will take 20-30 minutes. Processing...")

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_COMPANY_PROFILES)
        conn.execute(CREATE_POSTER_COMPANIES)
        conn.execute("DELETE FROM company_profiles")
        conn.execute("DELETE FROM poster_companies")
        conn.commit()

    # Step 1: Extract companies from all posters
    poster_rows = []
    skipped = 0

    for i, pdf_path in enumerate(pdfs, 1):
        if i % 50 == 0 or i == 1:
            print(f"  [{i:4d}/{len(pdfs)}] Processing...")

        poster_id, category, title = _parse_filename(pdf_path.name)
        text = _extract_text(str(pdf_path))

        if not text:
            skipped += 1
            continue

        corpus = title + " " + text
        companies = _detect_companies(corpus)
        is_onc = 1 if _is_oncology(title, text) else 0

        for company in companies:
            poster_rows.append((poster_id, category, title[:120], company, is_onc))

        # If no company detected, tag as Unaffiliated/Academic
        if not companies:
            poster_rows.append((poster_id, category, title[:120], "Academic/Unaffiliated", is_onc))

    print(f"\n  Processed: {len(pdfs) - skipped} | Skipped: {skipped}")
    print(f"  Total company-poster associations: {len(poster_rows)}")

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            "INSERT INTO poster_companies (poster_id, category, title, company, is_oncology) VALUES (?,?,?,?,?)",
            poster_rows,
        )
        conn.commit()

    # Step 2: Aggregate by company and classify archetypes
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT company, category, poster_id FROM poster_companies").fetchall()

    # Group by company
    from collections import defaultdict
    company_data: dict = defaultdict(lambda: {"categories": [], "poster_ids": set(), "oncology_count": 0})

    for company, category, poster_id in rows:
        company_data[company]["categories"].append(category)
        company_data[company]["poster_ids"].add(poster_id)

    # Also get oncology counts
    with sqlite3.connect(DB_PATH) as conn:
        onc_rows = conn.execute(
            "SELECT company, COUNT(*) FROM poster_companies WHERE is_oncology=1 GROUP BY company"
        ).fetchall()
    onc_map = {r[0]: r[1] for r in onc_rows}

    CAT_FIELDS = ["EE", "HTA", "CO", "RWD", "MSR", "EPH", "HSD", "HPR", "PCR", "SA"]

    profile_rows = []
    for company, data in company_data.items():
        cats = data["categories"]
        total = len(cats)
        counts = {c: cats.count(c) for c in CAT_FIELDS}
        other = total - sum(counts.values())
        archetype, rationale = _classify_archetype(counts, total)
        poster_ids_str = ", ".join(sorted(data["poster_ids"]))
        onc_count = onc_map.get(company, 0)

        profile_rows.append((
            company, total,
            counts.get("EE", 0), counts.get("HTA", 0),
            counts.get("CO", 0), counts.get("RWD", 0),
            counts.get("MSR", 0), counts.get("EPH", 0),
            counts.get("HSD", 0), counts.get("HPR", 0),
            counts.get("PCR", 0), counts.get("SA", 0),
            other, onc_count, archetype, rationale, poster_ids_str, now,
        ))

    # Sort by total posters descending
    profile_rows.sort(key=lambda x: x[1], reverse=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO company_profiles
               (company_name, total_posters, ee_count, hta_count, co_count, rwd_count,
                msr_count, eph_count, hsd_count, hpr_count, pcr_count, sa_count,
                other_count, oncology_count, archetype, archetype_rationale,
                poster_ids, pull_timestamp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            profile_rows,
        )
        conn.commit()

    print(f"\n  Company profiles built: {len(profile_rows)}")
    print(f"\n  Archetype distribution:")
    from collections import Counter
    archetype_counts = Counter(r[14] for r in profile_rows)
    for arch, count in archetype_counts.most_common():
        print(f"    {arch}: {count}")

    print(f"\n  Top 10 companies by poster volume:")
    for r in profile_rows[:10]:
        print(f"    {r[0]:35s} {r[1]:3d} posters | {r[14]}")

    print("\nArchetype build complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PSIT Company Archetype Builder")
    parser.add_argument("--path", required=True, help="Path to ISPOR poster folder")
    args = parser.parse_args()
    run(args.path)
