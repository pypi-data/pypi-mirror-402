#!/usr/bin/env python3
"""Hash Join 优化规则"""
import json
from typing import Dict
from rules.base_rule import BaseRule

class HashJoinOptimization(BaseRule):
    name = "hash_join_optimization"
    category = "incremental/stage_optimization"
    description = "检测 Broadcast Hash Join 性能问题"
    STAGE_TIME_THRESHOLD_MS = 10000
    STAGE_PERCENT_THRESHOLD = 8.0
    JOIN_PERCENT_THRESHOLD = 30.0
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        metrics = stage_data.get('metrics', {})
        plan = stage_data.get('plan', {})
        total_time = context.get('total_job_time', 0)
        elapsed_ms = metrics.get('elapsed_ms', 0)
        time_pct = (elapsed_ms / total_time * 100) if total_time else 0
        if elapsed_ms < self.STAGE_TIME_THRESHOLD_MS and time_pct < self.STAGE_PERCENT_THRESHOLD:
            return False
        plan_str = json.dumps(plan)
        return 'BroadcastHashJoin' in plan_str or 'Broadcast' in plan_str
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        metrics = stage_data.get('metrics', {})
        profile = stage_data.get('profile', {})
        settings = context.get('settings', {})
        elapsed_ms = metrics.get('elapsed_ms', 0)
        input_gb = metrics.get('input_bytes', 0) / (1024**3)
        
        findings, recommendations, insights = [], [], []
        join_info = self._analyze_join_operators(profile, elapsed_ms)
        
        if join_info['has_slow_join']:
            findings.append(self.create_finding('BROADCAST_JOIN', stage_id, 'MEDIUM',
                f"Broadcast Join 耗时 {join_info['max_join_ms']/1000:.1f}s ({join_info['join_pct']:.0f}%)",
                {'join_time_ms': join_info['max_join_ms'], 'join_pct': join_info['join_pct'], 'input_gb': input_gb}))
            param = 'cz.optimizer.enable.broadcast.hash.join'
            if param not in settings or settings.get(param) != 'false':
                recommendations.append(self.create_recommendation(param, 'false', 2,
                    f"Stage {stage_id}: Broadcast Join 耗时 {join_info['max_join_ms']/1000:.1f}s, 数据 {input_gb:.1f}GB",
                    'MEDIUM', settings.get(param), warning="禁用后将使用 Shuffle Hash Join"))
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
    
    def _analyze_join_operators(self, profile: Dict, stage_elapsed_ms: float) -> Dict:
        result = {'has_slow_join': False, 'max_join_ms': 0, 'join_pct': 0}
        if 'operatorSummary' not in profile:
            return result
        for op_id, op_data in profile['operatorSummary'].items():
            if 'Join' in op_id:
                max_ms = int(op_data.get('wallTimeNs', {}).get('max', 0)) / 1_000_000
                if max_ms > result['max_join_ms']:
                    result['max_join_ms'] = max_ms
        if result['max_join_ms'] > 0 and stage_elapsed_ms > 0:
            result['join_pct'] = result['max_join_ms'] / stage_elapsed_ms * 100
            result['has_slow_join'] = result['join_pct'] > self.JOIN_PERCENT_THRESHOLD
        return result
