# NPM Package Miner

A Python tool to mine and extract complete package lists from the NPM registry.

## Installation

```bash
pip install npm-miner
```

## Usage

```bash
npm-miner
```

Or use as a Python module:

```python
from npm_miner import mine_npm
mine_npm()
```

## Data Source

- NPM Registry: https://registry.npmjs.org/
- All packages: https://replicate.npmjs.com/_all_docs

## Output

**Location:** `../Package-List/NPM.csv`

The output file will be stored in a folder named "Package-List" _in your current working directory_.

If you are using a virtual environment, "Package-List" will be located where `venv` is installed.

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "NPM")
- Name (package name)
- Homepage URL
- Repository URL
