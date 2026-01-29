#!/usr/bin/env python3
"""增量计算分析器"""
from typing import Dict
from analyzers.base_analyzer import BaseAnalyzer
from rules.incremental.stage_optimization import (
    RefreshTypeDetection, SingleDopAggregate, HashJoinOptimization,
    TableSinkDop, MaxDopCheck, SpillingAnalysis, ActiveProblemFinding,
)
from rules.incremental.state_table import (
    NonIncrementalDiagnosis, RowNumberCheck, AppendOnlyScan,
    StateTableEnable, AggregateReuse, HeavyCalcState,
    IncrementalAlgorithmVisualization,
)


class IncrementalAnalyzer(BaseAnalyzer):
    name = "incremental_analyzer"
    description = "分析 REFRESH SQL 的性能问题"

    def __init__(self, enable_state_table_rules: bool = True):
        super().__init__()
        # Stage 级别规则
        self.stage_rules = [
            RefreshTypeDetection(), SingleDopAggregate(), HashJoinOptimization(),
            TableSinkDop(), MaxDopCheck(), SpillingAnalysis(), ActiveProblemFinding(),
        ]

        # 全局规则和 Stage 级别状态表规则
        self.global_rules = []
        self.state_table_rules = []

        if enable_state_table_rules:
            # 全局规则
            self.global_rules = [
                NonIncrementalDiagnosis(),
                IncrementalAlgorithmVisualization(),
            ]
            # Stage 级别状态表规则
            self.state_table_rules = [
                RowNumberCheck(), AppendOnlyScan(),
                StateTableEnable(), AggregateReuse(), HeavyCalcState(),
            ]

        self.refresh_type = None

    def analyze(self, aligned_data: Dict) -> Dict:
        aligned_stages = aligned_data.get('aligned_stages', {})
        self.context['total_job_time'] = aligned_data.get('total_job_time', 0)
        self.context['all_stage_metrics'] = aligned_data.get('stage_metrics', {})
        self.context['operator_analysis'] = aligned_data.get('operator_analysis', [])
        self.context['aligned_stages'] = aligned_stages
        self.context['stage_dependencies'] = aligned_data.get('stage_dependencies', {})
        self.context['reporter'] = self.reporter  # 传递 reporter 给规则

        all_results = {'findings': [], 'recommendations': [], 'insights': []}

        print("\n" + "=" * 80)
        print("阶段1: Stage/Operator 级别优化分析")
        print("=" * 80)

        # 执行 Stage 级别规则
        for stage_id, stage_data in aligned_stages.items():
            stage_data['stage_id'] = stage_id
            for rule in self.stage_rules:
                try:
                    if rule.check(stage_data, self.context):
                        result = rule.analyze(stage_data, self.context)
                        self._merge_results(all_results, result)
                        if rule.name == 'refresh_type_detection' and result.get('refresh_type'):
                            self.refresh_type = result['refresh_type']
                            self.context['refresh_type'] = self.refresh_type
                            print(f"  [{rule.name}] 刷新类型: {self.refresh_type}")
                        elif result.get('findings'):
                            print(f"  [{rule.name}] Stage {stage_id}: 发现 {len(result['findings'])} 个问题")
                except Exception as e:
                    print(f"  [{rule.name}] Stage {stage_id}: 异常 - {str(e)}")

        # 执行全局规则（只执行一次）
        if self.global_rules:
            print("\n" + "=" * 80)
            print("阶段2: 全局规则分析")
            print("=" * 80)
            for rule in self.global_rules:
                try:
                    result = rule.analyze_global(self.context)
                    self._merge_results(all_results, result)
                    if result.get('findings'):
                        print(f"  [{rule.name}] 发现 {len(result['findings'])} 个全局问题")
                except Exception as e:
                    print(f"  [{rule.name}] 异常 - {str(e)}")

        # 执行 Stage 级别状态表规则
        if self.state_table_rules:
            print("\n" + "=" * 80)
            print("阶段3: 状态表优化分析")
            print("=" * 80)
            for stage_id, stage_data in aligned_stages.items():
                stage_data['stage_id'] = stage_id
                for rule in self.state_table_rules:
                    try:
                        if rule.check(stage_data, self.context):
                            result = rule.analyze(stage_data, self.context)
                            self._merge_results(all_results, result)
                            if result.get('findings'):
                                print(f"  [{rule.name}] Stage {stage_id}: 发现 {len(result['findings'])} 个问题")
                    except Exception as e:
                        print(f"  [{rule.name}] Stage {stage_id}: 异常 - {str(e)}")

        for f in all_results['findings']:
            self.reporter.add_finding(f)
        for r in all_results['recommendations']:
            self.reporter.add_recommendation(r)
        for i in all_results['insights']:
            self.reporter.add_insight(i)

        self.reporter.set_metadata('sql_type', 'REFRESH')
        self.reporter.set_metadata('refresh_type', self.refresh_type)
        self.reporter.set_metadata('total_time_seconds', aligned_data.get('total_job_time', 0) / 1000)
        self.reporter.set_metadata('stage_count', len(aligned_stages))

        return all_results

    def _merge_results(self, target: Dict, source: Dict):
        target['findings'].extend(source.get('findings', []))
        target['recommendations'].extend(source.get('recommendations', []))
        target['insights'].extend(source.get('insights', []))

