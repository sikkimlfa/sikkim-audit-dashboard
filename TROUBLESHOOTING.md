# Troubleshooting & Diagnostics

### 1. Environment & Package Errors

#### `error: externally-managed-environment` (PEP 668)
- **Symptom:** `pip install` fails with a message indicating the environment is externally managed.
- **Cause:** Linux Mint / Debian 12 prevents global `pip` installations.
- **Fix:** Activate the project's virtual environment:

  ```bash
  source venv/bin/activate
  pip install -r requirements.txt
  ```

#### `pipx: No apps associated with package pandas`

* **Symptom:** `pipx install pandas` installs nothing or warns that no binaries exist.
* **Cause:** `pipx` is designed for CLI executables, not Python development libraries.
* **Fix:** Uninstall packages from `pipx` (`pipx uninstall pandas; pipx uninstall pdfplumber`) and install them inside your virtual environment using standard `pip`.

---

### 2. Git & Mount Permissions

#### `fatal: detected dubious ownership in repository at '/mnt/...'`

* **Symptom:** Git blocks operations on mounted NTFS/ext4 drives.
* **Cause:** File ownership UID on the mounted drive differs from the active Linux user.
* **Fix:** Add the repository path to Git safe directories:
```bash
git config --global --add safe.directory /Home/sikkim-audit-dashboard

```



---

### 3. Extraction & Audit Math Issues

#### Financial Year Defaulting Incorrectly

* **Symptom:** Output JSON shows years outside the valid range (e.g., `2080-81` or `2008-09`).
* **Cause:** The regex pattern evaluated numeric tokens (voucher numbers or codes) using unanchored 4-digit matching.
* **Fix:** The updated pattern in `scripts/extract_annexures.py` bounds the year check:
```python
re.search(r'\b(20(?:1[5-9]|2[0-5]))[-–/](\d{2,4})\b', text)

```



#### Units Missing from Output

* **Symptom:** A unit appears in the PDF but does not show up in `financial_statements.json`.
* **Cause:** The unit either failed the whitelist check or was routed to `audit_discrepancies.json` due to an arithmetic mismatch.
* **Fix:**
1. Inspect `data/processed/audit_discrepancies.json` to verify if reported $\text{Total Receipts} \ne \text{OB} + \text{Receipts}$.


2. If the name is misspelled in the PDF, register the alias in `SPELLING_ALIASES` inside `scripts/extract_annexures.py`.
