#!/usr/bin/env python3
"""Append-Only Scan 检查规则"""
import json
from typing import Dict, List
from rules.base_rule import BaseRule

class AppendOnlyScan(BaseRule):
    name = "append_only_scan"
    category = "incremental/state_table"
    description = "检查 append-only 表是否被正确识别和优化"
    INCREMENTAL_DELETE_COL = '__incremental_delete'
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        plan_str = json.dumps(stage_data.get('plan', {}))
        return 'tableScan' in plan_str or 'TableScan' in plan_str
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        plan = stage_data.get('plan', {})
        settings = context.get('settings', {})
        findings, recommendations, insights = [], [], []
        
        table_analysis = self._analyze_tables(plan)
        for info in table_analysis:
            if info['is_append_only']:
                insights.append(self.create_insight(
                    f"Stage {stage_id}: 表 {info['name']} 是 append-only", stage_id))
                if info['has_join'] or info['has_agg']:
                    ops = []
                    if info['has_join']: ops.append('Join')
                    if info['has_agg']: ops.append('Aggregate')
                    append_only_tables = settings.get('cz.optimizer.incremental.append.only.tables', '')
                    if info['name'] not in append_only_tables:
                        findings.append(self.create_finding('POTENTIAL_OPTIMIZATION', stage_id, 'INFO',
                            f"append-only 表 {info['name']} 有 {', '.join(ops)}，可能有优化空间"))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
    
    def _analyze_tables(self, plan: Dict) -> List[Dict]:
        results = []
        plan_str = json.dumps(plan)
        try:
            for op in plan.get('operators', []):
                if 'tableScan' in op:
                    table_name = op['tableScan'].get('table', {}).get('name', 'unknown')
                    cols = [f.get('name', '') for f in op['tableScan'].get('schema', {}).get('fields', [])]
                    results.append({
                        'name': table_name,
                        'is_append_only': self.INCREMENTAL_DELETE_COL not in cols,
                        'has_join': 'Join' in plan_str,
                        'has_agg': 'HashAggregate' in plan_str or 'Aggregate' in plan_str,
                    })
        except:
            pass
        return results
