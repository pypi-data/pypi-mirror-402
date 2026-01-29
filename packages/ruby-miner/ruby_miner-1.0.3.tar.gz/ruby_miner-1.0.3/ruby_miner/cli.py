"""Command-line interface for ruby-miner."""

import sys
from .miner import mine_ruby_gems


def main():
    """Main CLI entry point."""
    try:
        mine_ruby_gems()
        return 0
    except KeyboardInterrupt:
        print("\n\nMining interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
