#!/usr/bin/env python3
"""
extract_annexures.py - Whitelist Extraction & Math Verification Engine
Directorate of Local Fund Audit — Government of Sikkim

Features:
  - Whitelist enforcement for 212 authorized local bodies (199 GPUs, 6 ZPs, 7 ULBs).
  - Strict Financial Year range constraint (2015-16 to 2025-26).
  - Legacy 4-district Zilla Panchayat resolution (East, West, North, South).
  - Regional orthographic alias normalization.
  - Mathematical integrity verification:
      1) Total Receipts == Opening Balance + Receipts
      2) Closing Balance == Total Receipts - Payments
  - Routes discrepancies to data/processed/audit_discrepancies.json.
  - Outputs verified records to data/processed/financial_statements.json.
"""

import sys
import re
import json
import difflib
from pathlib import Path
from collections import defaultdict

try:
    import pdfplumber
except ImportError:
    print("Error: Required library 'pdfplumber' is missing. Run: pip install pdfplumber")
    sys.exit(1)


# Mapping of legacy 4-district references to modern Zilla Panchayat codes
LEGACY_ZILLA_MAP = {
    "east": "216",          # Gangtok Zilla Panchayat
    "eastzilla": "216",
    "eastdistrict": "216",
    "edzp": "216",
    "west": "219",          # Gyalshing Zilla Panchayat
    "westzilla": "219",
    "zillawest": "219",
    "westdistrict": "219",
    "wdzp": "219",
    "north": "217",         # Mangan Zilla Panchayat
    "northzilla": "217",
    "northdistrict": "217",
    "ndzp": "217",
    "south": "218",         # Namchi Zilla Panchayat
    "southzilla": "218",
    "southdistrict": "218",
    "sdzp": "218",
}

# Regional orthographic normalization map
SPELLING_ALIASES = {
    "geyzing": "gyalshing",
    "gezing": "gyalshing",
    "gazing": "gyalshing",
    "yoksum": "yuksom",
    "yoksom": "yuksom",
    "yuksam": "yuksom",
    "jorethang": "nayabazar",
    "jorethangnayabazar": "nayabazar",
    "nayabazarjorethang": "nayabazar",
    "ravangla": "ravong",
    "rabong": "ravong",
    "sikkip": "sikip",
    "phensong": "phensang",
    "lamatingtingmoo": "lamtingtingmo",
    "turukramabong": "turukramabung",
    "salghari": "salghari",
    "dzumsa": "",
    "gpu": "",
    "panchayat": "",
    "zilla": "",
    "district": "",
    "unit": "",
    "nagar": "",
    "council": "",
    "corporation": "",
    "gmc": "gangtok",
}


def load_audit_whitelist():
    """Load the 212 authorized Local Bodies from the Master Audit Plan."""
    plan_path = Path("data/raw/annual_audit_plan_2026.json")
    if not plan_path.exists():
        print(f"[!] Master audit plan not found at {plan_path.resolve()}.")
        print("    Please run: python3 scripts/generate_master_units.py")
        sys.exit(1)
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_clean_string(s):
    """Clean strings and apply standardized aliases for resilient matching."""
    if not s:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()
    for key, target in SPELLING_ALIASES.items():
        if key in cleaned:
            cleaned = cleaned.replace(key, target)
    return cleaned


