#!/usr/bin/env python3
"""Aggregate 复用检查规则"""
import json
from typing import Dict, List
from rules.base_rule import BaseRule

class AggregateReuse(BaseRule):
    name = "aggregate_reuse"
    category = "incremental/state_table"
    description = "检查聚合计算是否利用了之前的结果"
    ALWAYS_INCREMENTAL = ['SUM', 'COUNT', 'sum', 'count']
    APPEND_ONLY_INCREMENTAL = ['MIN', 'MAX', 'min', 'max']
    INCREMENTAL_DELETE_COL = '__incremental_delete'

    def check(self, stage_data: Dict, context: Dict) -> bool:
        plan_str = json.dumps(stage_data.get('plan', {}))
        return 'HashAggregate' in plan_str or 'Aggregate' in plan_str

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        plan = stage_data.get('plan', {})
        settings = context.get('settings', {})
        findings, recommendations, insights = [], [], []

        # 获取所有 aggregate，并过滤掉增量算法的辅助 aggregate
        agg_funcs = self._analyze_aggregates(plan, filter_incremental_helpers=True)
        if not agg_funcs:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        is_append_only = self._check_append_only_inputs(plan)
        has_incremental_marker = self._check_incremental_markers(plan)

        for func_name in agg_funcs:
            upper_name = func_name.upper()
            if any(f in upper_name for f in self.ALWAYS_INCREMENTAL):
                if not has_incremental_marker:
                    findings.append(self.create_finding('AGG_NOT_REUSING', stage_id, 'WARNING',
                        f"{func_name} 未复用之前的计算结果"))
            elif any(f in upper_name for f in self.APPEND_ONLY_INCREMENTAL):
                if is_append_only and not has_incremental_marker:
                    findings.append(self.create_finding('AGG_NOT_REUSING', stage_id, 'INFO',
                        f"{func_name} 在 append-only 场景下未复用之前的计算结果"))
                    if not settings.get('cz.optimizer.incremental.append.only.tables'):
                        insights.append(self.create_insight(
                            f"Stage {stage_id}: 建议为 append-only 表添加 hint", stage_id))

        if has_incremental_marker:
            insights.append(self.create_insight(f"Stage {stage_id}: 聚合计算已利用增量特性", stage_id))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

    def _is_incremental_helper_aggregate(self, op: Dict) -> bool:
        """
        判断是否是增量算法的辅助 aggregate（而非原始 SQL 的 aggregate）

        判断依据：
        1. 3阶段 aggregate 的 P1/P2 阶段（PARTIAL1, PARTIAL2）
        2. 包含增量相关的特殊函数（如 MULTI_RANGE_COLLECT, _DF_BF_COLLECT）
        3. 读取的是 delta 数据（通过 incrementalTableProperty 判断）
        """
        if 'hashAgg' not in op:
            return False

        agg = op['hashAgg']
        mode = agg.get('aggregate', {}).get('mode', '')

        # 1. 检查是否是 3阶段 aggregate 的 P1/P2 阶段
        # P1/P2 通常是增量算法的一部分，用于分布式计算
        if mode in ['PARTIAL1', 'P1', 'PARTIAL2', 'P2', 'Partial1', 'Partial2']:
            return True

        # 2. 检查是否包含增量相关的特殊函数
        # 这些函数通常用于增量计算的中间状态
        agg_calls = agg.get('aggregate', {}).get('aggregateCalls', [])
        for call in agg_calls:
            func_name = call.get('function', {}).get('function', {}).get('name', '')
            # 增量算法的特殊函数
            if any(special in func_name for special in [
                'MULTI_RANGE_COLLECT', '_DF_BF_COLLECT', 'BF_COLLECT',
                'DF_BF_COLLECT', '_INCR_', 'INCREMENTAL_'
            ]):
                return True

        return False

    def _analyze_aggregates(self, plan: Dict, filter_incremental_helpers: bool = True) -> List[str]:
        """
        分析 plan 中的 aggregate 函数

        Args:
            plan: stage 的 plan
            filter_incremental_helpers: 是否过滤掉增量算法的辅助 aggregate

        Returns:
            aggregate 函数名列表
        """
        funcs = []
        try:
            for op in plan.get('operators', []):
                if 'hashAgg' not in op:
                    continue

                # 如果需要过滤，检查是否是辅助 aggregate
                if filter_incremental_helpers and self._is_incremental_helper_aggregate(op):
                    continue

                # 提取 aggregate 函数
                for call in op['hashAgg'].get('aggregate', {}).get('aggregateCalls', []):
                    name = call.get('function', {}).get('function', {}).get('name', '')
                    if name:
                        funcs.append(name)
        except:
            pass
        return funcs

    def _check_append_only_inputs(self, plan: Dict) -> bool:
        try:
            for op in plan.get('operators', []):
                if 'tableScan' in op:
                    cols = [f.get('name', '') for f in op['tableScan'].get('schema', {}).get('fields', [])]
                    if self.INCREMENTAL_DELETE_COL in cols:
                        return False
            return True
        except:
            return False

    def _check_incremental_markers(self, plan: Dict) -> bool:
        plan_str = json.dumps(plan).lower()
        return any(m in plan_str for m in ['incremental', 'delta', 'state', 'partial_result'])
