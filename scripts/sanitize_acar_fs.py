#!/usr/bin/env python3
"""
sanitize_acar_fs.py - Master Sanitization Pipeline for Sikkim DLFA Financial Data
Directorate of Local Fund Audit — Government of Sikkim
"""

import re
import json
import difflib
from pathlib import Path
import pandas as pd
import numpy as np

# Master lookup mapping all historical spellings, shorthand, and BAC list prefixes
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


def load_master_whitelist():
    """Load canonical list of 212 units from the audit plan."""
    plan_path = Path("data/raw/annual_audit_plan_2026.json")
    if not plan_path.exists():
        raise FileNotFoundError(f"Missing master whitelist at: {plan_path.resolve()}")
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_unit_string(s):
    """Clean serial numbers, BAC list numbers, and punctuation."""
    if not s or pd.isna(s):
        return ""
    text = str(s).strip().lower()
    text = re.sub(r'^(?:sl\.?\s*no\.?|sno\.?|\d+[\.\-\)]|\d+\s*[-/]?\s*)\s*', '', text)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def normalize_clean_string(s):
    """Normalize and map phonetics."""
    if not s:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', str(s)).lower()
    for key, target in SPELLING_ALIASES.items():
        if key in cleaned:
            cleaned = cleaned.replace(key, target)
    return cleaned


def resolve_canonical_unit(raw_name, whitelist):
    """Match raw name strings against canonical units."""
    if not raw_name or pd.isna(raw_name):
        return None

    cleaned_raw = clean_unit_string(raw_name)
    if len(cleaned_raw) < 3:
        return None

    if cleaned_raw in EXPLICIT_NAME_TO_CODE:
        code = EXPLICIT_NAME_TO_CODE[cleaned_raw]
        for u in whitelist:
            if u["code"] == code:
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
    matches = difflib.get_close_matches(str(raw_name).strip(), whitelist_names, n=1, cutoff=0.72)
    if matches:
        for u in whitelist:
            if u["name"] == matches[0]:
                return u

    return None


def clean_currency(val, is_lakhs=False):
    """Parse numeric values, convert parentheses to negative, and scale Lakhs to Rupees."""
    if val is None or pd.isna(val):
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
    """Bound Financial Years strictly between 2015-16 and 2025-26."""
    if not text or pd.isna(text):
        return None
    match = re.search(r'\b(20(?:1[5-9]|2[0-5]))[-–/](\d{2,4})\b', str(text))
    if match:
        start_yr = match.group(1)
        end_yr = match.group(2)
        if len(end_yr) == 4:
            end_yr = end_yr[2:]
        return f"{start_yr}-{end_yr}"
    return None


