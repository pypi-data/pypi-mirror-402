#!/usr/bin/env python3
"""
Clickzetta Job 性能分析工具 - 命令行入口

使用方法:
    cz-analyze-job <plan.json> <job_profile.json> [options]

示例:
    # 基本分析
    cz-analyze-job plan.json job_profile.json

    # 启用状态表优化分析
    cz-analyze-job plan.json job_profile.json --enable-state-table

    # 指定输出目录
    cz-analyze-job plan.json job_profile.json -o ./output
"""
import sys
import os
import argparse

def main():
    """命令行入口函数"""
    # Import here to avoid circular imports
    from .analyze_job import analyze_job, print_header

    parser = argparse.ArgumentParser(
        description='Clickzetta Job 性能分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本分析（仅 Stage/Operator 级别优化）
  cz-analyze-job plan.json job_profile.json

  # 启用状态表优化分析
  cz-analyze-job plan.json job_profile.json --enable-state-table

  # 指定输出目录
  cz-analyze-job plan.json job_profile.json -o ./output --enable-state-table
        """
    )

    parser.add_argument('plan_file', help='plan.json 文件路径')
    parser.add_argument('profile_file', help='job_profile.json 文件路径')
    parser.add_argument('-o', '--output', dest='output_dir', default='.',
                       help='输出目录（默认: 当前目录）')
    parser.add_argument('--enable-state-table', action='store_true',
                       help='启用状态表优化分析（默认禁用）')

    args = parser.parse_args()

    if not os.path.exists(args.plan_file):
        print(f"错误: 文件不存在 - {args.plan_file}")
        sys.exit(1)
    if not os.path.exists(args.profile_file):
        print(f"错误: 文件不存在 - {args.profile_file}")
        sys.exit(1)

    print_header()
    analyze_job(args.plan_file, args.profile_file, args.output_dir, args.enable_state_table)

if __name__ == '__main__':
    main()
