#!/usr/bin/env python3
"""测试目标算子识别"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.incremental_algorithm_analyzer import IncrementalAlgorithmAnalyzer


def test_target_operator_inclusion():
    """
    测试目标算子是否被正确包含在 subplan 中

    场景：Rule hint 在 Join 上，但指向 Aggregate#31766669
    期望：Aggregate#31766669 应该在 subplan 中
    """
    print("=" * 80)
    print("测试: 目标算子包含在 subplan 中")
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
            # 这个 Join 是为了计算 Aggregate#31766669 的辅助算子
            {
                'id': '102',
                'join': {
                    'hint': 'Rule:IncrementalAggPositiveDeltaDedupRule_cz::optimizer::LogicalAggregate#31766669'
                }
            },
            # Calc - 没有 hint (ID: 103)
            {
                'id': '103',
                'calc': {}
            },
            # HashAggregate - 目标算子，但没有 Rule hint (ID: 31766669)
            # 这是 Rule hint 中指向的目标算子
            {
                'id': '31766669',
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
        print(f"  索引 {idx} -> ID {op_id}")

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
            target_id = algo.get('target_operator_id')
            operators = algo['operators']
            rule_operators = algo['rule_operators']

            if target_id:
                checks.append(f"✅ 从 Rule ID 中提取到目标算子 ID: {target_id}")

                if target_id in operators:
                    checks.append(f"✅ 目标算子 {target_id} 已包含在 subplan 中")
                else:
                    checks.append(f"❌ 目标算子 {target_id} 未包含在 subplan 中")

                if target_id not in rule_operators:
                    checks.append(f"✅ 目标算子 {target_id} 不在 Rule hint 算子列表中（符合预期）")
                else:
                    checks.append(f"⚠️  目标算子 {target_id} 在 Rule hint 算子列表中")

            # 检查 subplan 是否包含所有相关算子
            expected_operators = ['100', '101', '102', '103', '31766669']
            missing = set(expected_operators) - set(operators)
            if not missing:
                checks.append(f"✅ subplan 包含所有预期的算子: {expected_operators}")
            else:
                checks.append(f"❌ subplan 缺少算子: {missing}")

    for check in checks:
        print(f"  {check}")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_target_operator_inclusion()
