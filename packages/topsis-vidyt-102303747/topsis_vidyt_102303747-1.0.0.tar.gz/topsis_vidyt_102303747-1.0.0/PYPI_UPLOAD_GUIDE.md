# TOPSIS Package Structure & Steps to Upload to PyPI

## Current Project Structure:

```
TOPSIS/
├── topsis_package/           # Main package directory
│   ├── __init__.py          # Package initialization
│   ├── core.py              # Core TOPSIS algorithm
│   └── __main__.py          # CLI entry point
├── setup.py                 # Setup script
├── pyproject.toml           # Modern Python project config
├── README.md                # User documentation
├── LICENSE                  # MIT License
├── data.xlsx                # Sample input
├── out-fund.csv            # Sample output
└── topsis.py               # (Old version - can keep for reference)
```

## Step-by-Step: Build & Upload to PyPI

### Step 1: Update Package Name
Edit these files and replace "yourname-rollnumber":
- `pyproject.toml` line 5: `name = "topsis-<YourName>-<RollNumber>"`
- `setup.py` line 17: `name="topsis-<YourName>-<RollNumber>"`
- `README.md` line 7-11: Update installation examples

Example: If your name is "John" and roll is "10155792":
```
name = "topsis-john-10155792"
```

### Step 2: Update Author Info
Edit `setup.py` and `pyproject.toml`:
```
author="Your Full Name"
author_email="your.email@example.com"
```

### Step 3: Build the Package
```bash
# Install build tools
pip install build twine

# Navigate to project directory
cd f:\College\UCS654\TOPSIS

# Build distribution packages
python -m build
```

This creates:
- `dist/topsis-yourname-rollnumber-1.0.0.tar.gz` (source distribution)
- `dist/topsis-yourname-rollnumber-1.0.0-py3-none-any.whl` (wheel)

### Step 4: Register on PyPI
1. Go to https://pypi.org/account/register/
2. Create account with username/password
3. Go to https://pypi.org/manage/account/#api-tokens
4. Create API token (copy and save securely)

### Step 5: Upload to PyPI
```bash
# Upload to PyPI (will ask for token)
twine upload dist/*

# When prompted for username, enter: __token__
# When prompted for password, paste your API token
```

### Step 6: Test Installation from PyPI
```bash
# In a new environment/folder
pip install topsis-yourname-rollnumber

# Test it works
python -m topsis_package data.xlsx "0.2,0.2,0.2,0.2,0.2" "+,+,+,+,+" output.csv
```

## Troubleshooting

**Issue: Package name already exists**
- Solution: Use unique package name format (add your actual roll number)

**Issue: Upload fails with 403**
- Solution: Check API token validity at https://pypi.org/manage/account/#api-tokens

**Issue: Import errors after installation**
- Solution: Ensure all dependencies installed: `pip install numpy pandas openpyxl`

## Resources:
- PyPI: https://pypi.org
- Building packages: https://packaging.python.org/tutorials/packaging-projects/
- Twine docs: https://twine.readthedocs.io/
- setuptools: https://setuptools.readthedocs.io/
