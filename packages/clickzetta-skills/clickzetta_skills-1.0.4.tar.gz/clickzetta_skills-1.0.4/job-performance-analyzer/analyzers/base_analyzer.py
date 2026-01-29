#!/usr/bin/env python3
"""基础分析器"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from core.reporter import Reporter

class BaseAnalyzer(ABC):
    name: str = "base_analyzer"
    description: str = ""
    
    def __init__(self):
        self.rules = []
        self.reporter = Reporter()
        self.context = {}
    
    def set_context(self, context: Dict[str, Any]):
        self.context = context
    
    @abstractmethod
    def analyze(self, aligned_data: Dict) -> Dict:
        pass
    
    def run_rules_on_stage(self, stage_data: Dict) -> Dict:
        results = {'findings': [], 'recommendations': [], 'insights': []}
        for rule in self.rules:
            try:
                if rule.check(stage_data, self.context):
                    result = rule.analyze(stage_data, self.context)
                    results['findings'].extend(result.get('findings', []))
                    results['recommendations'].extend(result.get('recommendations', []))
                    results['insights'].extend(result.get('insights', []))
            except Exception as e:
                results['insights'].append({'rule': rule.name, 
                    'message': f"规则 {rule.name} 执行异常: {str(e)}", 'stage_id': stage_data.get('stage_id')})
        return results
    
    def get_report(self) -> Reporter:
        return self.reporter
