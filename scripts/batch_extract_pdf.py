#!/usr/bin/env python3
"""
batch_extract_pdf.py - Bulk Annual Report Extraction Engine
Directorate of Local Fund Audit — Government of Sikkim

Description:
    Processes all PDF annual reports inside `data/raw/`, extracts audit tables,
    normalizes numbers, calculates closing balances, and generates a unified
    `data/processed/records.json` dataset for index.html.
"""

import sys
import json
import re
from pathlib import Path

try:
    import pdfplumber
    import pandas as pd
except ImportError:
    print("Error: Required packages missing. Run: pip install pdfplumber pandas")
    sys.exit(1)


def clean_currency_val(val):
    """Strip currency symbols (₹), commas, and spaces into standard float."""
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    cleaned_str = re.sub(r'[^\d.-]', '', str(val)).strip()
    try:
        return float(cleaned_str)
    except ValueError:
        return 0.0


def extract_tables_from_pdf(pdf_path):
    """Extract structured rows from a single PDF annual report."""
    extracted = []
    filename = pdf_path.name
    
    # Extract Financial Year from filename if present (e.g., Report_2024-25.pdf)
    fy_match = re.search(r'20\d{2}[-_]\d{2,4}', filename)
    default_fy = fy_match.group(0).replace('_', '-') if fy_match else "2024-25"

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    
                    row_str = " ".join([str(cell) for cell in row if cell])
                    
                    # Skip header/footer noise
                    if any(header in row_str.lower() for header in ["opening balance", "particulars", "total", "sl. no"]):
                        continue
                    
                    body = str(row[0]).replace('\n', ' ').strip() if row[0] else ''
                    if not body or len(body) < 3 or body.isdigit():
                        continue

                    # Tier detection logic
                    tier = "Zilla Panchayat" if "zilla" in body.lower() or "gram" in body.lower() else "Urban Local Body"
                    
                    ob = clean_currency_val(row[1] if len(row) > 1 else 0)
                    receipts = clean_currency_val(row[2] if len(row) > 2 else 0)
                    payments = clean_currency_val(row[3] if len(row) > 3 else 0)

                    extracted.append({
                        "body": body,
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

    print(f"[*] Found {len(pdf_files)} PDF reports in {raw_dir}/. Starting extraction...")

    all_records = []
    for pdf in pdf_files:
        print(f"  -> Extracting: {pdf.name}")
        records = extract_tables_from_pdf(pdf)
        all_records.extend(records)

    # Format output array with IDs and calculated Closing Balances
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

    print(f"\n[✓] Successfully extracted {len(final_output)} audit records from {len(pdf_files)} PDF files.")
    print(f"[✓] Compiled dataset written to: {output_file.resolve()}")


if __name__ == "__main__":
    main()