def match_against_whitelist(raw_name, whitelist):
    """
    Match an extracted string against the 212 authorized units:
      1. Resolves legacy 4-district ZP keywords.
      2. Checks direct normalized containment.
      3. Uses difflib fuzzy matching fallback (cutoff 0.70).
    """
    if not raw_name or len(raw_name.strip()) < 3:
        return None

    raw_lower = raw_name.lower().strip()
    norm_raw = normalize_clean_string(raw_lower)

    # 1. Check legacy Zilla Panchayat naming patterns
    if "zilla" in raw_lower or "district" in raw_lower or any(d in raw_lower.split() for d in ["east", "west", "north", "south", "edzp", "wdzp", "ndzp", "sdzp"]):
        for legacy_key, target_code in LEGACY_ZILLA_MAP.items():
            if legacy_key in norm_raw:
                for unit in whitelist:
                    if unit.get("code") == target_code:
                        return unit

    # 2. Check direct normalized name containment
    for unit in whitelist:
        norm_canonical = normalize_clean_string(unit["name"])
        if norm_raw == norm_canonical:
            return unit
        if len(norm_raw) >= 5 and (norm_raw in norm_canonical or norm_canonical in norm_raw):
            return unit

    # 3. Fuzzy matching fallback
    whitelist_names = [unit["name"] for unit in whitelist]
    matches = difflib.get_close_matches(raw_name, whitelist_names, n=1, cutoff=0.70)
    if matches:
        matched_name = matches[0]
        for unit in whitelist:
            if unit["name"] == matched_name:
                return unit

    return None


def clean_currency(val):
    """Convert monetary table strings into clean float values."""
    if val is None:
        return 0.0
    s = str(val).strip().replace('₹', '').replace(',', '').replace('\n', ' ')
    if s.lower() in ['', 'nil', '-', '--', 'null', 'n/a']:
        return 0.0
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    match = re.search(r'[-+]?\d*\.?\d+', s)
    return float(match.group(0)) if match else 0.0


def detect_fy(text):
    """
    Strictly extract valid Financial Years between 2015-16 and 2025-26.
    Rejects general 4-digit numbers to avoid false positives.
    """
    if not text:
        return None

    # Matches only FYs starting from 2015 up to 2026
    match = re.search(r'\b(20(?:1[5-9]|2[0-6]))[-–/](\d{2,4})\b', text)
    if match:
        start_yr = match.group(1)
        end_yr = match.group(2)
        if len(end_yr) == 4:
            end_yr = end_yr[2:]
        return f"{start_yr}-{end_yr}"

    return None


