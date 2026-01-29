#!/usr/bin/env python3
"""TableSink DOP 优化规则"""
from typing import Dict, List
from rules.base_rule import BaseRule
from utils.plan_navigator import create_stage_navigator


class TableSinkDop(BaseRule):
    name = "tablesink_dop"
    category = "incremental/stage_optimization"
    description = "检测 TableSink Stage 的 DOP 是否被自动调小"
    TIME_THRESHOLD_MS = 10000
    DOP_RATIO_THRESHOLD = 0.5

    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        metrics = stage_data.get('metrics', {})
        navigator = create_stage_navigator(stage_data)

        if not navigator.has_operator('TableSink'):
            return False
        return metrics.get('elapsed_ms', 0) >= self.TIME_THRESHOLD_MS

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        metrics = stage_data.get('metrics', {})
        settings = context.get('settings', {})
        current_dop = metrics.get('dop', 0)

        findings, recommendations, insights = [], [], []

        # 获取真正的上游 stage DOP
        upstream_stages = stage_data.get('upstream_stages', [])
        all_stage_metrics = context.get('all_stage_metrics', {})

        upstream_dops = []
        for upstream_id in upstream_stages:
            if upstream_id in all_stage_metrics:
                upstream_dop = all_stage_metrics[upstream_id].get('dop', 0)
                if upstream_dop > 0:
                    upstream_dops.append(upstream_dop)

        if not upstream_dops:
            insights.append(self.create_insight(
                f"Stage {stage_id}: 无法找到上游 Stage，跳过 DOP 检查", stage_id))
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        max_upstream = max(upstream_dops)

        # 检查 DOP 是否被调小
        if current_dop >= max_upstream:
            # 下游 DOP 大于等于上游，不需要调整
            insights.append(self.create_insight(
                f"Stage {stage_id}: DOP={current_dop} >= 上游最大 DOP={max_upstream}，无需调整", stage_id))
        else:
            dop_ratio = current_dop / max_upstream
            if dop_ratio >= self.DOP_RATIO_THRESHOLD:
                # DOP 差异不大
                insights.append(self.create_insight(
                    f"Stage {stage_id}: DOP={current_dop} 与上游接近 (max={max_upstream})，无需调整", stage_id))
            else:
                # DOP 被显著调小
                findings.append(self.create_finding('TABLESINK_DOP', stage_id, 'MEDIUM',
                    f"TableSink DOP={current_dop} 远小于上游 (max={max_upstream}, ratio={dop_ratio:.2f})",
                    {'current_dop': current_dop, 'max_upstream_dop': max_upstream,
                     'upstream_dops': upstream_dops, 'dop_ratio': dop_ratio}))

                param = 'cz.sql.enable.dag.auto.adaptive.split.size'
                if param not in settings or settings.get(param) != 'false':
                    recommendations.append(self.create_recommendation(param, 'false', 2,
                        f"Stage {stage_id}: TableSink DOP={current_dop} 可能被自动调小 (上游={max_upstream})",
                        'MEDIUM', settings.get(param),
                        warning="该参数影响全局，禁用后可能影响其他 Stage"))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

