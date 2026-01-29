#!/usr/bin/env python3
"""
Clickzetta Job 性能分析工具
使用方法: python analyze_job.py <plan.json> <job_profile.json> [output_dir]
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from core.parser import PlanProfileParser
from core.aligner import StageAligner
from analyzers import get_analyzer

def print_header():
    print("=" * 80)
    print("Clickzetta Job 性能分析工具 v2.0")
    print("=" * 80)
    print("\n已实现规则:")
    print("  ✅ Stage/Operator 级别优化 (7条):")
    print("     增量/全量判断、单DOP聚合、Hash Join、TableSink DOP、最大DOP、Spilling、主动问题发现")
    print("  ✅ 状态表优化 (6条):")
    print("     非增量诊断、Row Number检查、Append-Only Scan、状态表启用、Aggregate复用、Calc状态优化")

def analyze_job(plan_file: str, profile_file: str, output_dir: str = ".", enable_state_table_analysis: bool = False):
    """
    分析 Job 性能

    Args:
        plan_file: plan.json 文件路径
        profile_file: job_profile.json 文件路径
        output_dir: 输出目录
        enable_state_table_analysis: 是否启用状态表优化分析（默认 False）
    """
    print("\n" + "=" * 80)
    print("步骤1: 解析输入文件")
    print("=" * 80)

    parser = PlanProfileParser(plan_file, profile_file)
    parsed_data = parser.parse()
    sql_info = parsed_data['sql_info']
    vc_mode = parsed_data['vc_mode']
    settings = parsed_data['settings']
    version_info = parsed_data['version_info']
    has_profile = parsed_data.get('has_profile', False)

    print(f"\n[SQL 类型] {'REFRESH SQL' if sql_info['is_refresh'] else 'Regular SQL'}")
    print(f"[VC 模式] {vc_mode['mode']} Mode")
    print(f"[版本信息] {version_info['git_branch']}")
    print(f"[已有参数] Total: {len(settings)}")
    print(f"[Profile 数据] {'有效' if has_profile else '无效或为空（部分分析将基于 plan.json）'}")
    print(f"[状态表分析] {'启用' if enable_state_table_analysis else '禁用（使用 --enable-state-table 启用）'}")
    
    print("\n" + "=" * 80)
    print("步骤2: Stage 对齐与统计")
    print("=" * 80)
    
    aligner = StageAligner(parsed_data)
    aligned_data = aligner.align()
    total_time = aligned_data['total_job_time']

    print(f"\n[统计] Aligned Stages: {len(aligned_data['aligned_stages'])}, 总耗时: {total_time/1000:.2f}s")

    # 只有在有 profile 数据时才显示性能统计
    if has_profile:
        top_stages = aligner.get_top_stages(10)
        print(f"\n[Top 10 Stage]")
        print(f"{'#':<4}{'Stage':<12}{'Time(s)':>10}{'%':>8}{'DOP':>8}")
        print("-" * 45)
        for i, (sid, m) in enumerate(top_stages, 1):
            pct = m['elapsed_ms'] / total_time * 100 if total_time else 0
            print(f"{i:<4}{sid:<12}{m['elapsed_ms']/1000:>10.2f}{pct:>8.1f}{m['dop']:>8}")

        top_ops = aligner.get_top_operators(10)
        print(f"\n[Top 10 Operator]")
        print(f"{'#':<4}{'Stage':<12}{'Operator':<25}{'Max(s)':>10}{'Stage%':>8}{'Skew':>8}")
        print("-" * 70)
        for i, op in enumerate(top_ops, 1):
            print(f"{i:<4}{op['stage_id']:<12}{op['operator_id']:<25}"
                  f"{op['max_time_ms']/1000:>10.2f}{op['stage_pct']:>8.1f}{op['skew_ratio']:>8.1f}")
    else:
        print("\n[提示] 没有 profile 数据，跳过性能统计展示")
    
    sql_type = 'REFRESH' if sql_info['is_refresh'] else 'REGULAR'
    analyzer = get_analyzer(sql_type=sql_type, vc_mode=vc_mode['mode'],
                           enable_state_table_rules=enable_state_table_analysis)
    analyzer.context['settings'] = settings
    analyzer.context['vc_mode'] = vc_mode['mode']
    analyzer.context['version_info'] = version_info
    analyzer.context['has_profile'] = has_profile  # 传递 profile 数据标志
    
    print("\n" + "=" * 80)
    print("步骤3: 执行规则分析")
    print("=" * 80)
    
    analyzer.analyze(aligned_data)
    reporter = analyzer.get_report()
    reporter.set_metadata('vc_mode', vc_mode['mode'])

    # 如果 context 中有增量算法数据，传递给 reporter
    if 'incremental_algorithms' in analyzer.context:
        reporter.set_incremental_algorithms(analyzer.context['incremental_algorithms'])

    print("\n" + reporter.generate_console_report(analyzer.context))
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "analysis_results.json")
    reporter.save_json_report(output_path)
    print(f"\n结果已保存: {output_path}")
    
    return reporter.generate_json_report()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Clickzetta Job 性能分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本分析（仅 Stage/Operator 级别优化）
  python analyze_job.py plan.json job_profile.json

  # 启用状态表优化分析
  python analyze_job.py plan.json job_profile.json --enable-state-table

  # 指定输出目录
  python analyze_job.py plan.json job_profile.json -o ./output --enable-state-table
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
