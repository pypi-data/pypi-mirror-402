"""
Entry point for `python -m rhizo` command.

This enables running the CLI via:
    python -m rhizo info ./mydata
    python -m rhizo tables ./mydata
    python -m rhizo versions ./mydata users
    python -m rhizo verify ./mydata
"""

import sys
from rhizo.cli import main

if __name__ == "__main__":
    sys.exit(main())
