#!/usr/bin/env python3
"""测试增量判断逻辑 - 使用真实的 path 结构"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils.plan_navigator import PlanNavigator


def test_incremental_detection_with_path():
    """测试增量/全量判断逻辑（基于 path）"""
    print("=" * 80)
    print("测试增量/全量判断逻辑（基于 table.path）")
    print("=" * 80)

    # 测试用例 1: 4元组 path，最后是 __delta__，应该是增量
    test_case_1 = {
        'operators': [{
            'tableSink': {
                'table': {
                    'path': ['gic_prod', 'kscdm', 'dim_ks_live_daily', '__delta__']
                },
                'overwrite': False
            }
        }]
    }
    nav1 = PlanNavigator(test_case_1)
    result1 = nav1.is_delta_table_sink()
    table_name1 = nav1.get_refresh_table_name()
    full_path1 = nav1.get_table_full_path()
    print(f"\n测试 1: 4元组 path，最后是 __delta__")
    print(f"  Path: ['gic_prod', 'kscdm', 'dim_ks_live_daily', '__delta__']")
    print(f"  表名: {table_name1}")
    print(f"  完整路径: {full_path1}")
    print(f"  结果: {'增量' if result1 else '全量'}")
    print(f"  预期: 增量")
    print(f"  {'✓ 通过' if result1 else '✗ 失败'}")

    # 测试用例 2: 3元组 path，overwrite=false，应该是增量
    test_case_2 = {
        'operators': [{
            'tableSink': {
                'table': {
                    'path': ['gic_prod', 'kscdm', 'dim_ks_live_daily']
                },
                'overwrite': False
            }
        }]
    }
    nav2 = PlanNavigator(test_case_2)
    result2 = nav2.is_delta_table_sink()
    table_name2 = nav2.get_refresh_table_name()
    full_path2 = nav2.get_table_full_path()
    print(f"\n测试 2: 3元组 path，overwrite=false")
    print(f"  Path: ['gic_prod', 'kscdm', 'dim_ks_live_daily']")
    print(f"  表名: {table_name2}")
    print(f"  完整路径: {full_path2}")
    print(f"  结果: {'增量' if result2 else '全量'}")
    print(f"  预期: 增量")
    print(f"  {'✓ 通过' if result2 else '✗ 失败'}")

    # 测试用例 3: 3元组 path，overwrite=true，应该是全量
    test_case_3 = {
        'operators': [{
            'tableSink': {
                'table': {
                    'path': ['gic_prod', 'kscdm', 'dim_ks_live_daily']
                },
                'overwrite': True
            }
        }]
    }
    nav3 = PlanNavigator(test_case_3)
    result3 = nav3.is_delta_table_sink()
    table_name3 = nav3.get_refresh_table_name()
    full_path3 = nav3.get_table_full_path()
    print(f"\n测试 3: 3元组 path，overwrite=true")
    print(f"  Path: ['gic_prod', 'kscdm', 'dim_ks_live_daily']")
    print(f"  表名: {table_name3}")
    print(f"  完整路径: {full_path3}")
    print(f"  结果: {'增量' if result3 else '全量'}")
    print(f"  预期: 全量")
    print(f"  {'✓ 通过' if not result3 else '✗ 失败'}")

    # 测试用例 4: 中间表（table_name 包含 __incr__）
    test_case_4 = {
        'operators': [{
            'tableSink': {
                'table': {
                    'path': ['gic_prod', 'kscdm', '2502726411993855340__incr__1266109515_202601080100011337ywpqgvvw6ek_4721998']
                },
                'overwrite': False
            }
        }]
    }
    nav4 = PlanNavigator(test_case_4)
    table_name4 = nav4.get_refresh_table_name()
    print(f"\n测试 4: 中间表识别")
    print(f"  Path: ['gic_prod', 'kscdm', '2502726411993855340__incr__...']")
    print(f"  表名: {table_name4}")
    print(f"  是否包含 __incr__: {'__incr__' in table_name4 if table_name4 else False}")
    print(f"  预期: 应该被识别为中间表")
    print(f"  {'✓ 通过' if table_name4 and '__incr__' in table_name4 else '✗ 失败'}")

    # 测试用例 5: 中间表的 delta 写入（4元组，table_name 包含 __incr__）
    test_case_5 = {
        'operators': [{
            'tableSink': {
                'table': {
                    'path': ['gic_prod', 'kscdm', '2502726411993855340__incr__1266109515_202601080100011337ywpqgvvw6ek_4721998', '__delta__']
                },
                'overwrite': False
            }
        }]
    }
    nav5 = PlanNavigator(test_case_5)
    result5 = nav5.is_delta_table_sink()
    table_name5 = nav5.get_refresh_table_name()
    print(f"\n测试 5: 中间表的 delta 写入")
    print(f"  Path: ['gic_prod', 'kscdm', '...incr...', '__delta__']")
    print(f"  表名: {table_name5}")
    print(f"  是否包含 __incr__: {'__incr__' in table_name5 if table_name5 else False}")
    print(f"  判断结果: {'增量' if result5 else '全量'}")
    print(f"  预期: 增量（但应该被过滤为中间表）")
    print(f"  {'✓ 通过' if result5 and table_name5 and '__incr__' in table_name5 else '✗ 失败'}")

    print("\n" + "=" * 80)
    all_passed = (result1 and result2 and not result3 and
                  table_name4 and '__incr__' in table_name4 and
                  result5 and table_name5 and '__incr__' in table_name5)
    if all_passed:
        print("✓ 所有测试通过！")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(test_incremental_detection_with_path())
