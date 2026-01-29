#!/usr/bin/env python3
"""最大 DOP 提示规则"""
from typing import Dict
from rules.base_rule import BaseRule

class MaxDopCheck(BaseRule):
    name = "max_dop_check"
    category = "incremental/stage_optimization"
    description = "检查是否达到系统 DOP 限制"
    MAP_MAX_DOP = 4096
    REDUCE_MAX_DOP = 2048
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        return stage_data.get('metrics', {}).get('dop', 0) >= self.REDUCE_MAX_DOP
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        dop = stage_data.get('metrics', {}).get('dop', 0)
        settings = context.get('settings', {})
        findings, recommendations, insights = [], [], []
        
        if dop >= self.MAP_MAX_DOP:
            limit_type, limit_value = 'Map', self.MAP_MAX_DOP
            user_setting = 'cz.optimizer.mapper.stage.max.dop'
        else:
            limit_type, limit_value = 'Reduce', self.REDUCE_MAX_DOP
            user_setting = 'cz.optimizer.reducer.stage.max.dop'
        
        user_set_value = settings.get(user_setting)
        if user_set_value:
            findings.append(self.create_finding('MAX_DOP_USER_SET', stage_id, 'INFO',
                f"Stage DOP={dop} 达到 {limit_type} 限制，用户已设置 {user_setting}={user_set_value}"))
            insights.append(self.create_insight(
                f"Stage {stage_id}: DOP={dop} 达到 {limit_type} 限制，用户已设置参数，请确认是否符合预期", stage_id))
        else:
            insights.append(self.create_insight(
                f"Stage {stage_id}: DOP={dop} 达到 {limit_type} 系统限制 {limit_value}，这是正常的", stage_id))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
