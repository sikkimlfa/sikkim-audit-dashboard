# 📊 Directorate of Local Fund Audit — Sikkim Dashboard

[![GitHub release](https://img.shields.io/github/v/release/Sikkimlfa/sikkim-audit-dashboard?include_prereleases&color=blue&style=flat-square)](https://github.com/Sikkimlfa/sikkim-audit-dashboard/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Repository Size](https://img.shields.io/github/repo-size/Sikkimlfa/sikkim-audit-dashboard?style=flat-square&color=informational)](https://github.com/Sikkimlfa/sikkim-audit-dashboard)
[![Last Commit](https://img.shields.io/github/last-commit/Sikkimlfa/sikkim-audit-dashboard?style=flat-square&color=success)](https://github.com/Sikkimlfa/sikkim-audit-dashboard/commits/main)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live%20Dashboard-brightgreen?style=flat-square&logo=github)](https://Sikkimlfa.github.io/sikkim-audit-dashboard/)

Automated extraction, strict mathematical reconciliation, and executive analytics dashboard built for the **Directorate of Local Fund Audit, Government of Sikkim**. 

The pipeline digitizes Consolidated Annual Audit Reports across 11+ financial years, enforcing strict whitelist verification across **212 sanctioned Local Bodies** (199 Gram Panchayat Units, 6 Zilla Panchayats, and 7 Urban Local Bodies)[cite: 12].

---

## 🗂 Project Structure

```text
sikkim-audit-dashboard/
├── .github/
│   └── workflows/
│       └── deploy.yml              # CI/CD: Automated GitHub Pages deployment
├── data/
│   ├── raw/
│   │   ├── annual_audit_plan_2026.json  # Official whitelist of 212 mandated units
│   │   └── .gitkeep                # Directory for raw Annual Report PDFs
│   └── processed/
│       ├── financial_statements.json    # Verified audit records (OB, Receipts, TR, Payments, CB)
│       └── audit_discrepancies.json     # Mathematical discrepancies isolated from source PDFs
├── reports/
│   └── .gitkeep                    # Generated CSVs and discrepancy summary memos
├── scripts/
│   ├── generate_master_units.py    # Generates canonical 212-unit whitelist database
│   ├── extract_annexures.py        # Whitelist-based PDF parsing & math verification engine
│   └── analyze_data.py             # Multi-year comparative trends and KPI summaries
├── index.html                      # Executive SPA dashboard (Chart.js & Tailwind CSS)
├── requirements.txt                # Python library dependencies
├── LICENSE                         # MIT License
├── README.md                       # Repository overview and setup guide
├── INSTALL.md                      # Detailed environment installation instructions
├── TROUBLESHOOTING.md              # Common errors, regex edge cases, and remedies
└── CONTRIBUTING.md                 # Public-sector contribution standards & PR workflows

```

---

## ⚡ Core Features

* **Strict Audit Whitelist Enforcement:** Restricts data extraction to the 212 statutory units defined in the Annual Audit Plan 2026–27.


* **Annexure & Appendix Resolution:** Intelligently maps Gram Panchayat Units (Annexure 1 & 2 / Appendix II), Zilla Panchayats (Annexure 3 / Appendix III), and Municipalities (Annexures 4–6 / Appendix IV & V).


* **Legacy & Orthographic Harmonization:** Automatically normalizes historical district nomenclature (`East` $\rightarrow$ `Gangtok`, `West` $\rightarrow$ `Gyalshing`, `North` $\rightarrow$ `Mangan`, `South` $\rightarrow$ `Namchi`) and phonetic spelling variants (*Geyzing* vs *Gyalshing*, *Yoksum* vs *Yuksom*)[cite: 3, 4, 5, 8, 9, 11, 12].
* **Double Mathematical Safeguard:**

$$\text{Total Receipts} = \text{Opening Balance (OB)} + \text{Receipts}$$


$$\text{Closing Balance (CB)} = \text{Total Receipts} - \text{Payments}$$


* **Discrepancy Drawer Isolation:** Records failing mathematical validation ($\Delta > ₹2.00$) are sequestered into `audit_discrepancies.json` and reviewed through a dedicated dashboard drawer.
* **Serverless Visual Interface:** Standalone client-side application using Tailwind CSS and Chart.js, deployable zero-cost to GitHub Pages.

---

## 🚀 Quick-Start Guide

### 1. Initialize Repository Locally

```bash
# Clone or initialize directory
mkdir -p sikkim-audit-dashboard
cd sikkim-audit-dashboard
git init
git branch -M main

# Configure identity
git config user.name "sikkimlfa"
git config user.email "sikkimlfa@gmail.com"

# Set remote origin
git remote add origin [https://github.com/Sikkimlfa/sikkim-audit-dashboard.git](https://github.com/Sikkimlfa/sikkim-audit-dashboard.git)

```

### 2. Scaffold Folder Structure

#### Linux Mint (Bash Terminal)

```bash
mkdir -p .github/workflows data/raw data/processed reports scripts
touch data/raw/.gitkeep reports/.gitkeep requirements.txt index.html

```

#### Windows 11 (PowerShell in VSCodium)

```powershell
New-Item -ItemType Directory -Force -Path .github\workflows, data\raw, data\processed, reports, scripts
New-Item -ItemType File -Force -Path data\raw\.gitkeep, reports\.gitkeep, requirements.txt, index.html

```

### 3. Run Pipeline and Deploy

```bash
# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows PowerShell: .\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Generate whitelist & extract data
python3 scripts/generate_master_units.py
python3 scripts/extract_annexures.py
python3 scripts/analyze_data.py

# Commit and Push
git add .
git commit -m "feat: complete automated extraction and audit dashboard for 212 units"
git push -u origin main --force-with-lease

```

---

## 📖 Extended Documentation

* [Installation Guide (Linux Mint & Windows 11)](INSTALL.md)
* [Troubleshooting & Diagnostics](https://www.google.com/search?q=TROUBLESHOOTING.md)
* [Contribution Guidelines](https://www.google.com/search?q=CONTRIBUTING.md)

