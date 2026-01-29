#!/usr/bin/env python3
"""测试增量算法分析器"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.incremental_algorithm_analyzer import IncrementalAlgorithmAnalyzer


def test_basic_analysis():
    """测试基本的增量算法分析"""
    print("=" * 80)
    print("测试: 基本增量算法分析")
    print("=" * 80)

    # 创建测试数据
    plan = {
        'operators': [
            # TableScan - delta
            {
                'id': '100',
                'tableScan': {
                    'incrementalTableProperty': {
                        'from': 28800,
                        'to': 57600
                    }
                }
            },
            # TableScan - snapshot (上个状态)
            {
                'id': '101',
                'tableScan': {
                    'incrementalTableProperty': {
                        'from': -9223372036854775808,  # MIN_LONG
                        'to': 28800
                    }
                }
            },
            # Join (有 Rule hint)
            {
                'id': '102',
                'join': {
                    'hint': 'Rule:IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766417'
                }
            },
            # Aggregate P1 (有 Rule hint)
            {
                'id': '103',
                'hashAgg': {
                    'hint': 'Rule:IncrementalLinearFunctionAggregateRule_cz::optimizer::LogicalAggregate#12345',
                    'mode': 'P1'
                }
            },
            # Aggregate P2 (有 Rule hint)
            {
                'id': '104',
                'hashAgg': {
                    'hint': 'Rule:IncrementalLinearFunctionAggregateRule_cz::optimizer::LogicalAggregate#12345',
                    'mode': 'P2'
                }
            },
            # Aggregate Final (有 Rule hint)
            {
                'id': '105',
                'hashAgg': {
                    'hint': 'Rule:IncrementalLinearFunctionAggregateRule_cz::optimizer::LogicalAggregate#12345',
                    'mode': 'Final'
                }
            }
        ]
    }

    # 创建分析器
    analyzer = IncrementalAlgorithmAnalyzer(plan)

    # 执行分析
    result = analyzer.analyze()

    # 输出结果
    print("\n[算子 ID 映射]")
    print(f"共 {len(analyzer.operator_ids)} 个算子")
    for idx, op_id in analyzer.operator_ids.items():
        print(f"  索引 {idx} -> ID {op_id}")

    print("\n[数据类型识别]")
    print(f"识别出 {len(result['operator_data_types'])} 个算子的数据类型")
    for op_id, data_type in result['operator_data_types'].items():
        print(f"  算子 {op_id}: {data_type}")

    print("\n[Rule 分组]")
    print(f"识别出 {len(result['rule_groups'])} 个 Rule 组")
    for rule_id, op_ids in result['rule_groups'].items():
        print(f"  {rule_id}:")
        print(f"    算子 ID: {op_ids}")

    print("\n[增量算法]")
    print(f"识别出 {len(result['incremental_algorithms'])} 个增量算法")
    for i, algo in enumerate(result['incremental_algorithms'], 1):
        print(f"\n  算法 {i}:")
        print(f"    类型: {algo['type']}")
        print(f"    Rule ID: {algo['rule_id']}")
        print(f"    原始 SQL: {algo['is_original_sql']}")
        print(f"    Rule hint 算子 ({len(algo['rule_operators'])}): {algo['rule_operators']}")
        print(f"    完整 subplan ({len(algo['operators'])}): {algo['operators']}")
        print(f"    Root 算子: {algo['root_operator_id']}")

    print("\n[依赖关系图]")
    print(result['dependency_graph'])

    # 验证关键点
    print("\n[验证]")
    checks = []

    # 检查1: 使用实际 ID 而不是索引
    for op_id in result['operator_data_types'].keys():
        if op_id.startswith('op_'):
            checks.append(f"❌ 发现使用索引作为 ID: {op_id}")
        else:
            checks.append(f"✅ 使用实际 ID: {op_id}")

    # 检查2: 完整 subplan 包含所有相关算子
    for algo in result['incremental_algorithms']:
        subplan_size = len(algo['operators'])
        hint_size = len(algo['rule_operators'])
        if subplan_size > hint_size:
            checks.append(f"✅ 算法 {algo['type']} 的 subplan ({subplan_size} 个算子) > hint 算子 ({hint_size} 个)")
        else:
            checks.append(f"⚠️  算法 {algo['type']} 的 subplan ({subplan_size} 个算子) == hint 算子 ({hint_size} 个)")

    for check in checks:
        print(f"  {check}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_basic_analysis()
