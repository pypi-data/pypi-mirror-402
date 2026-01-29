#!/usr/bin/env python3
"""
规则基类 - 所有优化规则的抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseRule(ABC):
    """规则基类"""

    name: str = "base_rule"
    category: str = "unknown"
    description: str = ""
    rule_scope: str = "stage"  # 'stage' 或 'global'

    def __init__(self):
        self.context = {}

    @abstractmethod
    def check(self, stage_data: Dict, context: Dict) -> bool:
        """检查是否触发该规则"""
        pass

    @abstractmethod
    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        """分析问题并返回结果"""
        pass

    def get_setting(self, setting: str, context: Dict) -> Optional[str]:
        """获取参数值"""
        return context.get('settings', {}).get(setting)

    def has_setting(self, setting: str, context: Dict) -> bool:
        """检查参数是否已配置"""
        return setting in context.get('settings', {})

    def has_profile_data(self, context: Dict) -> bool:
        """检查是否有有效的 profile 数据"""
        return context.get('has_profile', False)

    def create_recommendation(self, setting: str, value: str, priority: int,
                            reason: str, impact: str = 'MEDIUM',
                            current_value: str = None, warning: str = None) -> Dict:
        """创建参数建议"""
        return {
            'rule': self.name, 'setting': setting, 'value': value,
            'priority': priority, 'reason': reason, 'impact': impact,
            'current_value': current_value, 'warning': warning,
        }

    def create_finding(self, finding_type: str, stage_id: str, severity: str,
                      description: str = "", details: Dict = None) -> Dict:
        """创建问题发现"""
        return {
            'rule': self.name, 'type': finding_type, 'stage_id': stage_id,
            'severity': severity, 'description': description, 'details': details or {},
        }

    def create_insight(self, message: str, stage_id: str = None) -> Dict:
        """创建洞察"""
        return {'rule': self.name, 'message': message, 'stage_id': stage_id}


class GlobalRule(BaseRule):
    """全局规则基类 - 不针对单个 Stage，而是针对整个 Job"""

    rule_scope: str = "global"

    def check(self, stage_data: Dict, context: Dict) -> bool:
        """全局规则不需要 stage_data，直接返回 True"""
        return True

    @abstractmethod
    def analyze_global(self, context: Dict) -> Dict:
        """全局分析方法"""
        pass

    def analyze(self, stage_data: Dict, context: Dict) -> Dict:
        """兼容接口，调用 analyze_global"""
        return self.analyze_global(context)

