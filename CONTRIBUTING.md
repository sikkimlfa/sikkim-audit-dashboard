# Contributing Guidelines

Contributions are welcome to help maintain the data integrity, parsing precision, and visual capabilities of the Directorate of Local Fund Audit dashboard.

---

## Branching Strategy

We follow standard feature-branch workflows:
- `main`: Production-ready code and deployed GitHub Pages dashboard.
- `feature/<name>`: New analytical views, chart modules, or parsing enhancements.
- `fix/<name>`: Corrections to spelling alias maps, math verification routines, or regex rules.

---

## Coding Standards

### Python
- Maintain compliance with **PEP 8**.
- Handle currency strings defensively using `clean_currency()` to avoid exceptions on `nil`, `null`, or formatted negatives.
- Type hints are encouraged for public functions.

### JSON & Data Integrity
- Do not modify `data/raw/annual_audit_plan_2026.json` manually; regenerate it via `scripts/generate_master_units.py` to maintain audit trail consistency.
- Any change to mathematical validation thresholds ($\Delta > ₹2.00$) must be documented with an audit justification.

---

## Commit Message Format (Conventional Commits)

Format commit messages with structured prefixes:
- `feat:` Adds a new capability (e.g., `feat: add district export to CSV`)
- `fix:` Resolves a defect or parsing error (e.g., `fix: map legacy east zilla keyword`)
- `docs:` Documentation updates only (e.g., `docs: update INSTALL.md for Windows 11`)
- `refactor:` Code reorganization without functional changes (e.g., `refactor: optimize table column detection`)

---

## Pull Request Process

1. Fork or create a feature branch from `main`:
   ```bash
   git checkout -b feature/new-kpi-metric
   ```

2. Verify that extraction completes cleanly and math validations reconcile:
```bash
python3 scripts/extract_annexures.py
python3 scripts/analyze_data.py

```


3. Commit your changes and submit a Pull Request against `main` with:
* A summary of modifications made.
* Sample output verification numbers.
* Confirmation that no unauthorized units were added outside the 212-unit whitelist.

---

### Next Steps to Initialize and Push

Run the following commands in your Linux Mint terminal to initialize the repository, write the files, and publish to GitHub:

```bash
# 1. Navigate to project root
cd /Home/sikkim-audit-dashboard

# 2. Configure Git user credentials
git config user.name ""
git config user.email ""

# 3. Stage all blueprint files and scripts
git add README.md LICENSE INSTALL.md TROUBLESHOOTING.md CONTRIBUTING.md scripts/ index.html requirements.txt

# 4. Create initial commit
git commit -m "chore: initialize production repository blueprint and audit verification engine"

# 5. Set branch to main and push
git branch -M main
git push -u origin main --force-with-lease

```

Once pushed, enable GitHub Pages under **Repository Settings** > **Pages** > **Build and Deployment: GitHub Actions** to publish the live dashboard at:
[https://sikkimlfa.github.io/sikkim-audit-dashboard/](https://sikkimlfa.github.io/sikkim-audit-dashboard/)
