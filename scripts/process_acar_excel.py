#!/usr/bin/env python3
"""
process_acar_excel.py - Ingest & Sanitize ACAR FS Excel Workbooks
Directorate of Local Fund Audit — Government of Sikkim
"""

import re
import json
from pathlib import Path
from collections import defaultdict
import pandas as pd
import numpy as np

from extract_annexures import (
    load_audit_whitelist,
    match_against_whitelist,
    clean_currency,
    detect_fy
)


def find_header_row(df_raw):
    """Scan the first 12 rows to locate the actual table header."""
    for idx, row in df_raw.head(12).iterrows():
        row_str = " ".join([str(c).lower() for c in row.values if pd.notna(c)])
        if any(k in row_str for k in ['opening', 'receipt', 'payment', 'expenditure', 'closing', 'gpu', 'zilla', 'local body', 'particular']):
            return idx
    return 0


def process_excel_sheet(excel_path, sheet_name, whitelist):
    print(f"  -> Reading sheet: [{sheet_name}]")
    try:
        raw_df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    except Exception as e:
        print(f"     [!] Failed to read sheet [{sheet_name}]: {e}")
        return [], []

    if raw_df.empty or len(raw_df) < 3:
        return [], []

    header_idx = find_header_row(raw_df)
    df = pd.read_excel(excel_path, sheet_name=sheet_name, skiprows=header_idx)
    df.columns = [str(c).strip().lower().replace('\n', ' ').replace('_', ' ') for c in df.columns]

    sheet_context = f"{sheet_name} " + " ".join(df.columns)
    is_lakhs = bool(re.search(r'lakh', sheet_context, re.IGNORECASE))

    unit_col = next((c for c in df.columns if any(k in c for k in ['gram panchayat', 'unit', 'gpu', 'zilla', 'name', 'local body', 'particular', 'institution'])), None)
    ob_col = next((c for c in df.columns if 'opening' in c), None)
    rec_col = next((c for c in df.columns if 'receipt' in c and 'total' not in c), None)
    int_col = next((c for c in df.columns if 'interest' in c), None)
    tr_col = next((c for c in df.columns if 'total receipt' in c), None)
    pay_col = next((c for c in df.columns if any(k in c for k in ['payment', 'expenditure'])), None)
    trans_col = next((c for c in df.columns if any(k in c for k in ['transfer', 'remittance', 'surrender'])), None)
    cb_col = next((c for c in df.columns if 'closing' in c), None)
    fy_col = next((c for c in df.columns if any(k in c for k in ['fy', 'year', 'financial year'])), None)

    if not unit_col:
        print(f"     [!] No unit name column detected in [{sheet_name}]. Skipping.")
        return [], []

    is_summary = df[unit_col].astype(str).str.lower().str.contains(r'total|grand\s*total|sub\s*total|sl\.\s*no', regex=True)

    # Forward fill blank unit names from merged cells
    df[unit_col] = df[unit_col].replace(r'^\s*$', np.nan, regex=True)
    df.loc[is_summary, unit_col] = np.nan
    df[unit_col] = df[unit_col].ffill()

    # Drop summary rows
    df = df[~is_summary].copy()

    default_fy = detect_fy(sheet_name) or detect_fy(sheet_context) or "2024-25"

    df['clean_ob'] = df[ob_col].apply(lambda x: clean_currency(x, is_lakhs)) if ob_col else 0.0
    df['clean_rec'] = df[rec_col].apply(lambda x: clean_currency(x, is_lakhs)) if rec_col else 0.0
    df['clean_int'] = df[int_col].apply(lambda x: clean_currency(x, is_lakhs)) if int_col else 0.0
    df['clean_tr'] = df[tr_col].apply(lambda x: clean_currency(x, is_lakhs)) if tr_col else 0.0
    df['clean_pay'] = df[pay_col].apply(lambda x: clean_currency(x, is_lakhs)) if pay_col else 0.0
    df['clean_trans'] = df[trans_col].apply(lambda x: clean_currency(x, is_lakhs)) if trans_col else 0.0
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

    verified = []
    discrepancies = []

    for _, row in grouped.iterrows():
        raw_name = str(row[unit_col]).strip()
        if not raw_name or raw_name.lower() in ['nan', 'none', '']:
            continue

        matched = match_against_whitelist(raw_name, whitelist)
        if not matched:
            continue

        ob = round(row['clean_ob'], 2)
        rec = round(row['clean_rec'], 2)
        reported_tr = round(row['clean_tr'], 2)
        pay = round(row['clean_pay'], 2)
        reported_cb = round(row['clean_cb'], 2)

        if ob == 0 and rec == 0 and pay == 0 and reported_cb == 0:
            continue

        expected_tr = round(ob + rec, 2)
        effective_tr = reported_tr if reported_tr > 0 else expected_tr
        expected_cb = round(effective_tr - pay, 2)

        math_ok = True
        violations = []
        if reported_tr > 0 and abs(reported_tr - expected_tr) > 2.0:
            math_ok = False
            violations.append(f"TR Mismatch: Reported ₹{reported_tr:,.2f} != Expected ₹{expected_tr:,.2f}")
        if reported_cb != 0 and abs(reported_cb - expected_cb) > 2.0:
            math_ok = False
            violations.append(f"CB Mismatch: Reported ₹{reported_cb:,.2f} != Expected ₹{expected_cb:,.2f}")

        entry = {
            "code": matched["code"],
            "name": matched["name"],
            "district": matched["district"],
            "bac": matched.get("bac", "N/A"),
            "tier": matched["tier"],
            "fy": row['standard_fy'],
            "ob": ob,
            "receipts": rec,
            "total_receipts": effective_tr,
            "payments": pay,
            "cb": reported_cb if reported_cb != 0 else expected_cb,
            "source": f"{excel_path.name} [{sheet_name}]"
        }

        if math_ok:
            verified.append(entry)
        else:
            entry["expected_tr"] = expected_tr
            entry["expected_cb"] = expected_cb
            entry["error_reason"] = " | ".join(violations)
            discrepancies.append(entry)

    return verified, discrepancies


def main():
    whitelist = load_audit_whitelist()
    raw_dir = Path("data/raw")
    if not raw_dir.exists():
        raw_dir = Path(".")

    excel_files = list(raw_dir.glob("*.xls")) + list(raw_dir.glob("*.xlsx"))
    excel_files = [f for f in excel_files if "audit_plan" not in f.name.lower() and "annual_plan" not in f.name.lower()]

    if not excel_files:
        print(f"[!] No target Excel workbooks found in {raw_dir.resolve()}.")
        return

    all_verified = []
    all_disc = []

    for xl_file in excel_files:
        print(f"\n[*] Processing Workbook: {xl_file.name}")
        excel_obj = pd.ExcelFile(xl_file)
        for sheet in excel_obj.sheet_names:
            v, d = process_excel_sheet(xl_file, sheet, whitelist)
            all_verified.extend(v)
            all_disc.extend(d)

    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "financial_statements.json", "w", encoding="utf-8") as f:
        json.dump(all_verified, f, indent=2, ensure_ascii=False)

    with open(out_dir / "audit_discrepancies.json", "w", encoding="utf-8") as f:
        json.dump(all_disc, f, indent=2, ensure_ascii=False)

    print("\n[✓] Excel Ingestion Complete:")
    print(f"    • Verified Financial Records : {len(all_verified)} -> data/processed/financial_statements.json")
    print(f"    • Flagged Math Discrepancies : {len(all_disc)} -> data/processed/audit_discrepancies.json")


if __name__ == "__main__":
    main()