def run_extraction():
    whitelist = load_audit_whitelist()
    print(f"[*] Loaded {len(whitelist)} approved audit units from Annual Audit Plan 2026-27.")

    raw_dir = Path("data/raw")
    pdf_files = sorted([f for f in raw_dir.glob("*.pdf") if "plan" not in f.name.lower()])
    if not pdf_files:
        print(f"[!] No Annual Report PDFs found in {raw_dir.resolve()}.")
        return

    # Aggregate extracted figures by (Canonical Unit Code, Financial Year)
    aggregated = defaultdict(lambda: {"ob": 0.0, "receipts": 0.0, "tr": 0.0, "pay": 0.0, "cb": 0.0, "sources": set()})
    unit_lookup = {u["code"]: u for u in whitelist}

    for pdf_path in pdf_files:
        print(f"  -> Scanning: {pdf_path.name}")
        default_fy = detect_fy(pdf_path.name) or "2024-25"
        current_fy = default_fy

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                page_fy = detect_fy(text)
                if page_fy:
                    current_fy = page_fy

                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Dynamic header column detection
                    unit_idx, ob_idx, r_idx, tr_idx, pay_idx, cb_idx = 0, -1, -1, -1, -1, -1
                    for idx, cell in enumerate(table[0]):
                        c = str(cell).lower().replace('\n', ' ')
                        if any(k in c for k in ['gram panchayat', 'zilla', 'name of', 'unit', 'local body', 'nagar', 'institution']):
                            unit_idx = idx
                        elif 'opening' in c:
                            ob_idx = idx
                        elif 'total receipt' in c:
                            tr_idx = idx
                        elif 'receipt' in c and 'total' not in c:
                            r_idx = idx
                        elif any(k in c for k in ['payment', 'expenditure']):
                            pay_idx = idx
                        elif 'closing' in c:
                            cb_idx = idx

                    # Fallback column structure
                    if ob_idx == -1 and len(table[0]) >= 6:
                        ob_idx = len(table[0]) - 5
                        r_idx = len(table[0]) - 4
                        tr_idx = len(table[0]) - 3
                        pay_idx = len(table[0]) - 2
                        cb_idx = len(table[0]) - 1

                    for row in table[1:]:
                        if not row or len(row) <= max(ob_idx, pay_idx, cb_idx):
                            continue

                        raw_name = str(row[unit_idx]).replace('\n', ' ').strip() if unit_idx < len(row) else ''
                        matched_unit = match_against_whitelist(raw_name, whitelist)
                        if not matched_unit:
                            continue

                        ob = clean_currency(row[ob_idx]) if ob_idx != -1 else 0.0
                        rec = clean_currency(row[r_idx]) if r_idx != -1 else 0.0
                        tr = clean_currency(row[tr_idx]) if tr_idx != -1 else (ob + rec)
                        pay = clean_currency(row[pay_idx]) if pay_idx != -1 else 0.0
                        cb = clean_currency(row[cb_idx]) if cb_idx != -1 else (tr - pay)

                        # Skip blank/nil rows
                        if ob == 0 and rec == 0 and tr == 0 and pay == 0 and cb == 0:
                            continue

                        key = (matched_unit["code"], current_fy)
                        aggregated[key]["ob"] += ob
                        aggregated[key]["receipts"] += rec
                        aggregated[key]["tr"] += tr
                        aggregated[key]["pay"] += pay
                        aggregated[key]["cb"] += cb
                        aggregated[key]["sources"].add(pdf_path.name)

    verified_records = []
    discrepancies = []
    rec_id, disc_id = 1, 1

    for (code, fy), v in aggregated.items():
        unit_meta = unit_lookup[code]
        ob = round(v["ob"], 2)
        rec = round(v["receipts"], 2)
        tr = round(v["tr"], 2)
        pay = round(v["pay"], 2)
        cb = round(v["cb"], 2)

        calc_tr = round(ob + rec, 2)
        calc_cb = round(tr - pay, 2)

        math_ok = True
        reasons = []

        # Mathematical verification checks
        if rec > 0 and abs(calc_tr - tr) > 2.0:
            math_ok = False
            reasons.append(f"Total Receipts mismatch: Reported ₹{tr:,.2f} != (OB ₹{ob:,.2f} + Receipts ₹{rec:,.2f} = ₹{calc_tr:,.2f})")
        if abs(calc_cb - cb) > 2.0:
            math_ok = False
            reasons.append(f"Closing Balance mismatch: Reported ₹{cb:,.2f} != (TR ₹{tr:,.2f} - Payments ₹{pay:,.2f} = ₹{calc_cb:,.2f})")

        rec_entry = {
            "code": code,
            "name": unit_meta["name"],
            "tier": unit_meta["tier"],
            "district": unit_meta["district"],
            "bac": unit_meta.get("bac", "N/A"),
            "fy": fy,
            "ob": ob,
            "receipts": rec,
            "total_receipts": tr,
            "payments": pay,
            "cb": cb,
            "sources": sorted(list(v["sources"]))
        }

        if math_ok:
            rec_entry["id"] = rec_id
            verified_records.append(rec_entry)
            rec_id += 1
        else:
            rec_entry["id"] = disc_id
            rec_entry["calc_total_receipts"] = calc_tr
            rec_entry["calc_cb"] = calc_cb
            rec_entry["error_reason"] = " | ".join(reasons)
            discrepancies.append(rec_entry)
            disc_id += 1

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "financial_statements.json", "w", encoding="utf-8") as f:
        json.dump(verified_records, f, indent=2, ensure_ascii=False)

    with open(out_dir / "audit_discrepancies.json", "w", encoding="utf-8") as f:
        json.dump(discrepancies, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Whitelist Extraction & Math Verification Complete:")
    print(f"    • Total Authorized Units in Scope : {len(whitelist)}")
    print(f"    • Verified Financial Statements   : {len(verified_records)} -> data/processed/financial_statements.json")
    print(f"    • Flagged Calculation Anomalies    : {len(discrepancies)} -> data/processed/audit_discrepancies.json")


if __name__ == "__main__":
    run_extraction()
