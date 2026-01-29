#!/usr/bin/env python3
"""
Table Stats Expert - Table and Column Statistics Analysis Tool

Analyzes table and column metadata in ClickZetta Lakehouse, providing storage distribution,
growth trends, partition usage, ownership, and column-level statistics.

Usage:
    python impl.py <action> [options]

Examples:
    python impl.py analyze_schemas
    python impl.py analyze_size --limit 50 --min_size_mb 100
    python impl.py analyze_types
    python impl.py analyze_growth --days 30
    python impl.py analyze_partitions
    python impl.py analyze_creators
    python impl.py analyze_columns --schema public
    python impl.py analyze_data_types --schema public
    python impl.py analyze_table_structure --schema public --table_name my_table
"""

import argparse
import json
import sys
from typing import Dict, Any, Optional


def analyze_schemas() -> Dict[str, Any]:
    """
    Analyze table distribution by schema.
    Returns SQL queries for schema-level statistics.
    
    Returns:
        Dictionary containing schema_stats_sql
    """
    schema_stats_sql = """
-- Schema-level table statistics
SELECT
    table_schema,
    COUNT(*) as table_count,
    SUM(CASE WHEN table_type = 'TABLE' THEN 1 ELSE 0 END) as physical_tables,
    SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) as views,
    SUM(row_count) as total_rows,
    ROUND(SUM(bytes) / 1024 / 1024 / 1024, 2) as total_size_gb,
    ROUND(AVG(bytes) / 1024 / 1024, 2) as avg_table_size_mb,
    SUM(CASE WHEN is_partitioned = 'true' THEN 1 ELSE 0 END) as partitioned_tables,
    MIN(create_time) as oldest_table_create_time,
    MAX(last_modify_time) as latest_modify_time
FROM information_schema.tables
GROUP BY table_schema
ORDER BY total_size_gb DESC;
"""

    return {
        "status": "success",
        "analysis_type": "schemas",
        "schema_stats_sql": schema_stats_sql,
        "description": "Table distribution and storage statistics by schema"
    }


def analyze_size(limit: int = 50, min_size_mb: int = 0) -> Dict[str, Any]:
    """
    Analyze table size distribution and identify large tables.
    
    Args:
        limit: Top N largest tables, default 50
        min_size_mb: Minimum size threshold in MB, default 0
    
    Returns:
        Dictionary containing large_tables_sql and size_distribution_sql
    """
    large_tables_sql = f"""
-- Large table statistics (by storage size)
SELECT
    table_schema,
    table_name,
    table_type,
    table_creator,
    row_count,
    ROUND(bytes / 1024 / 1024 / 1024, 2) as size_gb,
    ROUND(bytes / 1024 / 1024, 2) as size_mb,
    is_partitioned,
    is_clustered,
    create_time,
    last_modify_time,
    comment
FROM information_schema.tables
WHERE bytes >= {min_size_mb} * 1024 * 1024
    AND table_type = 'TABLE'
ORDER BY bytes DESC
LIMIT {limit};
"""

    size_distribution_sql = """
-- Table size distribution statistics
SELECT
    CASE
        WHEN bytes < 1024 * 1024 THEN '< 1 MB'
        WHEN bytes < 10 * 1024 * 1024 THEN '1-10 MB'
        WHEN bytes < 100 * 1024 * 1024 THEN '10-100 MB'
        WHEN bytes < 1024 * 1024 * 1024 THEN '100 MB - 1 GB'
        WHEN bytes < 10 * 1024 * 1024 * 1024 THEN '1-10 GB'
        WHEN bytes < 100 * 1024 * 1024 * 1024 THEN '10-100 GB'
        ELSE '> 100 GB'
    END as size_range,
    COUNT(*) as table_count,
    ROUND(SUM(bytes) / 1024 / 1024 / 1024, 2) as total_size_gb
FROM information_schema.tables
WHERE table_type = 'TABLE'
GROUP BY
    CASE
        WHEN bytes < 1024 * 1024 THEN '< 1 MB'
        WHEN bytes < 10 * 1024 * 1024 THEN '1-10 MB'
        WHEN bytes < 100 * 1024 * 1024 THEN '10-100 MB'
        WHEN bytes < 1024 * 1024 * 1024 THEN '100 MB - 1 GB'
        WHEN bytes < 10 * 1024 * 1024 * 1024 THEN '1-10 GB'
        WHEN bytes < 100 * 1024 * 1024 * 1024 THEN '10-100 GB'
        ELSE '> 100 GB'
    END
ORDER BY MIN(bytes);
"""

    return {
        "status": "success",
        "analysis_type": "size",
        "large_tables_sql": large_tables_sql,
        "size_distribution_sql": size_distribution_sql,
        "description": f"Top {limit} largest tables and size distribution analysis"
    }


