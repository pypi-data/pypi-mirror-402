#!/usr/bin/env python3
"""增量/全量 REFRESH 判断规则"""
from typing import Dict
from rules.base_rule import BaseRule
from utils.plan_navigator import create_stage_navigator


class RefreshTypeDetection(BaseRule):
    name = "refresh_type_detection"
    category = "incremental/stage_optimization"
    description = "判断 REFRESH SQL 是增量还是全量刷新"
    INTERMEDIATE_PATTERNS = ['__incr__', '__state__', '__incr_state__', '__temp__', '__intermediate__']

    def check(self, stage_data: Dict, context: Dict) -> bool:
        navigator = create_stage_navigator(stage_data)
        return navigator.has_operator('TableSink')

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        navigator = create_stage_navigator(stage_data)

        findings, recommendations, insights = [], [], []

        # 获取表名（从 path[2] 提取）
        table_name = navigator.get_refresh_table_name()

        # 检查是否是中间状态表（需要忽略）
        if table_name and any(pattern in table_name for pattern in self.INTERMEDIATE_PATTERNS):
            insights.append(self.create_insight(
                f"Stage {stage_id}: 跳过中间状态表 {table_name}", stage_id))
            return {'findings': findings, 'recommendations': recommendations,
                   'insights': insights, 'refresh_type': None}

        # 判断是增量还是全量
        # 逻辑（基于 table.path）：
        # 1. path 是 4 元组且最后一个元素是 __delta__ → 增量（写入 delta 文件）
        # 2. path 是 3 元组且 overwrite=false → 增量
        # 3. 其他情况（3 元组且 overwrite=true）→ 全量
        is_incremental = navigator.is_delta_table_sink()
        is_overwrite = navigator.is_overwrite_sink()

        # 获取完整路径用于显示
        full_path = navigator.get_table_full_path()

        if is_incremental:
            # 增量刷新
            refresh_type = 'INCREMENTAL'
            # 检查是否是 delta 文件写入
            plan = stage_data.get('plan', {})
            for op in plan.get('operators', []):
                if 'tableSink' in op:
                    path = op['tableSink'].get('table', {}).get('path', [])
                    if len(path) == 4 and path[-1] == '__delta__':
                        insights.append(self.create_insight(
                            f"Stage {stage_id}: 检测到增量刷新 (写入 delta 文件: {full_path or table_name})", stage_id))
                        break
            else:
                insights.append(self.create_insight(
                    f"Stage {stage_id}: 检测到增量刷新 (overwrite=false, 表: {full_path or table_name})", stage_id))
        else:
            # 全量刷新
            refresh_type = 'FULL'
            findings.append(self.create_finding('FULL_REFRESH', stage_id, 'WARNING',
                f'检测到全量刷新 (表: {full_path or table_name or "unknown"}, overwrite={is_overwrite})',
                {'table_name': table_name, 'full_path': full_path, 'is_overwrite': is_overwrite}))
            insights.append(self.create_insight(
                f"Stage {stage_id}: 全量刷新可能导致性能问题，建议检查增量计算配置", stage_id))

        return {'findings': findings, 'recommendations': recommendations,
               'insights': insights, 'refresh_type': refresh_type}



