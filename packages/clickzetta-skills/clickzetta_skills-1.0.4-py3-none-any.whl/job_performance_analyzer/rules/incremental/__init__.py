#!/usr/bin/env python3
"""增量计算规则模块"""
from rules.incremental.stage_optimization import (
    RefreshTypeDetection, SingleDopAggregate, HashJoinOptimization,
    TableSinkDop, MaxDopCheck, SpillingAnalysis, ActiveProblemFinding,
)
from rules.incremental.state_table import (
    NonIncrementalDiagnosis, RowNumberCheck, AppendOnlyScan,
    StateTableEnable, AggregateReuse, HeavyCalcState,
)

STAGE_OPTIMIZATION_RULES = [
    RefreshTypeDetection, SingleDopAggregate, HashJoinOptimization,
    TableSinkDop, MaxDopCheck, SpillingAnalysis, ActiveProblemFinding,
]
STATE_TABLE_RULES = [
    NonIncrementalDiagnosis, RowNumberCheck, AppendOnlyScan,
    StateTableEnable, AggregateReuse, HeavyCalcState,
]

__all__ = [
    'RefreshTypeDetection', 'SingleDopAggregate', 'HashJoinOptimization',
    'TableSinkDop', 'MaxDopCheck', 'SpillingAnalysis', 'ActiveProblemFinding',
    'NonIncrementalDiagnosis', 'RowNumberCheck', 'AppendOnlyScan',
    'StateTableEnable', 'AggregateReuse', 'HeavyCalcState',
    'STAGE_OPTIMIZATION_RULES', 'STATE_TABLE_RULES',
]
