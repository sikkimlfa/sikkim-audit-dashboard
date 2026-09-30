#!/usr/bin/env python3
"""
analyze_data.py - Year-over-Year Comparative Analytics
Directorate of Local Fund Audit — Government of Sikkim
"""

import json
from pathlib import Path
from collections import defaultdict


def main():
    data_file = Path("data/processed/financial_statements.json")
    disc_file = Path("data/processed/audit_discrepancies.json")

    if not data_file.exists():
        print(f"[!] Data file missing: {data_file.resolve()}. Run extraction or sanitization first.")
        return

    with open(data_file, "r", encoding="utf-8") as f:
        records = json.load(f)

    discrepancies = []
    if disc_file.exists():
        with open(disc_file, "r", encoding="utf-8") as f:
            discrepancies = json.load(f)

    print("=" * 115)
    print("      DIRECTORATE OF LOCAL FUND AUDIT — FINANCIAL STATEMENT ANALYSIS & COMPARATIVE AUDIT METRICS")
    print("=" * 115)
    print(f"Total Validated Statements: {len(records)} | Isolated Math Discrepancies: {len(discrepancies)}\n")

    analysis = defaultdict(lambda: {
        "units": 0,
        "ob": 0.0,
        "receipts": 0.0,
        "total_receipts": 0.0,
        "payments": 0.0,
        "cb": 0.0
    })

    fy_set = set()
    tier_set = set()

    for r in records:
        key = (r["fy"], r["tier"])
        fy_set.add(r["fy"])
        tier_set.add(r["tier"])

        analysis[key]["units"] += 1
        analysis[key]["ob"] += r["ob"]
        analysis[key]["receipts"] += r["receipts"]
        analysis[key]["total_receipts"] += r["total_receipts"]
        analysis[key]["payments"] += r["payments"]
        analysis[key]["cb"] += r["cb"]

    header = f"{'Financial Year':<14} | {'Tier Category':<22} | {'Units':<6} | {'Total Receipts (₹)':<20} | {'Payments (₹)':<18} | {'Utilization %':<12}"
    print(header)
    print("-" * len(header))

    grand_total_tr = 0.0
    grand_total_pay = 0.0

    for (fy, tier), v in sorted(analysis.items()):
        utilization = (v["payments"] / v["total_receipts"] * 100) if v["total_receipts"] > 0 else 0.0
        grand_total_tr += v["total_receipts"]
        grand_total_pay += v["payments"]
        print(f"{fy:<14} | {tier:<22} | {v['units']:<6} | ₹{v['total_receipts']:>18,.2f} | ₹{v['payments']:>16,.2f} | {utilization:>10.2f}%")

    print("-" * len(header))
    grand_util = (grand_total_pay / grand_total_tr * 100) if grand_total_tr > 0 else 0.0
    print(f"{'OVERALL TOTAL':<14} | {'All Tiers Combined':<22} | {len(records):<6} | ₹{grand_total_tr:>18,.2f} | ₹{grand_total_pay:>16,.2f} | {grand_util:>10.2f}%\n")

    # High-level summary by tier across all financial years
    print("=== Cumulative Position by Local Body Tier ===")
    tier_summary = defaultdict(lambda: {"units": 0, "tr": 0.0, "pay": 0.0, "cb": 0.0})
    for r in records:
        t = r["tier"]
        tier_summary[t]["units"] += 1
        tier_summary[t]["tr"] += r["total_receipts"]
        tier_summary[t]["pay"] += r["payments"]
        tier_summary[t]["cb"] += r["cb"]

    for t, vals in sorted(tier_summary.items()):
        t_util = (vals["pay"] / vals["tr"] * 100) if vals["tr"] > 0 else 0.0
        print(f"  • {t:<22}: {vals['units']} records | Gross Receipts: ₹{vals['tr']:,.2f} | Payments: ₹{vals['pay']:,.2f} | Unspent CB: ₹{vals['cb']:,.2f} (Util: {t_util:.1f}%)")


if __name__ == "__main__":
    main()