def analyze_types() -> Dict[str, Any]:
    """
    Analyze table type distribution.
    
    Returns:
        Dictionary containing type_stats_sql
    """
    type_stats_sql = """
-- Table type statistics
SELECT
    table_type,
    COUNT(*) as table_count,
    SUM(row_count) as total_rows,
    ROUND(SUM(bytes) / 1024 / 1024 / 1024, 2) as total_size_gb,
    ROUND(AVG(bytes) / 1024 / 1024, 2) as avg_size_mb,
    SUM(CASE WHEN is_partitioned = 'true' THEN 1 ELSE 0 END) as partitioned_count,
    SUM(CASE WHEN is_clustered = 'true' THEN 1 ELSE 0 END) as clustered_count
FROM information_schema.tables
GROUP BY table_type
ORDER BY table_count DESC;
"""

    return {
        "status": "success",
        "analysis_type": "types",
        "type_stats_sql": type_stats_sql,
        "description": "Table type distribution statistics"
    }


def analyze_growth(days: int = 30) -> Dict[str, Any]:
    """
    Analyze table growth trends and activity.
    
    Args:
        days: Time window for analysis in days, default 30
    
    Returns:
        Dictionary containing recent_tables_sql, active_tables_sql, stale_tables_sql, creation_trend_sql
    """
    recent_tables_sql = f"""
-- Recently created tables (last {days} days)
SELECT
    table_schema,
    table_name,
    table_type,
    table_creator,
    row_count,
    ROUND(bytes / 1024 / 1024, 2) as size_mb,
    create_time,
    last_modify_time,
    DATEDIFF(CURRENT_DATE(), DATE(last_modify_time)) as days_since_modified,
    comment
FROM information_schema.tables
WHERE create_time >= CURRENT_DATE() - INTERVAL {days} DAY
ORDER BY create_time DESC;
"""

    active_tables_sql = f"""
-- Active tables (modified in last {days} days)
SELECT
    table_schema,
    table_name,
    table_type,
    row_count,
    ROUND(bytes / 1024 / 1024 / 1024, 2) as size_gb,
    create_time,
    last_modify_time,
    DATEDIFF(CURRENT_DATE(), DATE(last_modify_time)) as days_since_modified
FROM information_schema.tables
WHERE last_modify_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND table_type = 'TABLE'
ORDER BY last_modify_time DESC;
"""

    stale_days = days * 3
    stale_tables_sql = f"""
-- Stale tables (not modified for more than {stale_days} days)
SELECT
    table_schema,
    table_name,
    table_creator,
    row_count,
    ROUND(bytes / 1024 / 1024 / 1024, 2) as size_gb,
    create_time,
    last_modify_time,
    DATEDIFF(CURRENT_DATE(), DATE(last_modify_time)) as days_since_modified,
    comment
FROM information_schema.tables
WHERE table_type = 'TABLE'
    AND last_modify_time < CURRENT_DATE() - INTERVAL {stale_days} DAY
ORDER BY last_modify_time ASC;
"""

    creation_trend_sql = """
-- Table creation trend (by month)
SELECT
    DATE_FORMAT(create_time, '%Y-%m') as create_month,
    COUNT(*) as tables_created,
    SUM(CASE WHEN table_type = 'TABLE' THEN 1 ELSE 0 END) as physical_tables,
    SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) as views_created
FROM information_schema.tables
GROUP BY DATE_FORMAT(create_time, '%Y-%m')
ORDER BY create_month DESC
LIMIT 12;
"""

    return {
        "status": "success",
        "analysis_type": "growth",
        "recent_tables_sql": recent_tables_sql,
        "active_tables_sql": active_tables_sql,
        "stale_tables_sql": stale_tables_sql,
        "creation_trend_sql": creation_trend_sql,
        "description": f"Table growth trends and activity analysis for the past {days} days"
    }


