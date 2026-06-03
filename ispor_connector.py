"""
PSIT -- ISPOR 2026 Poster Connector.
Extracts text from oncology-relevant ISPOR posters (first page only),
indexes them in SQLite as T6_HEOR_OUTCOMES evidence, and feeds into
the PSIT evidence architecture.

Usage:
    python ispor_connector.py --path "C:/Users/kaibo/OneDrive/Desktop/ISPOR"

Requirements:
    pip install pdfplumber
"""

import argparse
import os
import re
import sqlite3
import pathlib
from datetime import datetime, timezone

try:
    import pdfplumber
except ImportError:
    raise ImportError("Run: pip install pdfplumber")

# ── Configuration ─────────────────────────────────────────────────────────────

DB_PATH = pathlib.Path("psit.db")

ONCOLOGY_KEYWORDS = [
    "oncol", "cancer", "tumor", "tumour", "carcinoma", "lymphoma",
    "leukemia", "leukaemia", "myeloma", "melanoma", "glioma", "sarcoma",
    "breast", "ovarian", "gastric", "cervical", "endometrial", "urothelial",
    "prostate", "colorectal", "hepatocellular", "renal cell", "bladder",
    "non-small cell", "nsclc", "pancreatic", "esophageal",
]

ADC_DRUGS = {
    "enhertu": "Trastuzumab deruxtecan (Enhertu)",
    "t-dxd": "Trastuzumab deruxtecan (Enhertu)",
    "trastuzumab deruxtecan": "Trastuzumab deruxtecan (Enhertu)",
    "ds-8201": "Trastuzumab deruxtecan (Enhertu)",
    "kadcyla": "Ado-trastuzumab emtansine (Kadcyla)",
    "t-dm1": "Ado-trastuzumab emtansine (Kadcyla)",
    "ado-trastuzumab": "Ado-trastuzumab emtansine (Kadcyla)",
    "trodelvy": "Sacituzumab govitecan (Trodelvy)",
    "sacituzumab": "Sacituzumab govitecan (Trodelvy)",
    "padcev": "Enfortumab vedotin (Padcev)",
    "enfortumab": "Enfortumab vedotin (Padcev)",
    "elahere": "Mirvetuximab soravtansine (Elahere)",
    "mirvetuximab": "Mirvetuximab soravtansine (Elahere)",
    "mirv": "Mirvetuximab soravtansine (Elahere)",
    "datopotamab": "Datopotamab deruxtecan",
    "dato-dxd": "Datopotamab deruxtecan",
    "disitamab": "Disitamab vedotin",
    "rc48": "Disitamab vedotin",
    "tivdak": "Tisotumab vedotin (Tivdak)",
    "tisotumab": "Tisotumab vedotin (Tivdak)",
    "zynlonta": "Loncastuximab tesirine (Zynlonta)",
    "loncastuximab": "Loncastuximab tesirine (Zynlonta)",
    "blenrep": "Belantamab mafodotin",
    "belantamab": "Belantamab mafodotin",
    "lumoxiti": "Moxetumomab pasudotox",
    "besylomab": "Besylomab",
    "antibody-drug conjugate": "ADC (generic)",
    "adc": "ADC (generic)",
}

TARGET_ANTIGENS = {
    "her2": "HER2",
    "erbb2": "HER2",
    "trop-2": "TROP2",
    "trop2": "TROP2",
    "trop ": "TROP2",
    "nectin-4": "Nectin-4",
    "nectin4": "Nectin-4",
    "folate receptor": "FRα",
    "fr-alpha": "FRα",
    "fralpha": "FRα",
    "frα": "FRα",           # Greek alpha character
    "frα": "FRα",     # Unicode folate receptor alpha
    "fr‐positive": "FRα",  # FR‑positive (en-dash)
    "fr-positive": "FRα",
    "her3": "HER3",
    "erbb3": "HER3",
    "egfr": "EGFR",
    "b7-h3": "B7-H3",
    "b7h3": "B7-H3",
    "cd19": "CD19",
    "cd22": "CD22",
    "cd30": "CD30",
    "cd33": "CD33",
    "cd79b": "CD79b",
    "bcma": "BCMA",
    "claudin": "Claudin 18.2",
    "dll3": "DLL3",
    "axl": "AXL",
}

