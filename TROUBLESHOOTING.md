# 🔍 Troubleshooting & Edge Cases

### 1. Missing `pandas` or `openpyxl` Module
Ensure you install required dependencies inside your virtual environment:
```bash
pip install -r requirements.txt
```
### 2. UTF-8 Byte Order Mark (BOM) in Excel
When generating CSV exports, ensure \uFEFF is prepended to the CSV blob so Microsoft Excel correctly displays currency symbols (₹).


---