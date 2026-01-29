"""
SQL History Expert - SQL Execution History Analysis Tool

Analyzes SQL execution history in ClickZetta Lakehouse, providing workload distribution,
table access statistics, cache hit rate analysis, and performance issue diagnosis.
"""

__version__ = "1.0.0"
__author__ = "Clickzetta Team"

from .analyze_sql_history import (
    analyze_load,
    analyze_tables,
    analyze_cache,
    diagnose,
)

__all__ = [
    "analyze_load",
    "analyze_tables",
    "analyze_cache",
    "diagnose",
]
