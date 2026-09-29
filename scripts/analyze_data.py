#!/usr/bin/env python3
"""
analyze_data.py - Year-over-Year Comparative Analytics
Directorate of Local Fund Audit — Government of Sikkim
"""

import json
from pathlib import Path
from collections import defaultdict

data_file = Path("data/processed/financial_statements.json")
if not data_file.exists():
    print("Run scripts/extract_annexures.py first!")
    exit(1)

with open(data_file, "r") as f:
    records = json.load(f)

# Aggregate metrics by (FY, Tier)
analysis = defaultdict(lambda: {"units": 0, "ob": 0.0, "receipts": 0.0, "total_receipts": 0.0, "payments": 0.0, "cb": 0.0})

for r in records:
    key = (r["fy"], r["tier"])
    analysis[key]["units"] += 1
    analysis[key]["ob"] += r["ob"]
    analysis[key]["receipts"] += r["receipts"]
    analysis[key]["total_receipts"] += r["total_receipts"]
    analysis[key]["payments"] += r["payments"]
    analysis[key]["cb"] += r["cb"]

print(f"{'Financial Year':<12} | {'Tier':<22} | {'Units':<6} | {'Total Receipts (₹)':<20} | {'Payments (₹)':<18} | {'Utilization %':<12}")
print("-" * 105)

for (fy, tier), v in sorted(analysis.items()):
    utilization = (v["payments"] / v["total_receipts"] * 100) if v["total_receipts"] > 0 else 0.0
    print(f"{fy:<12} | {tier:<22} | {v['units']:<6} | ₹{v['total_receipts']:>18,.2f} | ₹{v['payments']:>16,.2f} | {utilization:>10.2f}%")