def analyze_partitions() -> Dict[str, Any]:
    """
    Analyze partition table usage.
    
    Returns:
        Dictionary containing partition_stats_sql and partition_details_sql
    """
    partition_stats_sql = """
-- Partition table statistics
SELECT
    table_schema,
    COUNT(*) as total_tables,
    SUM(CASE WHEN is_partitioned = 'true' THEN 1 ELSE 0 END) as partitioned_tables,
    ROUND(SUM(CASE WHEN is_partitioned = 'true' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as partition_ratio,
    SUM(CASE WHEN is_clustered = 'true' THEN 1 ELSE 0 END) as clustered_tables,
    SUM(CASE WHEN is_partitioned = 'true' THEN bytes ELSE 0 END) / 1024 / 1024 / 1024 as partitioned_size_gb,
    SUM(bytes) / 1024 / 1024 / 1024 as total_size_gb
FROM information_schema.tables
WHERE table_type = 'TABLE'
GROUP BY table_schema
ORDER BY partitioned_tables DESC;
"""

    partition_details_sql = """
-- Partition table details
SELECT
    table_schema,
    table_name,
    table_creator,
    row_count,
    ROUND(bytes / 1024 / 1024 / 1024, 2) as size_gb,
    is_partitioned,
    is_clustered,
    create_time,
    last_modify_time,
    comment
FROM information_schema.tables
WHERE table_type = 'TABLE'
    AND is_partitioned = 'true'
ORDER BY bytes DESC;
"""

    return {
        "status": "success",
        "analysis_type": "partitions",
        "partition_stats_sql": partition_stats_sql,
        "partition_details_sql": partition_details_sql,
        "description": "Partition table usage and distribution analysis"
    }


def analyze_creators() -> Dict[str, Any]:
    """
    Analyze table ownership by creators.
    
    Returns:
        Dictionary containing creator_stats_sql
    """
    creator_stats_sql = """
-- Table count by creator
SELECT
    table_creator,
    COUNT(*) as table_count,
    SUM(CASE WHEN table_type = 'TABLE' THEN 1 ELSE 0 END) as physical_tables,
    SUM(CASE WHEN table_type = 'VIEW' THEN 1 ELSE 0 END) as views,
    SUM(row_count) as total_rows,
    ROUND(SUM(bytes) / 1024 / 1024 / 1024, 2) as total_size_gb,
    MIN(create_time) as first_table_created,
    MAX(create_time) as latest_table_created
FROM information_schema.tables
GROUP BY table_creator
ORDER BY table_count DESC;
"""

    return {
        "status": "success",
        "analysis_type": "creators",
        "creator_stats_sql": creator_stats_sql,
        "description": "Table ownership statistics by creators"
    }


