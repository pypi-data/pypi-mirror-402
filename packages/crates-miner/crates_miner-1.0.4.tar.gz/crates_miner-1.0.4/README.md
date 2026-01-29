# Crates.io Package Miner

A Python tool to mine and extract complete package lists from the crates.io (Rust) registry.

## Installation

```bash
pip install crates-miner
```

## Usage

```bash
crates-miner
```

Or use as a Python module:

```python
from crates_miner import mine_crates
mine_crates()
```

## Data Source

- Crates.io Database Dump: https://static.crates.io/db-dump.tar.gz

## Output

**Location:** `../Package-List/Crates.csv`

The output file will be stored in a folder named "Package-List" _in your current working directory_.

If you are using a virtual environment, "Package-List" will be located where `venv` is installed.

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "Crates.io")
- Name (crate name)
- Homepage URL
- Repository URL
