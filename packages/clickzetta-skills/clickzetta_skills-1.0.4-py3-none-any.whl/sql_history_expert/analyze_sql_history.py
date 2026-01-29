#!/usr/bin/env python3
"""
SQL History Expert - SQL Execution History Analysis Tool

Analyzes SQL execution history in ClickZetta Lakehouse, providing workload distribution,
table access statistics, cache hit rate analysis, and performance issue diagnosis.

Usage:
    python impl.py <action> [options]

Examples:
    python impl.py analyze_load --days 30
    python impl.py analyze_tables --days 7 --limit 50
    python impl.py analyze_cache --days 30
    python impl.py diagnose --days 7 --min_execution_time 300 --limit 50
"""

import argparse
import json
import sys
from typing import Dict, Any


def analyze_load(days: int = 30) -> Dict[str, Any]:
    """
    Analyze Workspace and Virtual Cluster load status.
    Returns SQL queries for analysis.
    
    Args:
        days: Analysis period in days, default 30
    
    Returns:
        Dictionary containing workspace_sql and vcluster_sql
    """
    workspace_sql = f"""
-- Workspace load statistics (last {days} days)
SELECT 
    workspace_name,
    COUNT(*) as job_count,
    SUM(execution_time) as total_execution_time,
    AVG(execution_time) as avg_execution_time,
    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as success_jobs,
    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed_jobs,
    ROUND(SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as success_rate
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
GROUP BY workspace_name
ORDER BY total_execution_time DESC;
"""
    
    vcluster_sql = f"""
-- Virtual Cluster load statistics (last {days} days)
SELECT 
    virtual_cluster,
    COUNT(*) as job_count,
    SUM(execution_time) as total_execution_time,
    AVG(execution_time) as avg_execution_time,
    MIN(execution_time) as min_execution_time,
    MAX(execution_time) as max_execution_time
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND virtual_cluster IS NOT NULL
GROUP BY virtual_cluster
ORDER BY total_execution_time DESC;
"""
    
    return {
        "status": "success",
        "analysis_type": "load",
        "workspace_sql": workspace_sql,
        "vcluster_sql": vcluster_sql,
        "description": f"Workspace and Virtual Cluster load analysis for the past {days} days"
    }


def analyze_tables(days: int = 30, limit: int = 20) -> Dict[str, Any]:
    """
    Analyze table access statistics.
    Returns SQL for most accessed tables and data read patterns.
    
    Args:
        days: Analysis period in days, default 30
        limit: Return top N tables, default 20
    
    Returns:
        Dictionary containing table_access_sql
    """
    table_access_sql = f"""
-- Most frequently accessed tables (last {days} days)
SELECT 
    GET_JSON_OBJECT(input_tables, '$.table[0].tableName') as table_name,
    CONCAT(
        GET_JSON_OBJECT(input_tables, '$.table[0].namespace[0]'),
        '.',
        GET_JSON_OBJECT(input_tables, '$.table[0].namespace[1]')
    ) as schema_name,
    COUNT(*) as access_count,
    SUM(CAST(input_bytes AS BIGINT)) as total_bytes_read,
    AVG(CAST(input_bytes AS BIGINT)) as avg_bytes_per_access,
    SUM(CAST(GET_JSON_OBJECT(input_tables, '$.table[0].record') AS BIGINT)) as total_records_read
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND input_tables IS NOT NULL
    AND input_tables != ''
    AND input_tables != '{{"table":[]}}'
    AND input_bytes > 0
GROUP BY 
    GET_JSON_OBJECT(input_tables, '$.table[0].tableName'),
    CONCAT(
        GET_JSON_OBJECT(input_tables, '$.table[0].namespace[0]'),
        '.',
        GET_JSON_OBJECT(input_tables, '$.table[0].namespace[1]')
    )
HAVING table_name IS NOT NULL
ORDER BY access_count DESC
LIMIT {limit};
"""
    
    return {
        "status": "success",
        "analysis_type": "tables",
        "table_access_sql": table_access_sql,
        "description": f"Top {limit} most accessed tables in the past {days} days"
    }


def analyze_cache(days: int = 30) -> Dict[str, Any]:
    """
    Analyze cache hit rate.
    Returns SQL for overall and per-workspace cache performance.
    
    Args:
        days: Analysis period in days, default 30
    
    Returns:
        Dictionary containing overall_cache_sql and workspace_cache_sql
    """
    overall_cache_sql = f"""
-- Overall cache hit rate (last {days} days)
SELECT 
    SUM(CAST(cache_hit_bytes AS BIGINT)) as total_cache_hit_bytes,
    SUM(CAST(input_bytes AS BIGINT)) as total_input_bytes,
    ROUND(SUM(CAST(cache_hit_bytes AS BIGINT)) * 100.0 / 
          NULLIF(SUM(CAST(input_bytes AS BIGINT)), 0), 2) as cache_hit_rate
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND input_bytes > 0;
"""
    
    workspace_cache_sql = f"""
-- Cache hit rate by workspace (last {days} days)
SELECT 
    workspace_name,
    SUM(CAST(cache_hit_bytes AS BIGINT)) as cache_hit_bytes,
    SUM(CAST(input_bytes AS BIGINT)) as input_bytes,
    ROUND(SUM(CAST(cache_hit_bytes AS BIGINT)) * 100.0 / 
          NULLIF(SUM(CAST(input_bytes AS BIGINT)), 0), 2) as cache_hit_rate
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND input_bytes > 0
GROUP BY workspace_name
ORDER BY cache_hit_rate DESC;
"""
    
    return {
        "status": "success",
        "analysis_type": "cache",
        "overall_cache_sql": overall_cache_sql,
        "workspace_cache_sql": workspace_cache_sql,
        "description": f"Cache hit rate analysis for the past {days} days"
    }


