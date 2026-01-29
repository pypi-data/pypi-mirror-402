# PyPI Package Miner

A Python tool to mine and extract complete package lists from the PyPI (Python Package Index) registry.

## Installation

```bash
pip install pypi-miner
```

## Usage

```bash
pypi-miner
```

Or use as a Python module:

```python
from pypi_miner import mine_pypi
mine_pypi()
```

## Data Source

- PyPI Simple Index: https://pypi.org/simple/
- Package Metadata: https://pypi.org/pypi/{package-name}/json

## Output

**Location:** `../Package-List/PyPI.csv`

The output file will be stored in a folder named "Package-List" _in your current working directory_.

If you are using a virtual environment, "Package-List" will be located where `venv` is installed.

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "PyPI")
- Name (package name)
- Homepage URL
- Repository URL
