#!/usr/bin/env python3
"""主动问题发现规则"""
from typing import Dict, List
from rules.base_rule import BaseRule

class ActiveProblemFinding(BaseRule):
    name = "active_problem_finding"
    category = "incremental/stage_optimization"
    description = "主动分析 Top 耗时 Stage 的瓶颈原因"
    MIN_STAGE_TIME_MS = 5000
    SKEW_THRESHOLD = 5.0
    SINGLE_OP_THRESHOLD = 80.0
    LOW_DOP_THRESHOLD = 10
    HIGH_SPILL_GB = 1.0
    
    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        return True  # 始终执行（如果有 profile 数据）
    
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        metrics = stage_data.get('metrics', {})
        total_time = context.get('total_job_time', 0)
        operator_analysis = context.get('operator_analysis', [])
        
        elapsed_ms = metrics.get('elapsed_ms', 0)
        time_pct = (elapsed_ms / total_time * 100) if total_time else 0
        dop = metrics.get('dop', 0)
        spill_gb = metrics.get('spill_bytes', 0) / (1024**3)
        
        findings, recommendations, insights = [], [], []
        
        if elapsed_ms < self.MIN_STAGE_TIME_MS:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
        
        # 找瓶颈 Operator
        stage_ops = sorted([op for op in operator_analysis if op['stage_id'] == stage_id],
                          key=lambda x: x['max_time_ms'], reverse=True)
        bottleneck = stage_ops[0] if stage_ops else None
        
        # 分析问题
        problems = self._analyze_problems(stage_id, elapsed_ms, dop, spill_gb, bottleneck)
        
        if problems:
            severity = 'HIGH' if time_pct > 30 else 'MEDIUM'
            findings.append(self.create_finding('BOTTLENECK_ANALYSIS', stage_id, severity,
                f"Stage 耗时 {elapsed_ms/1000:.1f}s ({time_pct:.1f}%)",
                {'elapsed_ms': elapsed_ms, 'time_pct': time_pct, 'problems': problems}))
            for p in problems:
                insights.append(self.create_insight(f"Stage {stage_id}: {p['description']}. 建议: {p['suggestion']}", stage_id))
        
        if bottleneck:
            insights.append(self.create_insight(
                f"Stage {stage_id} 瓶颈算子: {bottleneck['operator_id']}, "
                f"耗时 {bottleneck['max_time_ms']/1000:.1f}s ({bottleneck['stage_pct']:.1f}%), "
                f"倾斜 {bottleneck['skew_ratio']:.1f}x", stage_id))
        
        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}
    
    def _analyze_problems(self, stage_id, elapsed_ms, dop, spill_gb, bottleneck) -> List[Dict]:
        problems = []
        if bottleneck and bottleneck.get('skew_ratio', 1) > self.SKEW_THRESHOLD:
            problems.append({'type': 'DATA_SKEW', 'description': f"数据倾斜严重 ({bottleneck['skew_ratio']:.1f}x)",
                           'suggestion': 'SQL 改写或数据预处理', 'severity': 'HIGH'})
        if bottleneck and bottleneck.get('stage_pct', 0) > self.SINGLE_OP_THRESHOLD:
            problems.append({'type': 'SINGLE_OP_DOMINANT', 
                           'description': f"单个算子 {bottleneck['operator_id']} 占主导 ({bottleneck['stage_pct']:.1f}%)",
                           'suggestion': '检查算子逻辑或数据分布', 'severity': 'MEDIUM'})
        if 0 < dop <= self.LOW_DOP_THRESHOLD:
            problems.append({'type': 'LOW_DOP', 'description': f"DOP 较低 ({dop})",
                           'suggestion': '检查是否需要提高并行度', 'severity': 'MEDIUM'})
        if spill_gb > self.HIGH_SPILL_GB:
            problems.append({'type': 'HIGH_SPILLING', 'description': f"Spilling 较大 ({spill_gb:.2f} GB)",
                           'suggestion': '检查内存配置或数据倾斜', 'severity': 'MEDIUM'})
        if not problems and elapsed_ms > self.MIN_STAGE_TIME_MS * 2:
            problems.append({'type': 'GENERAL_SLOW', 'description': f"Stage 耗时较长 ({elapsed_ms/1000:.1f}s)",
                           'suggestion': '深入分析算子耗时分布', 'severity': 'LOW'})
        return problems
