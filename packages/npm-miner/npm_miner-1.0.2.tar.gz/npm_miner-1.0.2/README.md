# NPM Package Miner

A Python tool to mine and extract complete package lists from the NPM registry.

## Features

- Fetches all ~2-3 million NPM packages from the official registry
- Retrieves package metadata including homepage and repository URLs
- Parallel processing with 50 workers for efficient data collection
- Progress tracking with visual feedback
- Outputs standardized CSV format for cross-ecosystem analysis

## Installation

```bash
pip install npm-miner
```

## Quick Start

```bash
npm-miner
```

Or use as a Python module:

```python
from npm_miner import mine_npm
mine_npm()
```

## Output

Generates a CSV file with package information:
- Package ID, Platform, Name
- Homepage URL, Repository URL

## Performance

- Runtime: 10-20 hours for complete dataset
- Uses 50 parallel workers
- Network-dependent processing speed

## Data Source

- NPM Registry: https://registry.npmjs.org/
- All packages: https://replicate.npmjs.com/_all_docs

## License

MIT License - see LICENSE file for details
