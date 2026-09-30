#!/usr/bin/env python3
"""
extract_annexures.py - Whitelist Extraction & Mathematical Verification Engine
Directorate of Local Fund Audit — Government of Sikkim

Features:
  - Whitelist enforcement for 212 authorized local bodies (199 GPUs, 6 ZPs, 7 ULBs).
  - Multi-year alias dictionary from Annual Plans 2022-2026.
  - Strips numeric prefixes (e.g., '38-Chota Samdong', '54-Bariakhop').
  - Legacy 4-district ZP mapping (East -> Gangtok, West -> Gyalshing, etc.).
  - Bounded FY extraction (2015-16 through 2025-26).
  - Mathematical integrity verification:
      1) Total Receipts == Opening Balance + Receipts
      2) Closing Balance == Total Receipts - Payments
  - Isolates arithmetic discrepancies into data/processed/audit_discrepancies.json.
  - Saves verified records into data/processed/financial_statements.json.
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

# Comprehensive lookup mapping all historical spellings, shorthand, and BAC list prefixes
# to canonical Local Body codes from the 212-unit whitelist
EXPLICIT_NAME_TO_CODE = {
    # Zilla Panchayats (Legacy 4-district & modern)
    "east zilla": "216",
    "east district zilla panchayat": "216",
    "edzp": "216",
    "east zilla panchayat": "216",
    "gangtok zilla": "216",
    "gangtok zilla panchayat": "216",
    "west zilla": "219",
    "west district zilla panchayat": "219",
    "wdzp": "219",
    "zilla west": "219",
    "west zilla panchayat": "219",
    "gyalshing zilla": "219",
    "gyalshing zilla panchayat": "219",
    "geyzing zilla panchayat": "219",
    "north zilla": "217",
    "north district zilla panchayat": "217",
    "ndzp": "217",
    "north zilla panchayat": "217",
    "mangan zilla": "217",
    "mangan zilla panchayat": "217",
    "south zilla": "218",
    "south district zilla panchayat": "218",
    "sdzp": "218",
    "south zilla panchayat": "218",
    "namchi zilla": "218",
    "namchi zilla panchayat": "218",
    "pakyong zilla": "300083",
    "pakyong zilla panchayat": "300083",
    "soreng zilla": "300084",
    "soreng zilla panchayat": "300084",

    # Municipalities / Urban Local Bodies
    "geyzing nagar panchayat": "249690",
    "gazing nagar panchayat": "249690",
    "gnp": "249690",
    "gyalshing np": "249690",
    "gyalshing nagar panchayat": "249690",
    "jorethang nayabazar nagar panchayat": "249693",
    "nayabazar jorethang nagar panchayat": "249693",
    "jnp": "249693",
    "jorethang nagar panchayat": "249693",
    "nayabazar nagar panchayat": "249693",
    "singtam nagar panchayat": "249695",
    "snp": "249695",
    "mangan nagar panchayat": "249689",
    "mnp": "249689",
    "rangpo nagar panchayat": "290460",
    "rnp": "290460",
    "gangtok municipal corporation": "249694",
    "gmc": "249694",
    "namchi municipal council": "249692",
    "nmc": "249692",

    # Gram Panchayat Units (Transliterations, Historical Variants & Numbered List Prefixes)
    "yoksum": "254869",
    "yoksom": "254869",
    "yuksam": "254869",
    "yuksom": "254869",
    "yuksum dubdi": "254869",
    "melli aching": "254774",
    "melliaching": "254774",
    "meli aching": "254774",
    "tingling": "300082",
    "thingling": "300082",
    "rimbi tingvong": "276336",
    "rimbi tingbrum": "276336",
    "khecheopalri": "254851",
    "khechopalri": "254851",
    "khechodpalri": "254851",
    "karjee mangnam": "254743",
    "karzi mangnam": "254743",
    "arithang chongrang": "254709",
    "arithang chongrong": "254709",
    "dhupi narkhola": "254733",
    "dhupidara narkhola": "254733",
    "chota samdong": "254725",
    "chota samdong arubotey": "254725",
    "chota samdong arubotay": "254725",
    "38 chota samdong": "254725",
    "38 chota samdong arubotay": "254725",
    "buriakhop": "254720",
    "burikhop": "254720",
    "54 bariakhop gpu": "254720",
    "54 bariakhop": "254720",
    "barikhop": "254720",
    "lungchok salangdang": "254762",
    "lunchok salangdang": "254762",
    "lungchok salyangdang": "254762",
    "ribdi bharayang": "254807",
    "ribdi bhareng": "254807",
    "saprenagi": "300590",
    "sapreynaghi": "300590",
    "upper fambong": "254863",
    "upper thambong": "254863",
    "lower fambong": "254763",
    "gyaten karmatar": "254744",
    "karmatar gitang": "254744",
    "bongten sopakha": "254712",
    "bongten sapong": "254712",
    "bongten": "254712",
    "sardong lungzik": "254825",
    "sardung lungzik": "254825",
    "phensong": "254793",
    "phensang": "254793",
    "men rongong": "254776",
    "sirwani chisopani": "276337",
    "chisopani": "276337",
    "simick lingzey": "254829",
    "simik lingzey": "254829",
    "dungdung thasa": "257847",
    "dung dung thasa": "257847",
    "beng phegyong": "254717",
    "byeng phegyong": "254717",
    "byeng": "254717",
    "namchebong": "254745",
    "namcheybong": "254745",
    "boomtar": "276342",
    "boomtar salleybong": "276342",
    "salleybong": "276342",
    "nagi karek": "257853",
    "karek kabrey": "257853",
    "kateng pamphok": "254779",
    "rameng nizrameng": "254799",
    "tangzi bikmat": "254843",
    "turung mamring": "254862",
    "bhusuk naitam": "254780",
    "kopibari syari": "257846",
    "nandok saramsa": "257845",
    "rongey tathangchen": "254846",
    "rongay tathangchen": "254846",
    "latuk chuchenpheri": "254753",
    "latuk barapathing": "254753",
    "thekabong parakha": "254850",
    "linkey parakha": "254850",
    "lamating tingmoo": "254752",
    "lamting tingmo": "254752",
    "turuk ramabong": "254861",
    "turuk ramabung": "254861",
    "46 budang gpu": "276343",
    "46 budang": "276343",
    "budang": "276343",
    "bhudang": "276343",
    "52 karthok bojek": "257849",
    "karthok bojek": "257849",
    "50 timburbong": "300285",
    "lower timburbong": "300285",
    "upper timburbong": "254852",
    "45 malbasey": "254768",
    "malbasey": "254768",
    "malbasay": "254768",
    "48 mangsari mangerjung": "276344",
    "mangsari mangarjung": "276344",
    "49 singling": "254831",
    "singling": "254831",
    "47 soreng": "254834",
    "soreng": "254834",
    "51 tharpu": "254849",
    "tharpu": "254849"
}

SPELLING_ALIASES = {
    "geyzing": "gyalshing",
    "gezing": "gyalshing",
    "gazing": "gyalshing",
    "yoksum": "yuksom",
    "yoksom": "yuksom",
    "yuksam": "yuksom",
    "jorethang": "nayabazar",
    "ravangla": "ravong",
    "rabong": "ravong",
    "sikkip": "sikip",
    "phensong": "phensang",
    "dzumsa": "",
    "gpu": "",
    "panchayat": "",
    "zilla": "",
    "district": "",
    "unit": "",
    "nagar": "",
    "council": "",
    "corporation": "",
    "gmc": "gangtok"
}


def load_audit_whitelist():
    """Load canonical list of 212 units from the master audit plan."""
    plan_path = Path("data/raw/annual_audit_plan_2026.json")
    if not plan_path.exists():
        print(f"[!] Master audit plan not found at {plan_path.resolve()}.")
        print("    Please run: python3 scripts/generate_master_units.py")
        sys.exit(1)
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_unit_string(s):
    """Strip numbers, BAC prefixes, sl. nos, and non-alphabetical artifacts."""
    if not s:
        return ""
    text = str(s).strip().lower()
    text = re.sub(r'^(?:sl\.?\s*no\.?|sno\.?|\d+[\.\-\)]|\d+\s*[-/]?\s*)\s*', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_clean_string(s):
    """Clean string and apply phonetic replacements."""
    if not s:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()
    for key, target in SPELLING_ALIASES.items():
        if key in cleaned:
            cleaned = cleaned.replace(key, target)
    return cleaned


def match_against_whitelist(raw_name, whitelist):
    """Match extracted strings against canonical 212 units."""
    if not raw_name or len(str(raw_name).strip()) < 3:
        return None

    cleaned_raw = clean_unit_string(raw_name)
    if not cleaned_raw:
        return None

    if cleaned_raw in EXPLICIT_NAME_TO_CODE:
        target_code = EXPLICIT_NAME_TO_CODE[cleaned_raw]
        for u in whitelist:
            if u["code"] == target_code:
                return u

    for alias_name, code in EXPLICIT_NAME_TO_CODE.items():
        if len(alias_name) >= 5 and (alias_name in cleaned_raw or cleaned_raw in alias_name):
            for u in whitelist:
                if u["code"] == code:
                    return u

    norm_raw = normalize_clean_string(cleaned_raw)
    for u in whitelist:
        norm_canonical = normalize_clean_string(u["name"])
        if norm_raw == norm_canonical:
            return u
        if len(norm_raw) >= 5 and (norm_raw in norm_canonical or norm_canonical in norm_raw):
            return u

    whitelist_names = [u["name"] for u in whitelist]
    matches = difflib.get_close_matches(raw_name, whitelist_names, n=1, cutoff=0.72)
    if matches:
        for u in whitelist:
            if u["name"] == matches[0]:
                return u

    return None


def clean_currency(val, is_lakhs=False):
    """Parse numeric values, convert parentheses to negative, and scale Lakhs to Rupees."""
    if val is None:
        return 0.0
    s = str(val).strip().replace('₹', '').replace(',', '').replace(' ', '')
    if s.lower() in ['', 'nil', '-', '--', 'null', 'n/a', 'nan']:
        return 0.0

    is_negative = False
    if s.startswith('(') and s.endswith(')'):
        is_negative = True
        s = s[1:-1]

    match = re.search(r'[-+]?\d*\.?\d+', s)
    if not match:
        return 0.0

    num = float(match.group(0))
    if is_negative:
        num = -num

    if is_lakhs:
        num = num * 100000.0

    return num


def detect_fy(text):
    """Strictly extract valid Financial Years between 2015-16 and 2025-26."""
    if not text:
        return None
    match = re.search(r'\b(20(?:1[5-9]|2[0-5]))[-–/](\d{2,4})\b', str(text))
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

    aggregated = defaultdict(lambda: {"ob": 0.0, "receipts": 0.0, "tr": 0.0, "pay": 0.0, "cb": 0.0, "sources": set()})
    unit_lookup = {u["code"]: u for u in whitelist}

    for pdf_path in pdf_files:
        print(f"  -> Scanning: {pdf_path.name}")
        default_fy = detect_fy(pdf_path.name) or "2024-25"
        current_fy = default_fy

        with pdfplumber.open(pdf_path) as pdf:
            current_unit = None
            for page in pdf.pages:
                text = page.extract_text() or ""
                page_fy = detect_fy(text)
                if page_fy:
                    current_fy = page_fy

                is_lakhs = bool(re.search(r'lakh', text, re.IGNORECASE))

                tables = page.extract_tables()
                for table in tables:
                    if not table or len(table) < 2:
                        continue

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

                    if ob_idx == -1 and len(table[0]) >= 6:
                        ob_idx = len(table[0]) - 5
                        r_idx = len(table[0]) - 4
                        tr_idx = len(table[0]) - 3
                        pay_idx = len(table[0]) - 2
                        cb_idx = len(table[0]) - 1

                    for row in table[1:]:
                        if not row or len(row) <= max(ob_idx, pay_idx, cb_idx):
                            continue

                        row_str = " ".join([str(c).lower() for c in row if c])
                        if any(skip in row_str for skip in ['total', 'grand total', 'sub total', 'sl. no', 'particulars']):
                            continue

                        raw_name = str(row[unit_idx]).replace('\n', ' ').strip() if unit_idx < len(row) else ''
                        if raw_name:
                            matched = match_against_whitelist(raw_name, whitelist)
                            if matched:
                                current_unit = matched
                        elif not current_unit:
                            continue

                        active_unit = current_unit
                        if not active_unit:
                            continue

                        ob = clean_currency(row[ob_idx], is_lakhs) if ob_idx != -1 else 0.0
                        rec = clean_currency(row[r_idx], is_lakhs) if r_idx != -1 else 0.0
                        tr = clean_currency(row[tr_idx], is_lakhs) if tr_idx != -1 else (ob + rec)
                        pay = clean_currency(row[pay_idx], is_lakhs) if pay_idx != -1 else 0.0
                        cb = clean_currency(row[cb_idx], is_lakhs) if cb_idx != -1 else (tr - pay)

                        if ob == 0 and rec == 0 and tr == 0 and pay == 0 and cb == 0:
                            continue

                        key = (active_unit["code"], current_fy)
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

    print(f"\n[✓] PDF Annexure Extraction Complete:")
    print(f"    • Total Authorized Units in Scope : {len(whitelist)}")
    print(f"    • Verified Financial Statements   : {len(verified_records)} -> data/processed/financial_statements.json")
    print(f"    • Flagged Calculation Anomalies    : {len(discrepancies)} -> data/processed/audit_discrepancies.json")


if __name__ == "__main__":
    run_extraction()