def analyze_columns(schema: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze column-level statistics across all tables.
    
    Args:
        schema: Optional schema filter
    
    Returns:
        Dictionary containing column_stats_sql, nullable_analysis_sql, key_columns_sql
    """
    where_clause = ""
    if schema:
        where_clause = f"WHERE table_schema = '{schema}'"

    column_stats_sql = f"""
-- Column-level statistics
SELECT
    table_schema,
    COUNT(DISTINCT table_name) as table_count,
    COUNT(*) as total_columns,
    ROUND(AVG(column_count), 2) as avg_columns_per_table,
    SUM(CASE WHEN is_nullable = true THEN 1 ELSE 0 END) as nullable_columns,
    SUM(CASE WHEN is_primary_key = true THEN 1 ELSE 0 END) as primary_key_columns,
    SUM(CASE WHEN is_clustering_column = true THEN 1 ELSE 0 END) as clustering_columns
FROM (
    SELECT
        table_schema,
        table_name,
        column_name,
        is_nullable,
        is_primary_key,
        is_clustering_column,
        COUNT(*) OVER (PARTITION BY table_schema, table_name) as column_count
    FROM information_schema.columns
    {where_clause}
) t
GROUP BY table_schema
ORDER BY total_columns DESC;
"""

    nullable_analysis_sql = f"""
-- Nullable column analysis
SELECT
    table_schema,
    table_name,
    COUNT(*) as total_columns,
    SUM(CASE WHEN is_nullable = true THEN 1 ELSE 0 END) as nullable_count,
    ROUND(SUM(CASE WHEN is_nullable = true THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as nullable_percentage
FROM information_schema.columns
{where_clause}
GROUP BY table_schema, table_name
HAVING nullable_count > 0
ORDER BY nullable_percentage DESC;
"""

    # Handle WHERE clause for key_columns_sql
    key_where = "WHERE (is_primary_key = true OR is_clustering_column = true)"
    if schema:
        key_where = f"WHERE (is_primary_key = true OR is_clustering_column = true) AND table_schema = '{schema}'"

    key_columns_sql = f"""
-- Primary key and clustering column statistics
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    is_primary_key,
    is_clustering_column,
    comment
FROM information_schema.columns
{key_where}
ORDER BY table_schema, table_name, is_primary_key DESC, is_clustering_column DESC;
"""

    return {
        "status": "success",
        "analysis_type": "columns",
        "column_stats_sql": column_stats_sql,
        "nullable_analysis_sql": nullable_analysis_sql,
        "key_columns_sql": key_columns_sql,
        "description": "Column-level statistics including nullable and key columns analysis"
    }


def analyze_data_types(schema: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze data type distribution across all columns.
    
    Args:
        schema: Optional schema filter
    
    Returns:
        Dictionary containing type_distribution_sql, type_by_schema_sql, complex_types_sql
    """
    where_clause = ""
    if schema:
        where_clause = f"WHERE table_schema = '{schema}'"

    type_distribution_sql = f"""
-- Data type distribution statistics
SELECT
    data_type,
    COUNT(*) as column_count,
    COUNT(DISTINCT CONCAT(table_schema, '.', table_name)) as table_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM information_schema.columns
{where_clause}
GROUP BY data_type
ORDER BY column_count DESC;
"""

    type_by_schema_sql = f"""
-- Data type distribution by schema
SELECT
    table_schema,
    data_type,
    COUNT(*) as column_count,
    COUNT(DISTINCT table_name) as table_count
FROM information_schema.columns
{where_clause}
GROUP BY table_schema, data_type
ORDER BY table_schema, column_count DESC;
"""

    # Handle WHERE clause for complex_types_sql
    complex_where = "WHERE ("
    if schema:
        complex_where = f"WHERE table_schema = '{schema}' AND ("

    complex_types_sql = f"""
-- Complex data type usage (ARRAY, MAP, STRUCT, JSON)
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    comment
FROM information_schema.columns
{complex_where}
        data_type LIKE '%ARRAY%'
        OR data_type LIKE '%MAP%'
        OR data_type LIKE '%STRUCT%'
        OR data_type LIKE '%JSON%'
    )
ORDER BY table_schema, table_name, column_name;
"""

    return {
        "status": "success",
        "analysis_type": "data_types",
        "type_distribution_sql": type_distribution_sql,
        "type_by_schema_sql": type_by_schema_sql,
        "complex_types_sql": complex_types_sql,
        "description": "Data type distribution and complexity analysis"
    }


def analyze_table_structure(schema: Optional[str] = None, table_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze table structure including column counts, key constraints, and defaults.
    
    Args:
        schema: Optional schema filter
        table_name: Optional table name filter
    
    Returns:
        Dictionary containing structure_summary_sql, default_values_sql, undocumented_columns_sql
    """
    where_clause = ""
    if schema:
        where_clause = f"WHERE table_schema = '{schema}'"
        if table_name:
            where_clause += f" AND table_name = '{table_name}'"
    elif table_name:
        where_clause = f"WHERE table_name = '{table_name}'"

    # Handle WHERE clause for default_values_sql
    default_where = "WHERE column_default IS NOT NULL"
    if schema:
        default_where = f"WHERE table_schema = '{schema}' AND column_default IS NOT NULL"
        if table_name:
            default_where += f" AND table_name = '{table_name}'"
    elif table_name:
        default_where = f"WHERE table_name = '{table_name}' AND column_default IS NOT NULL"

    structure_summary_sql = f"""
-- Table structure complexity analysis
SELECT
    table_schema,
    table_name,
    COUNT(*) as column_count,
    SUM(CASE WHEN is_primary_key = true THEN 1 ELSE 0 END) as pk_count,
    SUM(CASE WHEN is_clustering_column = true THEN 1 ELSE 0 END) as cluster_key_count,
    SUM(CASE WHEN column_default IS NOT NULL THEN 1 ELSE 0 END) as default_value_count,
    SUM(CASE WHEN is_nullable = false THEN 1 ELSE 0 END) as not_null_count,
    SUM(CASE WHEN comment IS NOT NULL AND comment != '' THEN 1 ELSE 0 END) as commented_columns
FROM information_schema.columns
{where_clause}
GROUP BY table_schema, table_name
ORDER BY column_count DESC;
"""

    default_values_sql = f"""
-- Columns with default values
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    column_default,
    is_nullable,
    comment
FROM information_schema.columns
{default_where}
ORDER BY table_schema, table_name, column_name;
"""

    undocumented_columns_sql = f"""
-- Undocumented columns (data governance perspective)
SELECT
    table_schema,
    table_name,
    COUNT(*) as total_columns,
    SUM(CASE WHEN comment IS NULL OR comment = '' THEN 1 ELSE 0 END) as undocumented_count,
    ROUND(SUM(CASE WHEN comment IS NULL OR comment = '' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as undocumented_percentage
FROM information_schema.columns
{where_clause}
GROUP BY table_schema, table_name
HAVING undocumented_count > 0
ORDER BY undocumented_percentage DESC, total_columns DESC;
"""

    return {
        "status": "success",
        "analysis_type": "table_structure",
        "structure_summary_sql": structure_summary_sql,
        "default_values_sql": default_values_sql,
        "undocumented_columns_sql": undocumented_columns_sql,
        "description": "Table structure complexity and documentation quality analysis"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Table Stats Expert - Table and Column Statistics Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Usage:
  %(prog)s analyze_schemas
  %(prog)s analyze_size --limit 50 --min_size_mb 100
  %(prog)s analyze_types
  %(prog)s analyze_growth --days 30
  %(prog)s analyze_partitions
  %(prog)s analyze_creators
  %(prog)s analyze_columns --schema public
  %(prog)s analyze_data_types --schema public
  %(prog)s analyze_table_structure --schema public --table_name my_table

The output SQL can be executed via MCP Server's LH-execute_read_query tool.
        """
    )

    subparsers = parser.add_subparsers(dest="action", help="Analysis action")

    # analyze_schemas subcommand
    subparsers.add_parser(
        "analyze_schemas",
        help="Analyze table distribution by schema"
    )

    # analyze_size subcommand
    size_parser = subparsers.add_parser(
        "analyze_size",
        help="Analyze table size distribution"
    )
    size_parser.add_argument(
        "--limit", type=int, default=50,
        help="Top N largest tables, default 50"
    )
    size_parser.add_argument(
        "--min_size_mb", type=int, default=0,
        help="Minimum size threshold in MB, default 0"
    )

    # analyze_types subcommand
    subparsers.add_parser(
        "analyze_types",
        help="Analyze table type distribution"
    )

    # analyze_growth subcommand
    growth_parser = subparsers.add_parser(
        "analyze_growth",
        help="Analyze table growth trends"
    )
    growth_parser.add_argument(
        "--days", type=int, default=30,
        help="Time window for analysis in days, default 30"
    )

    # analyze_partitions subcommand
    subparsers.add_parser(
        "analyze_partitions",
        help="Analyze partition table usage"
    )

    # analyze_creators subcommand
    subparsers.add_parser(
        "analyze_creators",
        help="Analyze table ownership by creators"
    )

    # analyze_columns subcommand
    columns_parser = subparsers.add_parser(
        "analyze_columns",
        help="Analyze column-level statistics"
    )
    columns_parser.add_argument(
        "--schema", type=str, default=None,
        help="Optional schema filter"
    )

    # analyze_data_types subcommand
    data_types_parser = subparsers.add_parser(
        "analyze_data_types",
        help="Analyze data type distribution"
    )
    data_types_parser.add_argument(
        "--schema", type=str, default=None,
        help="Optional schema filter"
    )

    # analyze_table_structure subcommand
    structure_parser = subparsers.add_parser(
        "analyze_table_structure",
        help="Analyze table structure complexity"
    )
    structure_parser.add_argument(
        "--schema", type=str, default=None,
        help="Optional schema filter"
    )
    structure_parser.add_argument(
        "--table_name", type=str, default=None,
        help="Optional table name filter"
    )

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    # Execute corresponding analysis function
    if args.action == "analyze_schemas":
        result = analyze_schemas()
    elif args.action == "analyze_size":
        result = analyze_size(limit=args.limit, min_size_mb=args.min_size_mb)
    elif args.action == "analyze_types":
        result = analyze_types()
    elif args.action == "analyze_growth":
        result = analyze_growth(days=args.days)
    elif args.action == "analyze_partitions":
        result = analyze_partitions()
    elif args.action == "analyze_creators":
        result = analyze_creators()
    elif args.action == "analyze_columns":
        result = analyze_columns(schema=args.schema)
    elif args.action == "analyze_data_types":
        result = analyze_data_types(schema=args.schema)
    elif args.action == "analyze_table_structure":
        result = analyze_table_structure(schema=args.schema, table_name=args.table_name)
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)

    # Output result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
