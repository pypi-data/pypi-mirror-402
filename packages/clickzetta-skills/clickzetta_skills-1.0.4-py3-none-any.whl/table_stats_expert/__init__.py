"""
Table Stats Expert - Table and Column Statistics Analysis Tool

Analyzes table and column metadata in ClickZetta Lakehouse, providing storage distribution,
growth trends, partition usage, ownership, and column-level statistics.
"""

__version__ = "1.0.0"
__author__ = "Clickzetta Team"

from .analyze_table_stats import (
    analyze_schemas,
    analyze_size,
    analyze_types,
    analyze_growth,
    analyze_partitions,
    analyze_creators,
    analyze_columns,
    analyze_data_types,
    analyze_table_structure,
)

__all__ = [
    "analyze_schemas",
    "analyze_size",
    "analyze_types",
    "analyze_growth",
    "analyze_partitions",
    "analyze_creators",
    "analyze_columns",
    "analyze_data_types",
    "analyze_table_structure",
]
