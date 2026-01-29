#!/usr/bin/env python3
"""Spilling 分析规则"""
from typing import Dict, List
from rules.base_rule import BaseRule


class SpillingAnalysis(BaseRule):
    name = "spilling_analysis"
    category = "incremental/stage_optimization"
    description = "检测内存溢出到磁盘的情况，区分 Stage 级别和 Operator 级别"
    STAGE_SPILL_THRESHOLD_GB = 1.0
    OPERATOR_SPILL_THRESHOLD_GB = 0.5
    IGNORABLE_SPILL_PATTERNS = ['ShuffleWrite', 'ShuffleExchange', 'Exchange']

    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        spill_bytes = stage_data.get('metrics', {}).get('spill_bytes', 0)
        return spill_bytes > 0

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        metrics = stage_data.get('metrics', {})
        profile = stage_data.get('profile', {})
        stage_spill_gb = metrics.get('spill_bytes', 0) / (1024**3)

        findings, recommendations, insights = [], [], []

        # Stage 级别 Spilling 分析
        if stage_spill_gb >= self.STAGE_SPILL_THRESHOLD_GB:
            severity = 'HIGH' if stage_spill_gb >= self.STAGE_SPILL_THRESHOLD_GB * 3 else 'MEDIUM'
            findings.append(self.create_finding('STAGE_SPILLING', stage_id, severity,
                f"Stage 级别 Spilling: {stage_spill_gb:.2f} GB",
                {'spill_gb': stage_spill_gb, 'level': 'stage'}))

            if stage_spill_gb >= self.STAGE_SPILL_THRESHOLD_GB * 2:
                insights.append(self.create_insight(
                    f"Stage {stage_id}: Spilling 较大 ({stage_spill_gb:.2f} GB)，"
                    f"建议检查数据倾斜或增加内存配置", stage_id))

        # Operator 级别 Spilling 分析
        operator_spills = self._analyze_operator_spilling(stage_id, profile)

        for op_spill in operator_spills:
            op_id = op_spill['operator_id']
            spill_gb = op_spill['spill_gb']
            is_ignorable = op_spill['is_ignorable']

            if is_ignorable:
                # Shuffle Write 的 spill 可以忽略
                insights.append(self.create_insight(
                    f"Stage {stage_id}: {op_id} Spilling {spill_gb:.2f} GB (Shuffle Write，可忽略)", stage_id))
            elif spill_gb >= self.OPERATOR_SPILL_THRESHOLD_GB:
                # 需要关注的 Operator Spilling
                severity = 'HIGH' if spill_gb >= self.OPERATOR_SPILL_THRESHOLD_GB * 2 else 'MEDIUM'
                findings.append(self.create_finding('OPERATOR_SPILLING', stage_id, severity,
                    f"Operator {op_id} Spilling: {spill_gb:.2f} GB",
                    {'operator_id': op_id, 'spill_gb': spill_gb, 'level': 'operator'}))

                insights.append(self.create_insight(
                    f"Stage {stage_id}: {op_id} Spilling {spill_gb:.2f} GB，需关注", stage_id))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

    def _analyze_operator_spilling(self, stage_id: str, profile: Dict) -> List[Dict]:
        """分析 Operator 级别的 Spilling"""
        operator_spills = []

        if 'operatorSummary' not in profile:
            return operator_spills

        for op_id, op_data in profile['operatorSummary'].items():
            # 检查是否有 spillStats
            spill_bytes = 0

            if 'spillStats' in op_data:
                spill_stats = op_data['spillStats']
                if isinstance(spill_stats, dict):
                    spill_bytes = int(spill_stats.get('spillingBytes', 0))
                elif isinstance(spill_stats, (int, float)):
                    spill_bytes = int(spill_stats)

            # 也检查 inputOutputStats 中的 spillingBytes
            if 'inputOutputStats' in op_data:
                io_stats = op_data['inputOutputStats']
                io_spill = int(io_stats.get('spillingBytes', 0))
                spill_bytes = max(spill_bytes, io_spill)

            if spill_bytes > 0:
                spill_gb = spill_bytes / (1024**3)
                is_ignorable = any(pattern in op_id for pattern in self.IGNORABLE_SPILL_PATTERNS)

                operator_spills.append({
                    'operator_id': op_id,
                    'spill_bytes': spill_bytes,
                    'spill_gb': spill_gb,
                    'is_ignorable': is_ignorable,
                })

        return sorted(operator_spills, key=lambda x: x['spill_gb'], reverse=True)

