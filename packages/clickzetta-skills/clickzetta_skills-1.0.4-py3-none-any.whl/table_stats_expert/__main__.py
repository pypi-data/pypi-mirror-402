"""
Command-line entry point for Table Stats Expert
"""

import sys
from .analyze_table_stats import main

if __name__ == "__main__":
    sys.exit(main())
