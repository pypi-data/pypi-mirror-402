#!/usr/bin/env python3
"""Row Number=1 Pattern 检查规则"""
import json
from typing import Dict, List
from rules.base_rule import BaseRule

class RowNumberCheck(BaseRule):
    name = "row_number_check"
    category = "incremental/state_table"
    description = "检查 ROW_NUMBER=1 pattern 是否利用了 append-only 特性"
    ROW_NUMBER_PATTERNS = ['ROW_NUMBER', 'row_number', 'rn=1', 'rn = 1']
    INCREMENTAL_DELETE_COL = '__incremental_delete'
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        plan_str = json.dumps(stage_data.get('plan', {}))
        return any(p in plan_str for p in self.ROW_NUMBER_PATTERNS)
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        plan = stage_data.get('plan', {})
        settings = context.get('settings', {})
        findings, recommendations, insights = [], [], []
        
        append_only_tables = self._find_append_only_tables(plan)
        if append_only_tables:
            insights.append(self.create_insight(
                f"Stage {stage_id}: 发现 ROW_NUMBER pattern，输入表可能是 append-only: {', '.join(append_only_tables)}", stage_id))
            param = 'cz.optimizer.incremental.window.sd.to.sd.rule.enable'
            if settings.get(param) != 'false':
                recommendations.append(self.create_recommendation(param, 'false', 2,
                    f"Stage {stage_id}: 有 append-only 表和 ROW_NUMBER pattern", 'MEDIUM',
                    settings.get(param), warning="如果任务仍退化为全量刷新，需进一步诊断"))
            
            # 检查 hint
            append_only_setting = settings.get('cz.optimizer.incremental.append.only.tables', '')
            missing = [t for t in append_only_tables if t not in append_only_setting]
            if missing:
                findings.append(self.create_finding('MISSING_APPEND_ONLY_HINT', stage_id, 'WARNING',
                    f"以下 append-only 表缺少 hint: {', '.join(missing)}"))
                insights.append(self.create_insight(
                    f"Stage {stage_id}: 建议为 {', '.join(missing)} 添加 append-only hint", stage_id))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights, 
               'append_only_tables': append_only_tables}
    
    def _find_append_only_tables(self, plan: Dict) -> List[str]:
        append_only = []
        try:
            for op in plan.get('operators', []):
                if 'tableScan' in op:
                    table_name = op['tableScan'].get('table', {}).get('name', 'unknown')
                    cols = [f.get('name', '') for f in op['tableScan'].get('schema', {}).get('fields', [])]
                    if self.INCREMENTAL_DELETE_COL not in cols:
                        append_only.append(table_name)
        except:
            pass
        return append_only
