#!/usr/bin/env python3
"""
extract_annual_reports.py - Annual Report Data Extraction Engine
Directorate of Local Fund Audit — Government of Sikkim

Description:
    Extracts financial reconciliation tables from Annual Audit Reports (.pdf)
    as well as raw spreadsheets (.xlsx, .csv) located in data/raw/.
    Normalizes local body names, cleans monetary values, calculates balances,
    and outputs dynamic JSON data into data/processed/records.json for index.html.

Usage:
    python3 scripts/extract_annual_reports.py -i data/raw/Annual_Report_2024_25.pdf -o data/processed/records.json
"""

import sys
import json
import argparse
import re
from pathlib import Path

try:
    import pandas as pd
    import pdfplumber
except ImportError:
    print("Error: Missing required packages. Run: pip install -r requirements.txt")
    sys.exit(1)


def clean_currency_val(val):
    """Strip currency symbols (₹), commas, and whitespace into standard float."""
    if pd.isna(val) or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    
    cleaned_str = re.sub(r'[^\d.-]', '', str(val)).strip()
    try:
        return float(cleaned_str)
    except ValueError:
        return 0.0


def extract_from_pdf(pdf_path):
    """Extract financial audit tables from Annual Report PDF pages."""
    extracted_rows = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Filter out empty or header rows
                    if not row or len(row) < 5 or "Opening Balance" in str(row) or "Local Body" in str(row):
                        continue
                    
                    # Assume typical audit table layout: [Local Body, Tier, FY, OB, Receipts, Payments]
                    body = str(row[0]).replace('\n', ' ').strip() if row[0] else ''
                    tier = str(row[1]).replace('\n', ' ').strip() if len(row) > 1 and row[1] else 'Urban Local Body'
                    year = str(row[2]).strip() if len(row) > 2 and row[2] else '2024-25'
                    
                    if not body or len(body) < 3:
                        continue

                    ob = clean_currency_val(row[3] if len(row) > 3 else 0)
                    receipts = clean_currency_val(row[4] if len(row) > 4 else 0)
                    payments = clean_currency_val(row[5] if len(row) > 5 else 0)

                    extracted_rows.append({
                        "body": body,
                        "tier": tier,
                        "year": year,
                        "ob": ob,
                        "receipts": receipts,
                        "payments": payments
                    })

    return extracted_rows


def extract_from_spreadsheet(filepath):
    """Extract financial records from Excel (.xlsx) or CSV files."""
    file_path = Path(filepath)
    if file_path.suffix.lower() in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    df.columns = [str(col).strip().lower() for col in df.columns]

    column_mapping = {
        'body': ['local body', 'local body name', 'body', 'name', 'municipality', 'panchayat'],
        'tier': ['tier', 'level', 'type', 'category'],
        'year': ['financial year', 'fy', 'year', 'period'],
        'ob': ['opening balance', 'opening bal', 'ob', 'opening_balance'],
        'receipts': ['receipts', 'receipt', 'income', 'total_receipts'],
        'payments': ['payments', 'payment', 'expenditure', 'total_payments']
    }

    mapped_cols = {}
    for target_key, synonyms in column_mapping.items():
        for col in df.columns:
            if col in synonyms:
                mapped_cols[target_key] = col
                break

    records = []
    for idx, row in df.iterrows():
        body_name = str(row.get(mapped_cols.get('body', ''), f"Local Body #{idx + 1}")).strip()
        tier_name = str(row.get(mapped_cols.get('tier', ''), "Urban Local Body")).strip()
        fy = str(row.get(mapped_cols.get('year', ''), "2024-25")).strip()

        ob_val = clean_currency_val(row.get(mapped_cols.get('ob', 0)))
        receipts_val = clean_currency_val(row.get(mapped_cols.get('receipts', 0)))
        payments_val = clean_currency_val(row.get(mapped_cols.get('payments', 0)))

        records.append({
            "body": body_name,
            "tier": tier_name,
            "year": fy,
            "ob": ob_val,
            "receipts": receipts_val,
            "payments": payments_val
        })

    return records


def process_report(input_file, output_file):
    """Main transformation pipeline."""
    input_path = Path(input_file)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input report not found: {input_file}")

    print(f"[*] Processing annual report file: {input_path}")

    if input_path.suffix.lower() == '.pdf':
        raw_records = extract_from_pdf(input_path)
    elif input_path.suffix.lower() in ['.xlsx', '.xls', '.csv']:
        raw_records = extract_from_spreadsheet(input_path)
    else:
        raise ValueError("Unsupported format. Input must be .pdf, .xlsx, or .csv")

    # Format output array and calculate Closing Balances
    final_records = []
    for idx, rec in enumerate(raw_records, start=1):
        cb = rec["ob"] + rec["receipts"] - rec["payments"]
        final_records.append({
            "id": idx,
            "body": rec["body"],
            "tier": rec["tier"],
            "year": rec["year"],
            "ob": round(rec["ob"], 2),
            "receipts": round(rec["receipts"], 2),
            "payments": round(rec["payments"], 2),
            "cb": round(cb, 2)
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2, ensure_ascii=False)

    print(f"[✓] Extracted {len(final_records)} records to dynamic data endpoint: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract Annual Report data for Sikkim LFA Dashboard.")
    parser.add_argument("-i", "--input", required=True, help="Path to input annual report (.pdf, .xlsx, .csv)")
    parser.add_argument("-o", "--output", default="data/processed/records.json", help="Output path for dynamic dashboard JSON")

    args = parser.parse_args()

    try:
        process_report(args.input, args.output)
    except Exception as e:
        print(f"[X] Extraction Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()