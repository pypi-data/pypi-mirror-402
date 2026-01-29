#!/usr/bin/env python3
"""Calc 状态优化规则"""
import json
from typing import Dict
from rules.base_rule import BaseRule

class HeavyCalcState(BaseRule):
    name = "heavy_calc_state"
    category = "incremental/state_table"
    description = "检测高耗时 Calc 算子，建议存储状态以避免重复计算"
    CALC_STAGE_PERCENT = 30.0
    STAGE_TOTAL_PERCENT = 10.0
    UDF_PATTERNS = ['udf', 'UDF', 'user_defined', 'custom_func', 'ScalarFunction']
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        operator_analysis = context.get('operator_analysis', [])
        stage_id = stage_data.get('stage_id')
        calc_ops = [op for op in operator_analysis if op['stage_id'] == stage_id and 'Calc' in op.get('operator_id', '')]
        return len(calc_ops) > 0
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        plan = stage_data.get('plan', {})
        metrics = stage_data.get('metrics', {})
        settings = context.get('settings', {})
        operator_analysis = context.get('operator_analysis', [])
        total_time = context.get('total_job_time', 0)
        
        elapsed_ms = metrics.get('elapsed_ms', 0)
        stage_pct = (elapsed_ms / total_time * 100) if total_time else 0
        findings, recommendations, insights = [], [], []
        
        stage_ops = [op for op in operator_analysis if op['stage_id'] == stage_id]
        calc_ops = [op for op in stage_ops if 'Calc' in op.get('operator_id', '')]
        
        for calc_op in calc_ops:
            calc_stage_pct = calc_op.get('stage_pct', 0)
            if calc_stage_pct < self.CALC_STAGE_PERCENT or stage_pct < self.STAGE_TOTAL_PERCENT:
                continue
            
            operator_id = calc_op.get('operator_id', 'unknown')
            has_udf = any(p in json.dumps(plan) for p in self.UDF_PATTERNS)
            
            findings.append(self.create_finding('HEAVY_CALC', stage_id, 'HIGH' if has_udf else 'MEDIUM',
                f"Calc {operator_id} 占 Stage {calc_stage_pct:.1f}%，Stage 占整体 {stage_pct:.1f}%",
                {'operator_id': operator_id, 'has_udf': has_udf}))
            
            param = 'cz.optimizer.incremental.create.rule.based.table.on.heavy.calc'
            if settings.get(param) != 'true':
                recommendations.append(self.create_recommendation(param, 'true', 2 if has_udf else 3,
                    f"Stage {stage_id}: Calc {operator_id} 耗时高{'（含 UDF）' if has_udf else ''}", 
                    'HIGH' if has_udf else 'MEDIUM'))
            
            insights.append(self.create_insight(
                f"Stage {stage_id}: Calc {operator_id} 占比高 ({calc_stage_pct:.1f}%)，考虑开启状态优化", stage_id))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
