# Installation and Environment Setup

This guide provides setup instructions for **Linux Mint** and **Windows 11** environments using VSCodium.

---

## System Prerequisites

| Requirement | Supported Version | Notes |
| :--- | :--- | :--- |
| **Python** | `3.10` – `3.12` | Required for `pdfplumber` and `pandas` |
| **Git** | `>= 2.34` | Version control & remote sync |
| **VSCodium / VS Code** | Latest | Recommended development IDE |
| **Modern Browser** | Chrome / Firefox / Edge | For viewing `index.html` |

---

## Installation on Linux Mint

### 1. System Packages & Python Environment
Open your bash terminal:

```bash
# Update package repositories
sudo apt update && sudo apt install -y python3-venv python3-pip git

# Navigate to project location
cd /mnt/351095A642490756/lfa/Home/sikkim-audit-dashboard

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

```

### 2. Install Project Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt

```

---

## Installation on Windows 11 (PowerShell in VSCodium)

### 1. Initialize Virtual Environment

Open PowerShell inside VSCodium (`Ctrl + ~`):

```powershell
# Set execution policy if script activation is restricted
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Create virtual environment
python -m venv venv

# Activate environment
.\venv\Scripts\Activate.ps1

```

### 2. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt

```

---

## Configuration & Data Setup

1. **Populate Whitelist:** Run the generator script to compile the master reference dictionary:
```bash
python3 scripts/generate_master_units.py

```


2. **Add Raw Reports:** Copy annual audit report PDFs into `data/raw/`:
```bash
cp /path/to/annual_reports/*.pdf data/raw/

```


3. **Run Extraction Pipeline:**
```bash
python3 scripts/extract_annexures.py

```


4. **Preview Dashboard:**
```bash
python3 -m http.server 8000

```


Open `http://localhost:8000` in your web browser.