def sanitize_dataframe(df, source_label, whitelist):
    """Process merged rows, fill blank units, remove totals, and aggregate."""
    if df.empty or len(df) < 2:
        return [], []

    df.columns = [str(c).strip().lower().replace('\n', ' ').replace('_', ' ') for c in df.columns]

    unit_col = next((c for c in df.columns if any(k in c for k in ['gram panchayat', 'unit', 'gpu', 'zilla', 'name', 'local body', 'particular', 'institution'])), None)
    ob_col = next((c for c in df.columns if 'opening' in c), None)
    rec_col = next((c for c in df.columns if 'receipt' in c and 'total' not in c), None)
    int_col = next((c for c in df.columns if 'interest' in c), None)
    tr_col = next((c for c in df.columns if 'total receipt' in c), None)
    pay_col = next((c for c in df.columns if any(k in c for k in ['payment', 'expenditure'])), None)
    transfer_col = next((c for c in df.columns if any(k in c for k in ['transfer', 'remittance', 'surrender'])), None)
    cb_col = next((c for c in df.columns if 'closing' in c), None)
    fy_col = next((c for c in df.columns if any(k in c for k in ['fy', 'year', 'financial year'])), None)

    if not unit_col:
        print(f"     [!] Unit column not identified in {source_label}. Skipping.")
        return [], []

    is_summary = df[unit_col].astype(str).str.lower().str.contains(r'total|grand\s*total|sub\s*total|sl\.\s*no', regex=True)

    # Forward-fill: Assigns preceding unit name to rows with blank unit names
    df[unit_col] = df[unit_col].replace(r'^\s*$', np.nan, regex=True)
    df.loc[is_summary, unit_col] = np.nan
    df[unit_col] = df[unit_col].ffill()

    # Drop summary rows
    df = df[~is_summary].copy()

    context_text = f"{source_label} " + " ".join(df.columns)
    is_lakhs = bool(re.search(r'lakh', context_text, re.IGNORECASE))
    
    if not is_lakhs and ob_col:
        sample_vals = df[ob_col].dropna().apply(lambda x: clean_currency(x, False))
        if len(sample_vals) > 0 and 0 < sample_vals.median() < 1000:
            is_lakhs = True

    default_fy = detect_fy(source_label) or detect_fy(context_text) or "2024-25"

    df['clean_ob'] = df[ob_col].apply(lambda x: clean_currency(x, is_lakhs)) if ob_col else 0.0
    df['clean_rec'] = df[rec_col].apply(lambda x: clean_currency(x, is_lakhs)) if rec_col else 0.0
    df['clean_int'] = df[int_col].apply(lambda x: clean_currency(x, is_lakhs)) if int_col else 0.0
    df['clean_tr'] = df[tr_col].apply(lambda x: clean_currency(x, is_lakhs)) if tr_col else 0.0
    df['clean_pay'] = df[pay_col].apply(lambda x: clean_currency(x, is_lakhs)) if pay_col else 0.0
    df['clean_trans'] = df[transfer_col].apply(lambda x: clean_currency(x, is_lakhs)) if transfer_col else 0.0
    df['clean_cb'] = df[cb_col].apply(lambda x: clean_currency(x, is_lakhs)) if cb_col else 0.0

    df['clean_rec'] = df['clean_rec'] + df['clean_int']
    df['clean_pay'] = df['clean_pay'] + df['clean_trans']

    def resolve_row_fy(row):
        val = row.get(fy_col, '') if fy_col else ''
        parsed = detect_fy(val)
        return parsed if parsed else default_fy

    df['standard_fy'] = df.apply(resolve_row_fy, axis=1)

    grouped = df.groupby([unit_col, 'standard_fy'], as_index=False).agg({
        'clean_ob': 'sum',
        'clean_rec': 'sum',
        'clean_tr': 'sum',
        'clean_pay': 'sum',
        'clean_cb': 'sum'
    })

    verified_records = []
    discrepancy_records = []

    for _, row in grouped.iterrows():
        raw_u = row[unit_col]
        canonical = resolve_canonical_unit(raw_u, whitelist)
        if not canonical:
            continue

        ob = round(row['clean_ob'], 2)
        rec = round(row['clean_rec'], 2)
        reported_tr = round(row['clean_tr'], 2)
        pay = round(row['clean_pay'], 2)
        reported_cb = round(row['clean_cb'], 2)

        expected_tr = round(ob + rec, 2)
        effective_tr = reported_tr if reported_tr > 0 else expected_tr
        expected_cb = round(effective_tr - pay, 2)

        math_valid = True
        violations = []

        if reported_tr > 0 and abs(reported_tr - expected_tr) > 2.0:
            math_valid = False
            violations.append(f"TR Mismatch: Reported ₹{reported_tr:,.2f} != Expected ₹{expected_tr:,.2f}")

        if reported_cb != 0 and abs(reported_cb - expected_cb) > 2.0:
            math_valid = False
            violations.append(f"CB Mismatch: Reported ₹{reported_cb:,.2f} != Expected ₹{expected_cb:,.2f}")

        record = {
            "code": canonical["code"],
            "name": canonical["name"],
            "district": canonical["district"],
            "bac": canonical.get("bac", "N/A"),
            "tier": canonical["tier"],
            "fy": row['standard_fy'],
            "ob": ob,
            "receipts": rec,
            "total_receipts": effective_tr,
            "payments": pay,
            "cb": reported_cb if reported_cb != 0 else expected_cb,
            "source": source_label
        }

        if math_valid:
            verified_records.append(record)
        else:
            record["expected_tr"] = expected_tr
            record["expected_cb"] = expected_cb
            record["audit_violation"] = " | ".join(violations)
            discrepancy_records.append(record)

    return verified_records, discrepancy_records


