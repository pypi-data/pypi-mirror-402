#!/usr/bin/env python3
"""单 DOP 聚合优化规则"""
from typing import Dict, Optional
from rules.base_rule import BaseRule
from utils.plan_navigator import create_stage_navigator


class SingleDopAggregate(BaseRule):
    name = "single_dop_aggregate"
    category = "incremental/stage_optimization"
    description = "检测单并行度聚合Stage，优化三阶段聚合配置"
    EXPENSIVE_FUNCTIONS = ['MULTI_RANGE_COLLECT', '_DF_BF_COLLECT', 'BF_COLLECT', 'DF_BF_COLLECT']
    TIME_THRESHOLD_MS = 12000
    PERCENT_THRESHOLD = 15.0
    BITS_LOW_THRESHOLD = 536870912  # 512M
    BITS_HIGH_THRESHOLD_V12 = 1073741824  # 1G (v1.2及以下版本默认值)
    BITS_HIGH_THRESHOLD_V13_PLUS = 536870912  # 512M (v1.2以上版本默认值)

    def _get_version_threshold(self, context: Dict) -> int:
        """根据版本获取对应的 bits 阈值"""
        version_info = context.get('version_info', {})
        git_branch = version_info.get('git_branch', '')

        # 从 git_branch 中提取版本号，如 "release-v1.2" -> "1.2"
        # 如果无法解析版本，默认使用 v1.2 的阈值（更保守）
        try:
            if 'release-v' in git_branch:
                version_str = git_branch.split('release-v')[1].split('-')[0]
                # 解析主版本号和次版本号
                parts = version_str.split('.')
                major = int(parts[0]) if len(parts) > 0 else 1
                minor = int(parts[1]) if len(parts) > 1 else 2

                # v1.2 及以下使用 1G，v1.3+ 使用 512M
                if major < 1 or (major == 1 and minor <= 2):
                    return self.BITS_HIGH_THRESHOLD_V12
                else:
                    return self.BITS_HIGH_THRESHOLD_V13_PLUS
        except (ValueError, IndexError):
            pass

        # 默认使用 v1.2 的阈值（1G）
        return self.BITS_HIGH_THRESHOLD_V12

    def check(self, stage_data: Dict, context: Dict) -> bool:
        # 如果没有 profile 数据，跳过此规则（需要运行时性能数据）
        if not self.has_profile_data(context):
            return False

        metrics = stage_data.get('metrics', {})
        total_time = context.get('total_job_time', 0)

        # 检查 DOP 是否为 1
        if metrics.get('dop') != 1:
            return False

        # 检查耗时是否超过阈值
        elapsed_ms = metrics.get('elapsed_ms', 0)
        time_pct = (elapsed_ms / total_time * 100) if total_time else 0
        if elapsed_ms < self.TIME_THRESHOLD_MS and time_pct < self.PERCENT_THRESHOLD:
            return False

        # 使用 PlanNavigator 检查是否有 HashAggregate
        navigator = create_stage_navigator(stage_data)
        if not navigator.has_operator('HashAggregate'):
            return False

        # 检查是否有昂贵的聚合函数
        if not navigator.has_aggregate_function(self.EXPENSIVE_FUNCTIONS):
            return False

        # 检查是否是 Final 或 Complete 状态（表示最后一个聚合阶段）
        # 如果是 Final/Complete，说明可能需要 3 阶段优化
        has_final_or_complete = (navigator.has_hash_aggregate_phase('FINAL') or
                                 navigator.has_hash_aggregate_phase('Complete'))

        # 如果有 Final/Complete，检查上游是否有 P2（判断是否已经是 3 阶段）
        if has_final_or_complete:
            # 检查上游是否有 P2
            upstream_stages = stage_data.get('upstream_stages', [])
            all_aligned_stages = context.get('aligned_stages', {})
            has_upstream_p2 = False

            for upstream_id in upstream_stages:
                if upstream_id in all_aligned_stages:
                    upstream_nav = create_stage_navigator(all_aligned_stages[upstream_id])
                    if upstream_nav.has_hash_aggregate_phase('P2') or upstream_nav.has_hash_aggregate_phase('PARTIAL2'):
                        has_upstream_p2 = True
                        break

            # 如果上游没有 P2，说明没有开启 3 阶段，需要优化
            if not has_upstream_p2:
                return True

        # 如果没有明确的 Final/Complete 标记，但有昂贵函数，也可能需要优化
        # （兼容 mode 为 None 的情况）
        return True

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        stage_id = stage_data.get('stage_id', 'unknown')
        metrics = stage_data.get('metrics', {})
        settings = context.get('settings', {})
        total_time = context.get('total_job_time', 0)
        elapsed_ms = metrics.get('elapsed_ms', 0)
        time_pct = (elapsed_ms / total_time * 100) if total_time else 0

        navigator = create_stage_navigator(stage_data)

        findings = [self.create_finding('SINGLE_DOP_AGG', stage_id, 'HIGH',
            f"DOP=1, 耗时={elapsed_ms/1000:.1f}s ({time_pct:.1f}%)",
            {'dop': 1, 'elapsed_ms': elapsed_ms, 'time_pct': time_pct})]
        recommendations, insights = [], []

        # 检查聚合阶段
        has_final = navigator.has_hash_aggregate_phase('FINAL')
        has_complete = navigator.has_hash_aggregate_phase('Complete')

        # 检查上游是否有 P2
        upstream_stages = stage_data.get('upstream_stages', [])
        all_aligned_stages = context.get('aligned_stages', {})
        has_upstream_p2 = False

        for upstream_id in upstream_stages:
            if upstream_id in all_aligned_stages:
                upstream_nav = create_stage_navigator(all_aligned_stages[upstream_id])
                if upstream_nav.has_hash_aggregate_phase('P2') or upstream_nav.has_hash_aggregate_phase('PARTIAL2'):
                    has_upstream_p2 = True
                    break

        # 判断是否需要开启三阶段
        if has_final or has_complete:
            if not has_upstream_p2:
                insights.append(self.create_insight(
                    f"Stage {stage_id}: 聚合处于 {'FINAL' if has_final else 'Complete'} 阶段，"
                    f"但上游缺少 P2，当前只有 2 阶段聚合", stage_id))
            else:
                insights.append(self.create_insight(
                    f"Stage {stage_id}: 已开启 3 阶段聚合（上游有 P2）", stage_id))

        # 检查三阶段聚合参数
        # 注意：cz.optimizer.incremental.df.three.phase.agg.enable 和
        # cz.optimizer.df.enable.three.phase.agg 是等价的，任一开启即可
        p1 = 'cz.optimizer.incremental.df.three.phase.agg.enable'
        p2 = 'cz.optimizer.df.enable.three.phase.agg'
        three_phase_enabled = settings.get(p1) == 'true' or settings.get(p2) == 'true'

        if not three_phase_enabled:
            recommendations.append(self.create_recommendation(p1, 'true', 1,
                f"Stage {stage_id}: 开启三阶段聚合以提升并行度", 'HIGH'))
        elif has_complete:
            # 如果已经开启三阶段但还是 Complete，可能是 one-pass 导致退化
            param = 'cz.optimizer.enable.one.pass.agg'
            if param not in settings or settings.get(param) != 'false':
                recommendations.append(self.create_recommendation(param, 'false', 2,
                    f"Stage {stage_id}: 禁用 one-pass 防止三阶段退化", 'MEDIUM'))
            insights.append(self.create_insight(
                f"Stage {stage_id}: 聚合退化为单阶段 (Complete)，可能是 one-pass 导致", stage_id))

        # 检查 BF bits 阈值（根据版本使用不同的默认阈值）
        bits = navigator.extract_aggregate_bits()
        version_threshold = self._get_version_threshold(context)

        if bits and self.BITS_LOW_THRESHOLD <= bits < version_threshold:
            param = 'cz.optimizer.df.three.phase.agg.bf.width.threshold'
            current = settings.get(param)
            if not current or int(current) > bits:
                version_info = context.get('version_info', {})
                git_branch = version_info.get('git_branch', 'Unknown')
                threshold_desc = f"{version_threshold} (版本 {git_branch} 的默认值)"

                recommendations.append(self.create_recommendation(param, str(bits), 3,
                    f"Stage {stage_id}: BF bits={bits}，需调整阈值使三阶段生效", 'MEDIUM',
                    current, warning=f"bits={bits} < 默认阈值 {threshold_desc}"))
                insights.append(self.create_insight(
                    f"Stage {stage_id}: BF bits={bits} < 默认阈值 {threshold_desc}，"
                    f"可能导致三阶段未生效", stage_id))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}


