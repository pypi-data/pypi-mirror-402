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

**Format:** CSV file with columns:

- ID (sequential number)
- Platform (always "NPM")
- Name (package name)
- Homepage URL
- Repository URL
