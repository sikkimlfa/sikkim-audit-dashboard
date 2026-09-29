# 📊 Sikkim Local Fund Audit Dashboard

![Build Status](https://img.shields.io/badge/build-passing-brightgreen?style=for-the-badge&logo=github-actions)
![License](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)
![Tech Stack](https://img.shields.io/badge/Stack-Tailwind_CSS_%7C_Chart.js_%7C_jsPDF_%7C_Python-indigo?style=for-the-badge)

An enterprise-grade financial analytics dashboard and extraction pipeline built for the **Directorate of Local Fund Audit, Government of Sikkim**.

---

## 📂 Repository Directory Structure

```text
sikkim-audit-dashboard/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions deployment workflow for GitHub Pages
├── data/                       # Input raw spreadsheets (.xlsx, .csv)
│   └── sample_audit.xlsx
├── reports/                    # Output directory for exported reports (CSVs, PDFs)
│   └── .gitkeep
├── scripts/                    # Python extraction & unit test suite
│   ├── extract.py
│   └── test_extract.py
├── index.html                  # Single-Page Application (HTML, Tailwind, Chart.js, jsPDF)
├── requirements.txt            # Python dependencies (pandas, openpyxl, pytest)
├── LICENSE                     # MIT License
├── README.md                   # Primary documentation
├── INSTALL.md                  # Installation guide
├── TROUBLESHOOTING.md          # Common fixes and encoding diagnostics
└── CONTRIBUTING.md             # Developer guidelines
```

## 🚀 Quick Start
Install Python dependencies:
```Bash
pip install -r requirements.txt
```
Process raw audit spreadsheet:

```Bash
python3 scripts/extract.py -i data/sample_audit.xlsx -o data/records.json
```
Run local server:

```Bash
python3 -m http.server 8000
```
---