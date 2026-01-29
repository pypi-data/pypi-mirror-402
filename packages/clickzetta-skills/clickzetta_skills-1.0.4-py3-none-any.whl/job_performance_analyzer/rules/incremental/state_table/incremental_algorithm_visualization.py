#!/usr/bin/env python3
"""增量算法可视化规则 - 展示增量算法的依赖关系"""
from typing import Dict, List, Optional
from rules.base_rule import GlobalRule
from utils.incremental_algorithm_analyzer import create_incremental_analyzer


class IncrementalAlgorithmVisualization(GlobalRule):
    name = "incremental_algorithm_visualization"
    category = "incremental/state_table"
    description = "可视化增量算法的依赖关系，展示哪些算子计算 aggregate/join/window"
    rule_scope = "global"

    def analyze_global(self, context: Dict) -> Dict:
        """
        全局分析：将所有 stage 的 operators 合并后进行全局增量算法分析

        关键改进：
        - 不再按 stage 独立分析（会导致跨 stage 的算子依赖无法追踪）
        - 将所有 operators 合并成一个全局 plan
        - 这样可以正确追踪跨 stage 的依赖关系（通过 inputIds）
        - 解决了 4.2.1.3.1 的要求：Aggregate 增量算法需要找到 Final/Complete 状态的 Aggregate
        """
        findings, recommendations, insights = [], [], []
        aligned_stages = context.get('aligned_stages', {})

        if not aligned_stages:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        # 关键修改：将所有 stage 的 operators 合并成一个全局 plan
        all_operators = []
        operator_to_stage = {}  # operator_id -> stage_id 的映射

        for stage_id, stage_data in aligned_stages.items():
            operators = stage_data.get('plan_operators', [])
            for op in operators:
                op_id = op.get('id')
                if op_id:
                    all_operators.append(op)
                    operator_to_stage[op_id] = stage_id

        if not all_operators:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        # 创建全局 plan 并分析
        global_plan = {'operators': all_operators}

        try:
            from utils.incremental_algorithm_analyzer import IncrementalAlgorithmAnalyzer
            analyzer = IncrementalAlgorithmAnalyzer(global_plan)
            result = analyzer.analyze()

            algorithms = result.get('incremental_algorithms', [])
            if not algorithms:
                return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

            # 构建算法信息，添加 stage 信息
            algorithm_merge_map = {}

            for algo in algorithms:
                rule_id = algo['rule_id']
                if rule_id not in algorithm_merge_map:
                    # 找出这个算法涉及的所有 stage
                    involved_stages = set()
                    for op_id in algo['operators']:
                        if op_id in operator_to_stage:
                            involved_stages.add(operator_to_stage[op_id])

                    algorithm_merge_map[rule_id] = {
                        'type': algo['type'],
                        'is_original_sql': algo['is_original_sql'],
                        'stages': sorted(list(involved_stages)),
                        'operators': algo['operators'],          # 完整 subplan 的算子 ID
                        'rule_operators': algo.get('rule_operators', []),     # 仅 hint 算子 ID
                        'target_operator_id': algo.get('target_operator_id'),
                        'root_operator_id': algo.get('root_operator_id'),
                        'operator_details': []
                    }

                    # 保存算子详细信息（包括 stage_id 和实际 operator_id）
                    for op_id in algo['operators']:
                        stage_id = operator_to_stage.get(op_id, 'unknown')
                        algorithm_merge_map[rule_id]['operator_details'].append({
                            'stage_id': stage_id,
                            'operator_id': op_id  # 使用实际 operator ID
                        })

            # 保存到 context 供其他规则使用
            context['incremental_algorithms'] = list(algorithm_merge_map.values())
            context['operator_data_types'] = result.get('operator_data_types', {})

        except Exception as e:
            # 静默失败，不影响其他分析
            import traceback
            print(f"\n[WARNING] 增量算法分析失败: {str(e)}")
            print(traceback.format_exc())
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        # 如果没有检测到增量算法，不输出任何内容
        if not algorithm_merge_map:
            return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

        # 合并后的增量算法列表
        merged_algorithms = []
        for rule_id, algo_info in algorithm_merge_map.items():
            merged_algo = {
                'rule_id': rule_id,
                'type': algo_info['type'],
                'is_original_sql': algo_info['is_original_sql'],
                'stages': algo_info['stages'],
                'operators': algo_info['operator_details'],      # 保存所有算子详情（包括 stage_id 和 operator_id）
                'total_operators': len(algo_info['operators']),  # 完整 subplan 大小
                'rule_operators_count': len(algo_info['rule_operators']),  # hint 算子数量
                'root_operator': self._find_root_operator(algo_info['operator_details'])
            }
            merged_algorithms.append(merged_algo)

        # 构建 stage_algorithm_map（每个 stage 包含哪些算法）
        stage_algorithm_map = {}
        for algo in merged_algorithms:
            for stage_id in algo['stages']:
                if stage_id not in stage_algorithm_map:
                    stage_algorithm_map[stage_id] = {'algorithms': []}
                stage_algorithm_map[stage_id]['algorithms'].append(algo['rule_id'])

        # 获取验证警告
        validation_warnings = result.get('validation_warnings', [])

        # 将结构化数据保存到 context，供外部访问
        incremental_algorithms_data = {
            'algorithms': merged_algorithms,
            'stage_algorithm_map': stage_algorithm_map,
            'summary': {
                'total_algorithms': len(merged_algorithms),
                'by_type': self._count_by_type_merged(merged_algorithms),
                'by_stage': {stage_id: len(info['algorithms'])
                           for stage_id, info in stage_algorithm_map.items()}
            },
            'validation_warnings': validation_warnings  # 添加验证警告
        }
        context['incremental_algorithms'] = incremental_algorithms_data

        # 将增量算法数据传递给 Reporter（如果存在）
        if 'reporter' in context:
            context['reporter'].set_incremental_algorithms(incremental_algorithms_data)

        # 检查验证警告并显示
        if validation_warnings:
            print(f"\n[WARNING] 增量算法验证发现 {len(validation_warnings)} 个问题:")
            for warning in validation_warnings[:10]:  # 只显示前 10 个
                print(f"  ⚠️  {warning}")
            if len(validation_warnings) > 10:
                print(f"  ... 还有 {len(validation_warnings) - 10} 个警告未显示")

        # 生成全局的增量算法摘要（用于控制台显示）
        summary_lines = [
            "",
            "=" * 70,
            "增量算法分析摘要",
            "=" * 70,
            ""
        ]

        # 按算法类型分组统计
        algo_by_type = self._count_by_type_merged(merged_algorithms)

        summary_lines.append("检测到的增量算法（跨 stage 合并后）：")
        for algo_type, counts in algo_by_type.items():
            summary_lines.append(
                f"  - {algo_type.upper()}: "
                f"{counts['original']} 个原始SQL算子, "
                f"{counts['helper']} 个算法辅助算子"
            )

        summary_lines.append("")
        summary_lines.append(f"总共 {len(merged_algorithms)} 个增量算法")
        summary_lines.append("")

        # 显示每个算法的详细信息
        summary_lines.append("增量算法详情：")
        summary_lines.append("")

        for i, algo in enumerate(merged_algorithms[:10], 1):  # 只显示前 10 个
            algo_type = algo['type'].upper()
            rule_id = algo['rule_id']
            stages = algo['stages']
            total_ops = algo['total_operators']
            rule_ops_count = algo.get('rule_operators_count', 0)
            root_op = algo['root_operator']

            # 简化 rule_id 显示
            if '#' in rule_id:
                short_id = rule_id.split('#')[-1]
                summary_lines.append(f"{i}. [{algo_type}] #{short_id}")
            else:
                summary_lines.append(f"{i}. [{algo_type}] {rule_id[:50]}...")

            summary_lines.append(f"   跨 {len(stages)} 个 stage: {', '.join(stages[:5])}")
            if len(stages) > 5:
                summary_lines.append(f"   ... 等共 {len(stages)} 个 stage")

            summary_lines.append(f"   完整 subplan: {total_ops} 个算子 (其中 {rule_ops_count} 个有 Rule hint)")

            if root_op:
                summary_lines.append(f"   Root 算子: stage={root_op['stage_id']}, id={root_op['operator_id']}")

            summary_lines.append("")

        if len(merged_algorithms) > 10:
            summary_lines.append(f"... 还有 {len(merged_algorithms) - 10} 个算法未显示")
            summary_lines.append("")

        summary = '\n'.join(summary_lines)

        # 添加为 insight
        insights.append(self.create_insight(summary, 'global'))

        return {'findings': findings, 'recommendations': recommendations, 'insights': insights}

    def _find_root_operator(self, operator_details: List[Dict]) -> Optional[Dict]:
        """
        找到增量算法的 root 节点（最上层算子）

        根据 prompt 4.2.1.3：找到算子对应的 root 阶段

        逻辑：
        1. Root 算子是整个增量算法的最顶层算子（最后执行的算子）
        2. 简化实现：返回最后一个算子（按列表顺序）

        注意：operator_details 中的 'operator_id' 现在是实际的 operator ID，不是索引
        """
        if not operator_details:
            return None

        # 简化实现：返回最后一个算子
        # 在实际的增量算法分析器中已经找到了 root_operator_id
        # 这里只是为了兼容性，返回列表中的最后一个算子
        return operator_details[-1] if operator_details else None

    def _count_by_type_merged(self, algorithms: List[Dict]) -> Dict:
        """按算法类型统计（合并后的算法）"""
        algo_by_type = {}
        for algo in algorithms:
            algo_type = algo['type']
            if algo_type not in algo_by_type:
                algo_by_type[algo_type] = {'original': 0, 'helper': 0}

            if algo['is_original_sql']:
                algo_by_type[algo_type]['original'] += 1
            else:
                algo_by_type[algo_type]['helper'] += 1
        return algo_by_type
