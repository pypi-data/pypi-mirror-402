# PyPI Package Miner

A Python tool to mine and extract complete package lists from the PyPI (Python Package Index) registry.

## Features

- Fetches all ~500,000 PyPI packages from the official simple API
- Retrieves package metadata including homepage and repository URLs
- Parallel processing with 50 workers for efficient data collection
- Intelligently extracts repository URLs from multiple metadata fields
- Progress tracking with visual feedback
- Outputs standardized CSV format for cross-ecosystem analysis

## Installation

```bash
pip install pypi-miner
```

## Quick Start

```bash
pypi-miner
```

Or use as a Python module:

```python
from pypi_miner import mine_pypi
mine_pypi()
```

## Output

Generates a CSV file with package information:
- Package ID, Platform, Name
- Homepage URL, Repository URL

## Performance

- Runtime: 3-8 hours for complete dataset
- Uses 50 parallel workers
- Processes ~500,000 packages

## Data Source

- PyPI Simple Index: https://pypi.org/simple/
- Package Metadata: https://pypi.org/pypi/{package-name}/json

## License

MIT License - see LICENSE file for details
