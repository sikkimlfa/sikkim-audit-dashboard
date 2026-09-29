#!/usr/bin/env python3
"""
batch_extract_pdf.py - Enhanced Bulk Extraction Engine
Directorate of Local Fund Audit — Government of Sikkim

Fixes applied:
 - Precise Tier classification (ULB vs Zilla Panchayat vs Gram Panchayat)
 - Ignores NIL / Zero monetary records
 - Cleans and normalizes Local Body unit names (removes numbers, prefixes, noise)
"""

import sys
import json
import re
from pathlib import Path

try:
    import pdfplumber
    import pandas as pd
except ImportError:
    print("Error: Missing packages in active environment. Run 'pip install pdfplumber pandas'")
    sys.exit(1)


def clean_currency_val(val):
    """Strip currency symbols (₹), commas, 'nil', and whitespace into standard float."""
    if val is None or pd.isna(val):
        return 0.0
    
    val_str = str(val).strip().lower()
    if val_str in ['nil', 'null', '-', '--', 'n/a', '']:
        return 0.0

    if isinstance(val, (int, float)):
        return float(val)

    cleaned_str = re.sub(r'[^\d.-]', '', val_str)
    try:
        return float(cleaned_str)
    except ValueError:
        return 0.0


def clean_unit_name(raw_name):
    """Clean and normalize Local Body unit names."""
    if not raw_name:
        return ""

    # Replace newlines with spaces
    name = str(raw_name).replace('\n', ' ').strip()

    # Remove leading serial numbers like "1.", "01-", "Sl No 5", "1 )"
    name = re.sub(r'^(?:sl\.?\s*no\.?|sno\.?|\d+[\.\-\)]|\d+\s+)\s*', '', name, flags=re.IGNORECASE)

    # Remove repeated whitespaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Proper casing if string is ALL CAPS
    if name.isupper():
        name = name.title()

    return name


def detect_tier(unit_name):
    """Classify Local Body tier based on keyword analysis."""
    name_lower = unit_name.lower()

    if any(k in name_lower for k in ['zilla', 'zp', 'district panchayat']):
        return "Zilla Panchayat"
    elif any(k in name_lower for k in ['gram', 'gpu', 'gp', 'panchayat']):
        return "Gram Panchayat Unit"
    elif any(k in name_lower for k in ['municipal', 'corporation', 'gmc', 'council', 'nagar', 'ulb']):
        return "Urban Local Body"
    
    # Default fallback based on common Sikkim local body naming
    return "Gram Panchayat Unit" if "panchayat" in name_lower else "Urban Local Body"


def extract_tables_from_pdf(pdf_path):
    """Extract and normalize rows from a single PDF report."""
    extracted = []
    filename = pdf_path.name
    
    fy_match = re.search(r'20\d{2}[-_]\d{2,4}', filename)
    default_fy = fy_match.group(0).replace('_', '-') if fy_match else "2024-25"

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 4:
                        continue

                    # Header/Footer filter
                    row_str = " ".join([str(cell) for cell in row if cell])
                    if any(header in row_str.lower() for header in ["opening balance", "particulars", "total", "sl. no", "grand total"]):
                        continue

                    raw_unit = row[0] if row[0] else ''
                    unit_name = clean_unit_name(raw_unit)

                    # Filter out invalid name entries
                    if not unit_name or len(unit_name) < 3 or unit_name.isdigit():
                        continue

                    ob = clean_currency_val(row[1] if len(row) > 1 else 0)
                    receipts = clean_currency_val(row[2] if len(row) > 2 else 0)
                    payments = clean_currency_val(row[3] if len(row) > 3 else 0)

                    # FIX: Skip NIL records where all balances are zero
                    if ob == 0.0 and receipts == 0.0 and payments == 0.0:
                        continue

                    # FIX: Precise Tier assignment
                    tier = detect_tier(unit_name)

                    extracted.append({
                        "body": unit_name,
                        "tier": tier,
                        "year": default_fy,
                        "ob": ob,
                        "receipts": receipts,
                        "payments": payments,
                        "source_file": filename
                    })

    return extracted


def main():
    raw_dir = Path("data/raw")
    output_file = Path("data/processed/records.json")

    pdf_files = sorted(list(raw_dir.glob("*.pdf")) + list(raw_dir.glob("*.PDF")))

    if not pdf_files:
        print(f"[!] No PDF files found in {raw_dir.resolve()}")
        sys.exit(1)

    print(f"[*] Processing {len(pdf_files)} PDF reports from {raw_dir}/...")

    all_records = []
    for pdf in pdf_files:
        print(f"  -> Extracting & cleaning: {pdf.name}")
        records = extract_tables_from_pdf(pdf)
        all_records.extend(records)

    # Re-index clean records and calculate closing balance
    final_output = []
    for idx, rec in enumerate(all_records, start=1):
        cb = rec["ob"] + rec["receipts"] - rec["payments"]
        final_output.append({
            "id": idx,
            "body": rec["body"],
            "tier": rec["tier"],
            "year": rec["year"],
            "ob": round(rec["ob"], 2),
            "receipts": round(rec["receipts"], 2),
            "payments": round(rec["payments"], 2),
            "cb": round(cb, 2),
            "source": rec["source_file"]
        })

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Extracted {len(final_output)} non-nil records with tier classification.")
    print(f"[✓] File saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()