"""
Command-line entry point for SQL History Expert
"""

import sys
from .analyze_sql_history import main

if __name__ == "__main__":
    sys.exit(main())
