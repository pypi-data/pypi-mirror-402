#!/usr/bin/env python3
"""测试脚本 - 验证所有改进"""
import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def test_imports():
    """测试所有模块导入"""
    print("测试 1: 模块导入")
    try:
        from core.parser import PlanProfileParser
        from core.aligner import StageAligner
        from utils.plan_navigator import PlanNavigator, create_stage_navigator
        from rules.base_rule import BaseRule, GlobalRule
        from rules.incremental.stage_optimization import (
            RefreshTypeDetection, SingleDopAggregate, HashJoinOptimization,
            TableSinkDop, MaxDopCheck, SpillingAnalysis, ActiveProblemFinding,
        )
        from rules.incremental.state_table import (
            NonIncrementalDiagnosis, RowNumberCheck, AppendOnlyScan,
            StateTableEnable, AggregateReuse, HeavyCalcState,
        )
        from analyzers.incremental_analyzer import IncrementalAnalyzer
        print("  ✓ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"  ✗ 导入失败: {str(e)}")
        return False


def test_plan_navigator():
    """测试 PlanNavigator"""
    print("\n测试 2: PlanNavigator 功能")
    try:
        from utils.plan_navigator import PlanNavigator

        # 创建测试 plan
        test_plan = {
            'operators': [
                {'hashAgg': {'aggregate': {'aggregateCalls': []}}},
                {'tableSink': {'table': {'tableName': 'test_table'}}}
            ]
        }

        nav = PlanNavigator(test_plan)

        # 测试基本功能
        assert nav.has_operator('hashAgg'), "应该检测到 hashAgg"
        assert nav.has_operator('TableSink'), "应该检测到 TableSink"
        assert not nav.has_operator('NonExistent'), "不应该检测到不存在的算子"

        print("  ✓ PlanNavigator 基本功能正常")
        return True
    except Exception as e:
        print(f"  ✗ PlanNavigator 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_global_rule():
    """测试 GlobalRule"""
    print("\n测试 3: GlobalRule 功能")
    try:
        from rules.base_rule import GlobalRule

        class TestGlobalRule(GlobalRule):
            name = "test_global"
            category = "test"
            description = "测试全局规则"

            def analyze_global(self, context):
                return {'findings': [], 'recommendations': [], 'insights': []}

        rule = TestGlobalRule()
        assert rule.rule_scope == "global", "rule_scope 应该是 global"

        result = rule.analyze_global({})
        assert 'findings' in result, "结果应该包含 findings"

        print("  ✓ GlobalRule 功能正常")
        return True
    except Exception as e:
        print(f"  ✗ GlobalRule 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_stage_dependencies():
    """测试 Stage 依赖关系解析"""
    print("\n测试 4: Stage 依赖关系解析")
    try:
        from core.aligner import StageAligner

        # 创建测试数据
        parsed_data = {
            'plan_stages': {
                'stage1': {'operators': [], 'inputStages': []},
                'stage2': {'operators': [], 'inputStages': ['stage1']},
            },
            'profile_stages': {
                'stage1': {
                    'taskCountDetail': {'1': '4'},
                    'startTime': 0,
                    'endTime': 1000,
                    'inputOutputStats': {}
                },
                'stage2': {
                    'taskCountDetail': {'1': '2'},
                    'startTime': 1000,
                    'endTime': 2000,
                    'inputOutputStats': {}
                },
            }
        }

        aligner = StageAligner(parsed_data)
        result = aligner.align()

        assert 'stage_dependencies' in result, "结果应该包含 stage_dependencies"
        assert 'stage2' in result['stage_dependencies'], "应该解析出 stage2 的依赖"

        upstream = aligner.get_upstream_stages('stage2')
        assert 'stage1' in upstream, "stage2 的上游应该包含 stage1"

        print("  ✓ Stage 依赖关系解析正常")
        return True
    except Exception as e:
        print(f"  ✗ Stage 依赖关系测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """测试错误处理"""
    print("\n测试 5: 错误处理")
    try:
        from core.parser import PlanProfileParser

        # 测试文件不存在
        try:
            parser = PlanProfileParser('/nonexistent/plan.json', '/nonexistent/profile.json')
            print("  ✗ 应该抛出 FileNotFoundError")
            return False
        except FileNotFoundError as e:
            print(f"  ✓ 正确捕获文件不存在错误: {str(e)[:50]}...")

        return True
    except Exception as e:
        print(f"  ✗ 错误处理测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("Job Performance Analyzer - 改进测试")
    print("=" * 80)

    tests = [
        test_imports,
        test_plan_navigator,
        test_global_rule,
        test_stage_dependencies,
        test_error_handling,
    ]

    passed = 0
    failed = 0

    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 80)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 80)

    if failed == 0:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print(f"\n✗ {failed} 个测试失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
