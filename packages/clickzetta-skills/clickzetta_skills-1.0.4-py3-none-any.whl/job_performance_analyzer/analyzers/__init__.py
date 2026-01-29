#!/usr/bin/env python3
"""分析器模块"""
from analyzers.base_analyzer import BaseAnalyzer
from analyzers.incremental_analyzer import IncrementalAnalyzer

def get_analyzer(sql_type: str, vc_mode: str = 'GP', **kwargs):
    if sql_type == 'REFRESH':
        return IncrementalAnalyzer(**kwargs)
    return IncrementalAnalyzer(enable_state_table_rules=False, **kwargs)

__all__ = ['BaseAnalyzer', 'IncrementalAnalyzer', 'get_analyzer']
