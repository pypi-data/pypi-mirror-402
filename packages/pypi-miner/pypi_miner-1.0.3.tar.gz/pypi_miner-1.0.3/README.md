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

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "PyPI")
- Name (package name)
- Homepage URL
- Repository URL
