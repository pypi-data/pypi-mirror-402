"""Command-line interface for npm-miner."""

import sys
from .miner import mine_npm_packages


def main():
    """Main CLI entry point."""
    try:
        mine_npm_packages()
        return 0
    except KeyboardInterrupt:
        print("\n\nMining interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
