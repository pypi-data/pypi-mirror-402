#!/usr/bin/env python3
"""测试双向 DFS - 找到后续的 Aggregate 算子"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.incremental_algorithm_analyzer import IncrementalAlgorithmAnalyzer


def test_bidirectional_search():
    """
    测试双向搜索能否找到后续的 Aggregate 算子

    场景：
    - Rule hint 在前面的 Join 上
    - 目标 Aggregate 在后面
    - 应该向上搜索找到 Aggregate
    """
    print("=" * 80)
    print("测试: 双向 DFS 找到后续 Aggregate")
    print("=" * 80)

    # 创建测试数据
    plan = {
        'operators': [
            # TableScan - delta (ID: 100)
            {
                'id': '100',
                'tableScan': {
                    'incrementalTableProperty': {
                        'from': 28800,
                        'to': 57600
                    }
                }
            },
            # TableScan - snapshot (ID: 101)
            {
                'id': '101',
                'tableScan': {
                    'incrementalTableProperty': {
                        'to': 28800
                    }
                }
            },
            # Join - 有 Aggregate Rule hint (ID: 102)
            {
                'id': '102',
                'join': {
                    'hint': 'Rule:IncrementalAggregateSetDeltaRule_cz::optimizer::AggregatePhase#31770258'
                }
            },
            # Calc - 中间算子 (ID: 103)
            {
                'id': '103',
                'calc': {}
            },
            # Aggregate P1 (ID: 104)
            {
                'id': '104',
                'hashAgg': {
                    'mode': 'P1'
                }
            },
            # Aggregate P2 (ID: 105)
            {
                'id': '105',
                'hashAgg': {
                    'mode': 'P2'
                }
            },
            # Aggregate Final - 目标算子 (ID: 1418)
            {
                'id': '1418',
                'hashAgg': {
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
    for idx, op_id in analyzer.operator_ids.items():
        op_type = analyzer._get_operator_type(analyzer.operators[idx])
        print(f"  索引 {idx} -> ID {op_id} ({op_type})")

    print("\n[算子依赖关系]")
    for idx in range(len(analyzer.operators)):
        op_id = analyzer.operator_ids[idx]
        deps = analyzer.operator_dependencies.get(idx, [])
        dependents = analyzer.operator_dependents.get(idx, [])
        print(f"  {op_id}:")
        if deps:
            print(f"    输入: {[analyzer.operator_ids[d] for d in deps]}")
        if dependents:
            print(f"    输出到: {[analyzer.operator_ids[d] for d in dependents]}")

    print("\n[增量算法]")
    for i, algo in enumerate(result['incremental_algorithms'], 1):
        print(f"\n算法 {i}:")
        print(f"  类型: {algo['type']}")
        print(f"  Rule ID: {algo['rule_id']}")
        print(f"  目标算子 ID: {algo.get('target_operator_id', 'N/A')}")
        print(f"  Rule hint 算子: {algo['rule_operators']}")
        print(f"  完整 subplan: {algo['operators']}")
        print(f"  Root 算子: {algo['root_operator_id']}")

    # 验证
    print("\n[验证]")
    checks = []

    for algo in result['incremental_algorithms']:
        if algo['type'] == 'aggregate':
            operators = algo['operators']

            # 检查是否包含 Aggregate 算子
            has_aggregate = False
            aggregate_ids = []
            for op_id in operators:
                if op_id in ['104', '105', '1418']:  # Aggregate 算子
                    has_aggregate = True
                    aggregate_ids.append(op_id)

            if has_aggregate:
                checks.append(f"✅ subplan 包含 Aggregate 算子: {aggregate_ids}")
            else:
                checks.append(f"❌ subplan 不包含任何 Aggregate 算子")

            # 检查是否包含目标算子 1418
            if '1418' in operators:
                checks.append(f"✅ subplan 包含目标 Aggregate 1418")
            else:
                checks.append(f"❌ subplan 不包含目标 Aggregate 1418")

            # 检查是否包含所有相关算子
            expected = ['100', '101', '102', '103', '104', '105', '1418']
            missing = set(expected) - set(operators)
            if not missing:
                checks.append(f"✅ subplan 包含所有预期算子")
            else:
                checks.append(f"⚠️  subplan 缺少算子: {missing}")

    for check in checks:
        print(f"  {check}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_bidirectional_search()