def main():
    print("=" * 75)
    print("  Directorate of Local Fund Audit — Master File Sanitization Engine")
    print("=" * 75)

    whitelist = load_master_whitelist()
    print(f"[✓] Loaded Master Audit Plan whitelist ({len(whitelist)} units).")

    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raw_dir = Path(".")

    candidate_files = (
        list(raw_dir.glob("ACAR*.csv")) +
        list(raw_dir.glob("*.csv")) +
        list(raw_dir.glob("*.xls")) +
        list(raw_dir.glob("*.xlsx"))
    )
    
    target_files = [f for f in candidate_files if "audit_plan" not in f.name.lower() and "annual_plan" not in f.name.lower()]

    if not target_files:
        print("[!] No target ACAR data files found in data/raw/ or current directory.")
        return

    all_verified = []
    all_discrepancies = []

    for file_path in target_files:
        print(f"\n[*] Processing: {file_path.name}")
        try:
            if file_path.suffix.lower() in ['.xls', '.xlsx']:
                xl = pd.ExcelFile(file_path)
                for sheet in xl.sheet_names:
                    print(f"    -> Sheet: {sheet}")
                    raw_preview = pd.read_excel(file_path, sheet_name=sheet, header=None, nrows=12)
                    skip_rows = 0
                    for idx, row in raw_preview.iterrows():
                        r_str = " ".join([str(c).lower() for c in row.values if pd.notna(c)])
                        if any(k in r_str for k in ['opening', 'receipt', 'payment', 'closing', 'gpu', 'unit']):
                            skip_rows = idx
                            break
                    sheet_df = pd.read_excel(file_path, sheet_name=sheet, skiprows=skip_rows)
                    v, d = sanitize_dataframe(sheet_df, f"{file_path.name} [{sheet}]", whitelist)
                    all_verified.extend(v)
                    all_discrepancies.extend(d)
            else:
                df = pd.read_csv(file_path)
                v, d = sanitize_dataframe(df, file_path.name, whitelist)
                all_verified.extend(v)
                all_discrepancies.extend(d)
        except Exception as e:
            print(f"     [!] Failed to process {file_path.name}: {e}")

    # Deduplicate keeping highest receipts record if duplicate (code, fy) exists
    if all_verified:
        v_df = pd.DataFrame(all_verified)
        v_df = v_df.sort_values('total_receipts', ascending=False).drop_duplicates(subset=['code', 'fy']).sort_values(['tier', 'name', 'fy'])
        all_verified = v_df.to_dict(orient='records')

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_json = out_dir / "financial_statements.json"
    clean_csv = out_dir / "clean_financial_statements.csv"
    disc_json = out_dir / "audit_discrepancies.json"
    disc_csv = out_dir / "sanitization_discrepancies.csv"

    with open(clean_json, "w", encoding="utf-8") as f:
        json.dump(all_verified, f, indent=2, ensure_ascii=False)
    pd.DataFrame(all_verified).to_csv(clean_csv, index=False)

    with open(disc_json, "w", encoding="utf-8") as f:
        json.dump(all_discrepancies, f, indent=2, ensure_ascii=False)
    pd.DataFrame(all_discrepancies).to_csv(disc_csv, index=False)

    print("\n" + "=" * 75)
    print(f"[✓] Sanitization Complete:")
    print(f"    • Verified Financial Records : {len(all_verified)} -> {clean_json}")
    print(f"    • Exported Clean CSV         : {clean_csv}")
    print(f"    • Flagged Math Discrepancies : {len(all_discrepancies)} -> {disc_json}")
    print("=" * 75)


if __name__ == "__main__":
    main()