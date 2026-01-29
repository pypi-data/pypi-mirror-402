#!/usr/bin/env python3
"""非增量原因诊断规则"""
from typing import Dict
from rules.base_rule import GlobalRule


class NonIncrementalDiagnosis(GlobalRule):
    name = "non_incremental_diagnosis"
    category = "incremental/state_table"
    description = "诊断为什么任务退化为全量刷新"
    rule_scope = "global"
    DIAGNOSIS_FLAGS = [
        ('cz.optimizer.explain.incremental.plan', 'true'),
        ('cz.optimizer.print.non.incremental.reason', 'true'),
        ('cz.optimizer.print.non.incremental.reason_msg_max_length', '100000'),
        ('cz.optimizer.incremental.force.incremental', 'true'),
    ]

    def analyze_global(self, context: Dict) -> Dict:
        """全局分析：只在检测到全量刷新时执行一次"""
        refresh_type = context.get('refresh_type')
        settings = context.get('settings', {})

        findings, recommendations, insights = [], [], []

        # 只在全量刷新时触发
        if refresh_type != 'FULL':
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        findings.append(self.create_finding('NON_INCREMENTAL_REFRESH', 'global', 'HIGH',
            '任务退化为全量刷新，需要诊断原因'))

        missing_flags = [(p, v) for p, v in self.DIAGNOSIS_FLAGS if p not in settings]
        for param, value in missing_flags:
            recommendations.append(self.create_recommendation(param, value, 1,
                '全量刷新诊断所需参数', 'HIGH'))

        if missing_flags:
            insights.append(self.create_insight(
                "任务退化为全量刷新，请设置诊断参数后执行 EXPLAIN REFRESH 查看原因", 'global'))
        else:
            insights.append(self.create_insight(
                "诊断参数已设置，请执行 EXPLAIN REFRESH 查看退化原因", 'global'))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