# Drug → implied target (used when target not explicit in text)
DRUG_TO_TARGET = {
    "Mirvetuximab soravtansine (Elahere)":       "FRα",
    "Sacituzumab govitecan (Trodelvy)":           "TROP2",
    "Enfortumab vedotin (Padcev)":                "Nectin-4",
    "Tisotumab vedotin (Tivdak)":                 "Nectin-4",
    "Trastuzumab deruxtecan (Enhertu)":           "HER2",
    "Ado-trastuzumab emtansine (Kadcyla)":        "HER2",
    "Disitamab vedotin":                          "HER2",
    "Datopotamab deruxtecan":                     "TROP2",
    "Belantamab mafodotin":                       "BCMA",
    "Loncastuximab tesirine (Zynlonta)":          "CD19",
}

EVIDENCE_TYPES = {
    "EE": "Economic Evaluation",
    "HTA": "Health Technology Assessment",
    "CO": "Clinical Outcomes / RWE",
    "RWD": "Real-World Data",
    "MSR": "Methodology / AI-ML",
    "EPH": "Epidemiology",
    "HSD": "Health Services & Delivery",
    "HPR": "Health Policy Research",
    "PCR": "Patient-Centered Research",
    "SA": "Systematic Analysis / Meta-Analysis",
    "MT": "Methodology",
    "PT": "Patient Outcomes",
}

# ── Schema ─────────────────────────────────────────────────────────────────────

CREATE_ISPOR_POSTERS = """
CREATE TABLE IF NOT EXISTS ispor_posters (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    poster_id        TEXT NOT NULL,
    category         TEXT,
    evidence_type    TEXT,
    title            TEXT,
    abstract_text    TEXT,
    drug_tags        TEXT,
    target_tags      TEXT,
    relevance_tier   TEXT,
    pull_timestamp   TEXT,
    source_label     TEXT DEFAULT 'ISPOR 2026',
    source_url       TEXT DEFAULT 'ISPOR 2026 Annual Meeting'
)
"""

# ── Helpers ────────────────────────────────────────────────────────────────────

def _is_oncology_relevant(filename: str) -> bool:
    name = filename.lower()
    return any(kw in name for kw in ONCOLOGY_KEYWORDS)


def _detect_drugs(text: str) -> list[str]:
    text_lower = text.lower()
    found = set()
    for keyword, canonical in ADC_DRUGS.items():
        if keyword in text_lower:
            found.add(canonical)
    return sorted(found)


def _detect_targets(text: str, drugs: list[str] = None) -> list[str]:
    text_lower = text.lower()
    found = set()
    # Direct keyword match
    for keyword, canonical in TARGET_ANTIGENS.items():
        if keyword in text_lower:
            found.add(canonical)
    # Unicode FRα explicit check (U+03B1)
    if "frα" in text or "FRα" in text:
        found.add("FRα")
    # Infer targets from detected drugs
    if drugs:
        for drug in drugs:
            if drug in DRUG_TO_TARGET:
                found.add(DRUG_TO_TARGET[drug])
    return sorted(found)


def _score_relevance(drugs: list, targets: list, category: str) -> str:
    """Score ADC relevance as HIGH / MEDIUM / LOW."""
    adc_drugs = [d for d in drugs if d != "ADC (generic)"]
    if adc_drugs and targets:
        return "HIGH"
    if adc_drugs or (targets and category in ("EE", "HTA", "CO")):
        return "MEDIUM"
    return "LOW"


