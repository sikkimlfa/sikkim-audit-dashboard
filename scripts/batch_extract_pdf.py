#!/usr/bin/env python3
"""
batch_extract_pdf.py - Audit Math Verifier & Extraction Engine
Directorate of Local Fund Audit — Government of Sikkim

Features:
 - Verifies Total Receipts = OB + Receipts
 - Verifies Closing Balance = Total Receipts - Payments
 - Separates verified records from mathematically inconsistent entries
 - Generates data/processed/records.json and data/processed/audit_discrepancies.json
"""

import sys
import json
import re
from pathlib import Path

try:
    import pdfplumber
    import pandas as pd
except ImportError:
    print("Error: Missing required packages. Run 'pip install pdfplumber pandas'")
    sys.exit(1)


def clean_val(val):
    """Clean monetary strings to float."""
    if val is None or pd.isna(val):
        return 0.0
    val_str = str(val).strip().lower()
    if val_str in ['nil', 'null', '-', '--', 'n/a', '']:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    cleaned = re.sub(r'[^\d.-]', '', val_str)
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def clean_unit_name(raw):
    """Normalize unit names."""
    if not raw:
        return ""
    name = str(raw).replace('\n', ' ').strip()
    name = re.sub(r'^(?:sl\.?\s*no\.?|sno\.?|\d+[\.\-\)]|\d+\s+)\s*', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s+', ' ', name).strip()
    return name.title() if name.isupper() else name


def detect_tier(unit_name):
    """
    Precise tier classification for Sikkim Local Bodies.
    Order matters: ULB specific terms (including Nagar Panchayat) must be checked BEFORE general 'panchayat'.
    """
    nl = unit_name.lower()

    # 1. Urban Local Bodies (ULBs) - Check Nagar Panchayat BEFORE Gram Panchayat!
    ulb_keywords = [
        'municipal', 'corporation', 'gmc', 'council', 'nagar panchayat', 
        'nagar', 'ulb', 'town', 'notified area', 'np', 'nmc', 'mc'
    ]
    if any(k in nl for k in ulb_keywords):
        return "Urban Local Body"

    # 2. Zilla Panchayats (ZPs)
    zilla_keywords = ['zilla', 'zp', 'district panchayat', 'district parishad', 'district']
    if any(k in nl for k in zilla_keywords):
        return "Zilla Panchayat"

    # 3. Gram Panchayat Units (GPUs)
    gpu_keywords = ['gram', 'gpu', 'gp', 'panchayat', 'unit', 'ward']
    if any(k in nl for k in gpu_keywords):
        return "Gram Panchayat Unit"

    # Default fallback for Sikkim rural units
    return "Gram Panchayat Unit"

def process_pdf_reports():
    raw_dir = Path("data/raw")
    pdf_files = sorted(list(raw_dir.glob("*.pdf")) + list(raw_dir.glob("*.PDF")))

    if not pdf_files:
        print(f"[!] No PDF files found in {raw_dir.resolve()}")
        sys.exit(1)

    verified_records = []
    discrepancy_records = []

    record_id = 1
    discrepancy_id = 1

    for pdf_path in pdf_files:
        filename = pdf_path.name
        fy_match = re.search(r'20\d{2}[-_]\d{2,4}', filename)
        fy = fy_match.group(0).replace('_', '-') if fy_match else "2024-25"

        print(f"[*] Auditing and extracting: {filename}")

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or len(row) < 5:
                            continue

                        row_str = " ".join([str(c) for c in row if c])
                        if any(h in row_str.lower() for h in ["opening balance", "particulars", "total", "sl. no", "grand total"]):
                            continue

                        unit_name = clean_unit_name(row[0])
                        if not unit_name or len(unit_name) < 3 or unit_name.isdigit():
                            continue

                        # Read Extracted Financial Values
                        ob = clean_val(row[1] if len(row) > 1 else 0)
                        receipts = clean_val(row[2] if len(row) > 2 else 0)
                        reported_total_receipts = clean_val(row[3] if len(row) > 3 else 0)
                        payments = clean_val(row[4] if len(row) > 4 else 0)
                        reported_cb = clean_val(row[5] if len(row) > 5 else 0)

                        # Skip completely empty/nil entries
                        if ob == 0 and receipts == 0 and payments == 0:
                            continue

                        tier = detect_tier(unit_name)

                        # Mathematical Verification Checks
                        expected_total_receipts = round(ob + receipts, 2)
                        
                        # Use reported total receipts if present; otherwise fallback to expected
                        effective_total_receipts = reported_total_receipts if reported_total_receipts > 0 else expected_total_receipts
                        expected_cb = round(effective_total_receipts - payments, 2)

                        # Check for math discrepancy (tolerance of 1.0 for rounding)
                        math_error = False
                        reason = []

                        if reported_total_receipts > 0 and abs(reported_total_receipts - expected_total_receipts) > 1.0:
                            math_error = True
                            reason.append(f"Total Receipts mismatch: Reported ₹{reported_total_receipts}, Expected ₹{expected_total_receipts} (OB+Receipts)")

                        if reported_cb > 0 and abs(reported_cb - expected_cb) > 1.0:
                            math_error = True
                            reason.append(f"Closing Balance mismatch: Reported ₹{reported_cb}, Expected ₹{expected_cb} (Total Receipts - Payments)")

                        item = {
                            "body": unit_name,
                            "tier": tier,
                            "year": fy,
                            "ob": round(ob, 2),
                            "receipts": round(receipts, 2),
                            "total_receipts": expected_total_receipts if reported_total_receipts == 0 else round(reported_total_receipts, 2),
                            "payments": round(payments, 2),
                            "cb": expected_cb if reported_cb == 0 else round(reported_cb, 2),
                            "source": filename
                        }

                        if math_error:
                            item["id"] = discrepancy_id
                            item["error_reason"] = " | ".join(reason)
                            item["expected_cb"] = expected_cb
                            item["expected_total_receipts"] = expected_total_receipts
                            discrepancy_records.append(item)
                            discrepancy_id += 1
                        else:
                            item["id"] = record_id
                            verified_records.append(item)
                            record_id += 1

    # Write output files
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    with open("data/processed/records.json", "w", encoding="utf-8") as f:
        json.dump(verified_records, f, indent=2, ensure_ascii=False)

    with open("data/processed/audit_discrepancies.json", "w", encoding="utf-8") as f:
        json.dump(discrepancy_records, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Audit Complete!")
    print(f"    • Verified Valid Records   : {len(verified_records)} -> data/processed/records.json")
    print(f"    • Flagged Discrepancies    : {len(discrepancy_records)} -> data/processed/audit_discrepancies.json")


if __name__ == "__main__":
    process_pdf_reports()