def diagnose(days: int = 7, min_execution_time: int = 300, limit: int = 50) -> Dict[str, Any]:
    """
    Performance diagnosis: long-running jobs, failed jobs, resource-intensive jobs.
    
    Args:
        days: Analysis period in days, default 7
        min_execution_time: Minimum execution time threshold in seconds, default 300 (5 minutes)
        limit: Maximum results per query, default 50
    
    Returns:
        Dictionary containing long_running_sql, failed_jobs_sql, and resource_intensive_sql
    """
    long_running_sql = f"""
-- Long-running jobs (last {days} days)
SELECT 
    job_id,
    workspace_name,
    virtual_cluster,
    job_type,
    execution_time,
    start_time,
    end_time,
    status,
    LEFT(job_text, 100) as job_text_preview
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND execution_time > {min_execution_time}
ORDER BY execution_time DESC
LIMIT {limit};
"""
    
    failed_jobs_sql = f"""
-- Failed jobs statistics and analysis (last {days} days)
SELECT 
    workspace_name,
    virtual_cluster,
    job_type,
    COUNT(*) as failed_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as failure_percentage,
    LEFT(error_message, 100) as common_error
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND status = 'FAILED'
GROUP BY workspace_name, virtual_cluster, job_type, LEFT(error_message, 100)
ORDER BY failed_count DESC
LIMIT 20;
"""
    
    resource_intensive_sql = f"""
-- High resource consumption jobs analysis (last {days} days)
SELECT 
    job_type,
    workspace_name,
    COUNT(*) as job_count,
    SUM(execution_time) as total_execution_time,
    AVG(execution_time) as avg_execution_time,
    SUM(CAST(input_bytes AS BIGINT)) / 1024 / 1024 / 1024 as total_input_gb,
    AVG(CAST(input_bytes AS BIGINT)) / 1024 / 1024 as avg_input_mb
FROM sys.information_schema.job_history
WHERE start_time >= CURRENT_DATE() - INTERVAL {days} DAY
    AND input_bytes > 0
GROUP BY job_type, workspace_name
ORDER BY total_execution_time DESC
LIMIT 20;
"""
    
    return {
        "status": "success",
        "analysis_type": "diagnosis",
        "long_running_sql": long_running_sql,
        "failed_jobs_sql": failed_jobs_sql,
        "resource_intensive_sql": resource_intensive_sql,
        "description": f"Performance diagnosis for the past {days} days"
    }


def main():
    parser = argparse.ArgumentParser(
        description="SQL History Expert - SQL Execution History Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example Usage:
  %(prog)s analyze_load --days 30
  %(prog)s analyze_tables --days 7 --limit 50
  %(prog)s analyze_cache --days 30
  %(prog)s diagnose --days 7 --min_execution_time 300 --limit 50

The output SQL can be executed via MCP Server's LH-execute_read_query tool.
        """
    )
    
    subparsers = parser.add_subparsers(dest="action", help="Analysis action")
    
    # analyze_load subcommand
    load_parser = subparsers.add_parser(
        "analyze_load", 
        help="Analyze Workspace and Virtual Cluster load"
    )
    load_parser.add_argument(
        "--days", type=int, default=30,
        help="Analysis period in days, default 30"
    )
    
    # analyze_tables subcommand
    tables_parser = subparsers.add_parser(
        "analyze_tables",
        help="Analyze table access statistics"
    )
    tables_parser.add_argument(
        "--days", type=int, default=30,
        help="Analysis period in days, default 30"
    )
    tables_parser.add_argument(
        "--limit", type=int, default=20,
        help="Return top N tables, default 20"
    )
    
    # analyze_cache subcommand
    cache_parser = subparsers.add_parser(
        "analyze_cache",
        help="Analyze cache hit rate"
    )
    cache_parser.add_argument(
        "--days", type=int, default=30,
        help="Analysis period in days, default 30"
    )
    
    # diagnose subcommand
    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Performance problem diagnosis"
    )
    diagnose_parser.add_argument(
        "--days", type=int, default=7,
        help="Analysis period in days, default 7"
    )
    diagnose_parser.add_argument(
        "--min_execution_time", type=int, default=300,
        help="Minimum execution time threshold in seconds, default 300"
    )
    diagnose_parser.add_argument(
        "--limit", type=int, default=50,
        help="Maximum results per query, default 50"
    )
    
    args = parser.parse_args()
    
    if not args.action:
        parser.print_help()
        sys.exit(1)
    
    # Execute corresponding analysis function
    if args.action == "analyze_load":
        result = analyze_load(days=args.days)
    elif args.action == "analyze_tables":
        result = analyze_tables(days=args.days, limit=args.limit)
    elif args.action == "analyze_cache":
        result = analyze_cache(days=args.days)
    elif args.action == "diagnose":
        result = diagnose(
            days=args.days,
            min_execution_time=args.min_execution_time,
            limit=args.limit
        )
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)
        sys.exit(1)
    
    # Output result
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