def _extract_first_page(pdf_path: str, max_chars: int = 1200) -> str:
    """Extract text from the first substantive page. Token-efficient.
    Falls back to page 2 if page 1 is a PRISMA/flow diagram or thin."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                return ""
            text = re.sub(r'\s+', ' ', pdf.pages[0].extract_text() or "").strip()
            # Detect PRISMA flow pages or thin pages — try page 2
            is_prisma = "prisma" in text.lower() or "flow diagram" in text.lower()
            if (len(text) < 400 or is_prisma) and len(pdf.pages) > 1:
                text2 = re.sub(r'\s+', ' ', pdf.pages[1].extract_text() or "").strip()
                if len(text2) > len(text):
                    text = text2
            return text[:max_chars]
    except Exception as e:
        return f"[Extraction error: {e}]"


def _parse_filename(filename: str) -> tuple[str, str, str]:
    """Return (poster_id, category, title) from filename."""
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


# ── Database ───────────────────────────────────────────────────────────────────

def init_ispor_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_ISPOR_POSTERS)
        conn.commit()
    print("  ISPOR posters table ready.")


def clear_ispor_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM ispor_posters")
        conn.commit()


def insert_posters(records: list[dict]):
    now = datetime.now(timezone.utc).isoformat()
    rows = [(
        r["poster_id"], r["category"], r["evidence_type"], r["title"],
        r["abstract_text"], r["drug_tags"], r["target_tags"],
        r["relevance_tier"], now,
    ) for r in records]
    with sqlite3.connect(DB_PATH) as conn:
        conn.executemany(
            """INSERT INTO ispor_posters
               (poster_id, category, evidence_type, title, abstract_text,
                drug_tags, target_tags, relevance_tier, pull_timestamp)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
    print(f"  Inserted {len(rows)} ISPOR poster records.")


# ── Main ───────────────────────────────────────────────────────────────────────

def run(ispor_path: str, limit: int = None, high_only: bool = False):
    folder = pathlib.Path(ispor_path)
    if not folder.exists():
        raise FileNotFoundError(f"ISPOR folder not found: {ispor_path}")

    pdfs = sorted(folder.glob("*.pdf"))
    print(f"\nPSIT -- ISPOR 2026 Connector")
    print("=" * 52)
    print(f"  Folder   : {folder}")
    print(f"  Total PDFs: {len(pdfs)}")

    # Filter to oncology-relevant by filename
    oncology_pdfs = [p for p in pdfs if _is_oncology_relevant(p.name)]
    print(f"  Oncology-relevant (by filename): {len(oncology_pdfs)}")

    if limit:
        oncology_pdfs = oncology_pdfs[:limit]
        print(f"  Processing limit: {limit}")

    init_ispor_table()
    clear_ispor_table()

    records = []
    skipped = 0

    for i, pdf_path in enumerate(oncology_pdfs, 1):
        poster_id, category, title = _parse_filename(pdf_path.name)
        evidence_type = EVIDENCE_TYPES.get(category, category)

        print(f"  [{i:3d}/{len(oncology_pdfs)}] {poster_id} — extracting...", end="\r")

        text = _extract_first_page(str(pdf_path))
        if not text or text.startswith("[Extraction"):
            skipped += 1
            continue

        # Combine filename + body for tag detection
        search_corpus = title.lower() + " " + text.lower()
        drugs = _detect_drugs(search_corpus)
        targets = _detect_targets(search_corpus + text, drugs=drugs)  # pass raw text for unicode
        relevance = _score_relevance(drugs, targets, category)

        if high_only and relevance != "HIGH":
            continue

        records.append({
            "poster_id":     poster_id,
            "category":      category,
            "evidence_type": evidence_type,
            "title":         title,
            "abstract_text": text,
            "drug_tags":     ", ".join(drugs) if drugs else "",
            "target_tags":   ", ".join(targets) if targets else "",
            "relevance_tier": relevance,
        })

    print()  # clear \r line
    print(f"\n  Processed : {len(records)} posters")
    print(f"  Skipped   : {skipped} (extraction errors)")
    high = sum(1 for r in records if r["relevance_tier"] == "HIGH")
    med  = sum(1 for r in records if r["relevance_tier"] == "MEDIUM")
    low  = sum(1 for r in records if r["relevance_tier"] == "LOW")
    print(f"  HIGH relevance (ADC drug + target): {high}")
    print(f"  MEDIUM relevance (drug or target):  {med}")
    print(f"  LOW relevance (oncology context):   {low}")

    if records:
        insert_posters(records)

    print("\nISPOR connector complete.")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PSIT ISPOR 2026 Connector")
    parser.add_argument("--path", required=True, help="Path to ISPOR poster folder")
    parser.add_argument("--limit", type=int, default=None, help="Max posters to process (for testing)")
    parser.add_argument("--high-only", action="store_true", help="Only insert HIGH relevance posters")
    args = parser.parse_args()
    run(args.path, limit=args.limit, high_only=args.high_only)
