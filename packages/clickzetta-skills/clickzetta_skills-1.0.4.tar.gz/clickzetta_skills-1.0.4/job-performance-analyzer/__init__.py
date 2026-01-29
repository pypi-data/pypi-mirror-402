"""
Clickzetta Job Performance Analyzer

自动诊断 Clickzetta Job 性能问题的工具，分析执行计划(plan.json)和运行概况(job_profile.json)，
识别瓶颈并给出参数优化建议。

支持场景:
- 增量计算(REFRESH)
- AP模式
- GP模式
- Compaction
- 各类SQL场景

已实现规则:
- Stage/Operator 级别优化 (7条规则)
- 状态表优化 (6条规则)
"""

__version__ = "2.0.0"
__author__ = "Clickzetta Team"

from .analyze_job import analyze_job, print_header

__all__ = ["analyze_job", "print_header"]
