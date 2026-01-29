#!/usr/bin/env python3
"""Plan 导航器 - 提供结构化的 Plan 查询功能"""
import json
from typing import Dict, List, Optional, Any


class PlanNavigator:
    """用于结构化查询 Plan JSON 的工具类"""

    def __init__(self, plan: Dict):
        self.plan = plan
        self._plan_str_cache = None

    @property
    def plan_str(self) -> str:
        """缓存的 plan JSON 字符串"""
        if self._plan_str_cache is None:
            self._plan_str_cache = json.dumps(self.plan)
        return self._plan_str_cache

    def has_operator(self, operator_name: str) -> bool:
        """检查是否包含指定算子（大小写不敏感）"""
        plan_str_lower = self.plan_str.lower()
        operator_name_lower = operator_name.lower()
        return operator_name_lower in plan_str_lower

    def has_any_operator(self, operator_names: List[str]) -> bool:
        """检查是否包含任意一个指定算子"""
        return any(name in self.plan_str for name in operator_names)

    def has_all_operators(self, operator_names: List[str]) -> bool:
        """检查是否包含所有指定算子"""
        return all(name in self.plan_str for name in operator_names)

    def get_operators(self) -> List[Dict]:
        """获取所有算子"""
        return self.plan.get('operators', [])

    def find_operators_by_type(self, operator_type: str) -> List[Dict]:
        """根据类型查找算子"""
        operators = []
        for op in self.get_operators():
            if operator_type.lower() in json.dumps(op).lower():
                operators.append(op)
        return operators

    def has_hash_aggregate_phase(self, phase: str) -> bool:
        """
        检查是否有指定阶段的 HashAggregate
        phase: 'P1', 'PARTIAL1', 'P2', 'PARTIAL2', 'COMPLETE', 'FINAL' 等
        """
        for op in self.get_operators():
            if 'hashAgg' in op or 'HashAggregate' in json.dumps(op):
                op_str = json.dumps(op)
                if phase in op_str:
                    return True
        return False

    def has_aggregate_function(self, function_names: List[str]) -> bool:
        """检查是否包含指定的聚合函数"""
        for op in self.get_operators():
            if 'hashAgg' not in op:
                continue

            agg_calls = op.get('hashAgg', {}).get('aggregate', {}).get('aggregateCalls', [])
            for call in agg_calls:
                func_name = call.get('function', {}).get('function', {}).get('name', '')
                if any(fn in func_name for fn in function_names):
                    return True
        return False

    def extract_aggregate_bits(self) -> Optional[int]:
        """提取聚合函数的 bits 参数"""
        for op in self.get_operators():
            if 'hashAgg' not in op:
                continue

            agg_calls = op.get('hashAgg', {}).get('aggregate', {}).get('aggregateCalls', [])
            for call in agg_calls:
                func = call.get('function', {}).get('function', {})
                func_name = func.get('name', '')

                # 检查是否是 BF 相关函数
                if any(bf in func_name for bf in ['_DF_BF_COLLECT', 'BF_COLLECT', 'DF_BF_COLLECT']):
                    properties = func.get('properties', {}).get('properties', [])
                    for prop in properties:
                        if prop.get('key') == 'bits':
                            try:
                                return int(prop.get('value', 0))
                            except (ValueError, TypeError):
                                pass
        return None

    def get_table_sink_info(self) -> List[Dict]:
        """获取 TableSink 信息"""
        sinks = []
        for op in self.get_operators():
            if 'tableSink' in op or 'TableSink' in json.dumps(op):
                sinks.append(op)
        return sinks

    def is_delta_table_sink(self) -> bool:
        """
        检查是否是增量刷新的 TableSink
        判断逻辑（基于 table.path）：
        1. path 是 4 元组且最后一个元素是 __delta__ → 增量（写入 delta 文件）
        2. path 是 3 元组且 overwrite=false → 增量
        3. 其他情况（3 元组且 overwrite=true）→ 全量

        path 格式：
        - 3元组: [workspace, namespace, table_name]
        - 4元组: [workspace, namespace, table_name, __delta__]
        """
        for sink in self.get_table_sink_info():
            table_sink = sink.get('tableSink', {})

            # 获取 path（列表格式）
            table = table_sink.get('table', {})
            path = table.get('path', [])

            if not isinstance(path, list) or len(path) < 3:
                continue

            # 获取 overwrite 标志
            overwrite = table_sink.get('overwrite', True)
            if isinstance(overwrite, str):
                overwrite = overwrite.lower() == 'true'

            # 判断逻辑
            if len(path) == 4 and path[-1] == '__delta__':
                # 4元组且最后是 __delta__，表示写入 delta 文件，是增量
                return True
            elif len(path) == 3 and not overwrite:
                # 3元组且 overwrite=false，是增量
                return True

        # 其他情况是全量
        return False

    def is_overwrite_sink(self) -> bool:
        """检查是否是 OVERWRITE sink（overwrite=true）"""
        for sink in self.get_table_sink_info():
            table_sink = sink.get('tableSink', {})
            overwrite = table_sink.get('overwrite', True)
            if isinstance(overwrite, str):
                overwrite = overwrite.lower() == 'true'
            if overwrite:
                return True
        return False

    def get_refresh_table_name(self) -> Optional[str]:
        """
        获取 REFRESH 的表名（不过滤中间表，由调用方决定是否过滤）
        从 table.path 中提取表名：
        - 3元组: [workspace, namespace, table_name] -> table_name
        - 4元组: [workspace, namespace, table_name, __delta__] -> table_name
        """
        for sink in self.get_table_sink_info():
            table_sink = sink.get('tableSink', {})
            table = table_sink.get('table', {})
            path = table.get('path', [])

            if isinstance(path, list) and len(path) >= 3:
                # 3元组或4元组，table_name 在索引 2
                table_name = path[2]
                if table_name:
                    return table_name
        return None

    def get_table_full_path(self) -> Optional[str]:
        """获取表的完整路径（workspace.namespace.table_name）"""
        for sink in self.get_table_sink_info():
            table_sink = sink.get('tableSink', {})
            table = table_sink.get('table', {})
            path = table.get('path', [])

            if isinstance(path, list) and len(path) >= 3:
                # 返回 workspace.namespace.table_name
                return '.'.join(path[:3])
        return None

    def has_join_type(self, join_type: str) -> bool:
        """
        检查是否包含指定类型的 Join
        join_type: 'BroadcastHashJoin', 'HashJoin', 'ShuffleHashJoin' 等
        """
        return join_type in self.plan_str

    def get_join_operators(self) -> List[Dict]:
        """获取所有 Join 算子"""
        joins = []
        for op in self.get_operators():
            op_str = json.dumps(op)
            if 'join' in op_str.lower():
                joins.append(op)
        return joins

    def has_calc_with_udf(self) -> bool:
        """检查是否有包含 UDF 的 Calc 算子"""
        udf_patterns = ['udf', 'UDF', 'user_defined', 'custom_func', 'ScalarFunction']
        for op in self.get_operators():
            if 'calc' in json.dumps(op).lower():
                op_str = json.dumps(op)
                if any(pattern in op_str for pattern in udf_patterns):
                    return True
        return False

    def get_input_stages(self) -> List[str]:
        """获取当前 stage 的输入 stage ID 列表"""
        input_stages = []

        # 尝试从 plan 中提取 inputStages
        if 'inputStages' in self.plan:
            input_stages = self.plan.get('inputStages', [])
        elif 'inputs' in self.plan:
            inputs = self.plan.get('inputs', [])
            for inp in inputs:
                if isinstance(inp, dict) and 'stageId' in inp:
                    input_stages.append(inp['stageId'])
                elif isinstance(inp, str):
                    input_stages.append(inp)

        # 尝试从 operators 中提取
        if not input_stages:
            for op in self.get_operators():
                if 'exchange' in json.dumps(op).lower():
                    # Exchange 算子可能包含上游 stage 信息
                    exchange = op.get('exchange', {})
                    if 'inputStageId' in exchange:
                        input_stages.append(exchange['inputStageId'])

        return input_stages

    def has_scan_with_incremental_delete(self) -> bool:
        """检查是否有包含 __incremental_delete 列的 Scan"""
        return '__incremental_delete' in self.plan_str

    def has_row_number_pattern(self) -> bool:
        """检查是否包含 row_number=1 的模式"""
        patterns = ['row_number=1', 'rn=1', 'rowNumber=1', 'ROW_NUMBER=1']
        return any(pattern in self.plan_str for pattern in patterns)

    def extract_shuffle_bytes(self) -> int:
        """提取 shuffle 字节数（如果可用）"""
        # 这个需要从 profile 数据中提取，plan 中通常没有
        return 0

    def get_incremental_table_scans(self) -> List[Dict]:
        """
        获取所有 TableScan 的增量属性信息

        返回格式：
        [
            {
                'table_name': 'table1',
                'from_version': 28800,
                'to_version': 57600,
                'scan_type': 'delta' | 'snapshot_prev' | 'snapshot_current' | 'unknown'
            },
            ...
        ]
        """
        scans = []
        for op in self.get_operators():
            if 'tableScan' not in op:
                continue

            table_scan = op['tableScan']
            table_name = table_scan.get('table', {}).get('name', 'unknown')
            incr_property = table_scan.get('incrementalTableProperty', {})

            from_version = incr_property.get('from')
            to_version = incr_property.get('to')

            # 判断扫描类型
            scan_type = 'unknown'
            if from_version is not None and to_version is not None:
                # 有 from 和 to，表示 delta 数据
                scan_type = 'delta'
            elif from_version is None and to_version is not None:
                # 只有 to，需要判断是上个 snapshot 还是当前 snapshot
                # 这里简化处理，标记为 snapshot
                scan_type = 'snapshot'

            scans.append({
                'table_name': table_name,
                'from_version': from_version,
                'to_version': to_version,
                'scan_type': scan_type,
                'operator': op
            })

        return scans

    def has_delta_scan(self) -> bool:
        """检查是否有 delta 数据扫描"""
        scans = self.get_incremental_table_scans()
        return any(scan['scan_type'] == 'delta' for scan in scans)

    def get_delta_tables(self) -> List[str]:
        """获取所有读取 delta 数据的表名"""
        scans = self.get_incremental_table_scans()
        return [scan['table_name'] for scan in scans if scan['scan_type'] == 'delta']

    def get_snapshot_tables(self) -> List[str]:
        """获取所有读取 snapshot 数据的表名"""
        scans = self.get_incremental_table_scans()
        return [scan['table_name'] for scan in scans if scan['scan_type'] == 'snapshot']


def create_stage_navigator(stage_data: Dict) -> PlanNavigator:
    """为 stage_data 创建 PlanNavigator"""
    plan = stage_data.get('plan', {})
    return PlanNavigator(plan)
