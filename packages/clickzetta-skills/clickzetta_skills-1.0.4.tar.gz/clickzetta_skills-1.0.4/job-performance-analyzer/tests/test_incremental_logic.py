#!/usr/bin/env python3
"""测试增量判断逻辑"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils.plan_navigator import PlanNavigator


def test_incremental_detection():
    """测试增量/全量判断逻辑"""
    print("=" * 80)
    print("测试增量/全量判断逻辑")
    print("=" * 80)

    # 测试用例 1: 表名包含 __delta__，应该是增量
    test_case_1 = {
        'operators': [{
            'tableSink': {
                'table': {'tableName': 'my_table__delta__'},
                'overwrite': True
            }
        }]
    }
    nav1 = PlanNavigator(test_case_1)
    result1 = nav1.is_delta_table_sink()
    print(f"\n测试 1: 表名包含 __delta__ (overwrite=true)")
    print(f"  表名: my_table__delta__")
    print(f"  结果: {'增量' if result1 else '全量'}")
    print(f"  预期: 增量")
    print(f"  {'✓ 通过' if result1 else '✗ 失败'}")

    # 测试用例 2: 表名不含 __delta__，overwrite=false，应该是增量
    test_case_2 = {
        'operators': [{
            'tableSink': {
                'table': {'tableName': 'my_table'},
                'overwrite': False
            }
        }]
    }
    nav2 = PlanNavigator(test_case_2)
    result2 = nav2.is_delta_table_sink()
    print(f"\n测试 2: 表名不含 __delta__ (overwrite=false)")
    print(f"  表名: my_table")
    print(f"  结果: {'增量' if result2 else '全量'}")
    print(f"  预期: 增量")
    print(f"  {'✓ 通过' if result2 else '✗ 失败'}")

    # 测试用例 3: 表名不含 __delta__，overwrite=true，应该是全量
    test_case_3 = {
        'operators': [{
            'tableSink': {
                'table': {'tableName': 'my_table'},
                'overwrite': True
            }
        }]
    }
    nav3 = PlanNavigator(test_case_3)
    result3 = nav3.is_delta_table_sink()
    print(f"\n测试 3: 表名不含 __delta__ (overwrite=true)")
    print(f"  表名: my_table")
    print(f"  结果: {'增量' if result3 else '全量'}")
    print(f"  预期: 全量")
    print(f"  {'✓ 通过' if not result3 else '✗ 失败'}")

    # 测试用例 4: overwrite 是字符串 "false"
    test_case_4 = {
        'operators': [{
            'tableSink': {
                'table': {'tableName': 'my_table'},
                'overwrite': 'false'
            }
        }]
    }
    nav4 = PlanNavigator(test_case_4)
    result4 = nav4.is_delta_table_sink()
    print(f"\n测试 4: overwrite 是字符串 'false'")
    print(f"  表名: my_table")
    print(f"  结果: {'增量' if result4 else '全量'}")
    print(f"  预期: 增量")
    print(f"  {'✓ 通过' if result4 else '✗ 失败'}")

    # 测试用例 5: 中间表（包含 __incr__）
    test_case_5 = {
        'operators': [{
            'tableSink': {
                'table': {'tableName': 'my_table__incr__state'},
                'overwrite': True
            }
        }]
    }
    nav5 = PlanNavigator(test_case_5)
    table_name = nav5.get_refresh_table_name()
    print(f"\n测试 5: 中间表识别")
    print(f"  表名: {table_name}")
    print(f"  是否包含 __incr__: {'__incr__' in table_name if table_name else False}")
    print(f"  预期: 应该被识别为中间表")

    print("\n" + "=" * 80)
    all_passed = result1 and result2 and not result3 and result4
    if all_passed:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(test_incremental_detection())
