#!/usr/bin/env python3
"""状态表启用建议规则"""
import json
from typing import Dict
from rules.base_rule import BaseRule

class StateTableEnable(BaseRule):
    name = "state_table_enable"
    category = "incremental/state_table"
    description = "判断是否应该开启状态表以优化增量计算"
    STATE_TABLE_PATTERNS = ['__state__', '__incr_state__', 'state_table']
    STATEFUL_OPS = ['HashAggregate', 'Window', 'Join']
    STATE_SIZE_RATIO = 10
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        return context.get('refresh_type') == 'INCREMENTAL'
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        plan = stage_data.get('plan', {})
        metrics = stage_data.get('metrics', {})
        settings = context.get('settings', {})
        plan_str = json.dumps(plan)
        findings, recommendations, insights = [], [], []
        
        if any(p in plan_str for p in self.STATE_TABLE_PATTERNS):
            insights.append(self.create_insight(f"Stage {stage_id}: 已包含状态表", stage_id))
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
        
        stateful_ops = [op for op in self.STATEFUL_OPS if op in plan_str]
        if not stateful_ops:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
        
        output_bytes = metrics.get('output_bytes', 0)
        input_bytes = metrics.get('input_bytes', 0)
        size_ratio = output_bytes / input_bytes if input_bytes > 0 else 0
        
        if size_ratio < self.STATE_SIZE_RATIO:
            findings.append(self.create_finding('STATE_TABLE_CANDIDATE', stage_id, 'INFO',
                f"Stage 包含 {', '.join(stateful_ops)}，建议开启状态表"))
            param = 'cz.optimizer.incremental.enable.state.table'
            if settings.get(param) != 'true':
                recommendations.append(self.create_recommendation(param, 'true', 3,
                    f"Stage {stage_id}: 包含 {', '.join(stateful_ops)}，开启状态表可避免重复计算", 'MEDIUM'))
            insights.append(self.create_insight(f"Stage {stage_id}: 状态表大小预估合理，建议开启", stage_id))
        else:
            insights.append(self.create_insight(
                f"Stage {stage_id}: 状态表可能过大 (ratio={size_ratio:.1f}x)，不建议开启", stage_id))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
