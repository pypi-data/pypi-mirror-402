#!/usr/bin/env python3
"""增量算法分析器 - 识别增量算法和 delta/snapshot 传播"""
import json
import re
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum


class DataType(Enum):
    """数据类型：Delta 或 Snapshot"""
    DELTA = "delta"
    SNAPSHOT = "snapshot"
    UNKNOWN = "unknown"


class IncrementalAlgorithmAnalyzer:
    """
    增量算法分析器

    根据 prompt 4.2.1 的要求实现增量算法识别：

    4.2.1.1 识别所有 operator 是 delta 还是 snapshot
      - 识别 TableScan 的数据类型（delta/snapshot）
      - 传播数据类型（一元算子、Join、Union 规则）

    4.2.1.2 识别不同算子的增量算法
      - 解析 Rule hints（如 Rule:IncrementalJoinWithoutCondenseRule_xxx#ID）
      - 识别增量算法类型（aggregate/join/window）
      - 区分真正的 join/aggregate/window 增量算子和算法的一部分

    4.2.1.3 算子增量算法对应的 subplan
      - 找到一个增量算法对应的所有算子（不仅仅是有 Rule hint 的算子）
      - 包括整个执行路径上的所有算子
      - 识别算子对应的 root 阶段
      - 使用 plan.json 的 "id" 字段（实际 ID，不是数组索引）

    4.2.1.4 展示增量算法以及状态图
      - 生成增量算法依赖关系图
      - 画出算子的依赖关系
    """

    def __init__(self, plan: Dict):
        self.plan = plan
        self.operators = plan.get('operators', [])

        # 算子 ID 映射：operator_index -> actual_operator_id (from plan.json)
        self.operator_ids: Dict[int, str] = {}
        # 反向映射：actual_operator_id -> operator_index
        self.id_to_index: Dict[str, int] = {}
        self._extract_operator_ids()

        # 算子数据类型映射：operator_index -> DataType
        self.operator_data_types: Dict[int, DataType] = {}

        # Rule hint 映射：rule_id -> [operator_indices]
        self.rule_groups: Dict[str, List[int]] = {}

        # 算子依赖关系：operator_index -> [input_operator_indices]
        self.operator_dependencies: Dict[int, List[int]] = {}
        # 反向依赖：operator_index -> [output_operator_indices]（谁依赖我）
        self.operator_dependents: Dict[int, List[int]] = {}

    def _extract_operator_ids(self):
        """
        从算子对象中提取实际的 operator ID

        根据用户补充：
        - "在 plan.json 里找到所有 operator 对应的 Id"
        - "这里的 ID 不是代码中那些 index 下标"

        需要从 plan.json 的算子对象中找到实际的 id 字段
        """
        for idx, op in enumerate(self.operators):
            # 尝试从算子对象中提取实际的 ID
            op_id = self._extract_id_from_operator(op)

            if op_id:
                self.operator_ids[idx] = op_id
                self.id_to_index[op_id] = idx
            else:
                # 如果没有找到 ID，生成一个唯一标识
                # 但这不应该是常态，plan.json 中的算子应该都有 id
                self.operator_ids[idx] = f"unknown_op_{idx}"
                self.id_to_index[f"unknown_op_{idx}"] = idx

    def _extract_id_from_operator(self, op: Dict) -> Optional[str]:
        """
        从算子对象中提取实际的 ID

        plan.json 中算子的 id 字段可能在不同位置：
        1. 直接在算子对象的顶层：{"id": "12345", "tableScan": {...}}
        2. 在算子类型的子对象中：{"tableScan": {"id": "12345", ...}}
        """
        # 方法1: 直接从顶层获取
        if 'id' in op:
            return str(op['id'])

        # 方法2: 从算子类型的子对象中获取
        # 常见的算子类型：tableScan, join, hashAgg, calc, filter, project, union, etc.
        for key, value in op.items():
            if isinstance(value, dict) and 'id' in value:
                return str(value['id'])

        # 方法3: 递归查找（最多两层）
        for key, value in op.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key == 'id':
                        return str(sub_value)

        return None

    def analyze(self) -> Dict:
        """
        执行完整的增量算法分析

        实现 prompt 4.2.1.1-4.2.1.4 的完整流程

        Returns:
            {
                'operator_data_types': {op_id: 'delta'/'snapshot'/'unknown'},  # 使用实际 ID
                'rule_groups': {rule_id: [op_ids]},                             # 使用实际 ID
                'incremental_algorithms': [
                    {
                        'type': 'aggregate'/'join'/'window',
                        'rule_id': 'xxx',
                        'operators': [op_ids],           # 完整 subplan 的所有算子 ID
                        'rule_operators': [op_ids],      # 仅有 Rule hint 的算子 ID
                        'is_original_sql': True/False,
                        'root_operator_id': 'xxx'
                    }
                ],
                'algorithm_dependencies': {rule_id: [dependent_rule_ids]},
                'dependency_graph': 'text visualization',
                'validation_warnings': [...]  # 验证警告信息
            }
        """
        # 4.2.1.1 步骤 1: 识别 TableScan 的数据类型（delta/snapshot）
        self._identify_scan_data_types()

        # 4.2.1.2 步骤 2: 解析 Rule hints，识别增量算法
        self._parse_rule_hints()

        # 4.2.1.3 步骤 3: 构建算子依赖关系
        self._build_operator_dependencies()

        # 4.2.1.1 步骤 4: 传播数据类型
        self._propagate_data_types()

        # 4.2.1.2 & 4.2.1.3 步骤 5: 识别增量算法及其完整 subplan
        algorithms = self._identify_incremental_algorithms_with_subplan()

        # 4.2.1.3 步骤 6: 构建算法依赖关系
        algo_deps = self._build_algorithm_dependencies(algorithms)

        # 4.2.1.4 步骤 7: 生成依赖关系图
        dep_graph = self._generate_dependency_graph(algorithms, algo_deps)

        # 新增步骤 8: 验证增量算法的正确性（根据 prompt 4.2.1.3 第 59 行的要求）
        validation_warnings = self._validate_algorithms(algorithms)

        return {
            'operator_data_types': {
                self.operator_ids[idx]: dt.value
                for idx, dt in self.operator_data_types.items()
            },
            'rule_groups': {
                rule_id: [self.operator_ids[idx] for idx in indices]
                for rule_id, indices in self.rule_groups.items()
            },
            'incremental_algorithms': algorithms,
            'algorithm_dependencies': algo_deps,
            'dependency_graph': dep_graph,
            'validation_warnings': validation_warnings
        }

    def _identify_scan_data_types(self):
        """
        识别 TableScan 的数据类型（delta 或 snapshot）

        根据 original_prompt.md 第 49 行的修改：
        - **Delta 数据**：只有当 from 和 to 都是非 MIN_LONG 值时（如 from=28800, to=57600）
        - **Snapshot 数据**：from=-9223372036854775808（MIN_LONG）是明显特征

        示例：
        1. Delta: {"from": "28800", "to": "57600"} → delta
        2. Snapshot (上个状态): {"from": "-9223372036854775808", "to": "28800"} → snapshot
        3. Snapshot (当前状态): {"from": "-9223372036854775808", "to": "57600"} → snapshot
        """
        # MIN_LONG 常量（Java Long.MIN_VALUE）
        MIN_LONG = -9223372036854775808

        for idx, op in enumerate(self.operators):
            if 'tableScan' not in op:
                continue

            table_scan = op['tableScan']
            incr_property = table_scan.get('incrementalTableProperty', {})

            from_version = incr_property.get('from')
            to_version = incr_property.get('to')

            # 如果没有增量属性，可能是普通表
            if from_version is None and to_version is None:
                self.operator_data_types[idx] = DataType.UNKNOWN
                continue

            # 转换为整数进行比较（可能是字符串格式）
            try:
                from_val = int(from_version) if from_version is not None else None
                to_val = int(to_version) if to_version is not None else None
            except (ValueError, TypeError):
                # 无法转换，标记为 UNKNOWN
                self.operator_data_types[idx] = DataType.UNKNOWN
                continue

            # 判断逻辑：
            # 1. 如果 from 是 MIN_LONG，则是 snapshot（无论 to 是什么）
            # 2. 如果 from 和 to 都不是 MIN_LONG，则是 delta
            # 3. 其他情况标记为 UNKNOWN

            if from_val is not None and from_val == MIN_LONG:
                # from 是 MIN_LONG，表示 snapshot
                self.operator_data_types[idx] = DataType.SNAPSHOT
            elif from_val is not None and to_val is not None and from_val != MIN_LONG and to_val != MIN_LONG:
                # from 和 to 都不是 MIN_LONG，表示 delta
                self.operator_data_types[idx] = DataType.DELTA
            else:
                # 其他情况（如只有 to，或 from/to 值异常）
                self.operator_data_types[idx] = DataType.UNKNOWN

    def _parse_rule_hints(self):
        """
        解析 Rule hints

        格式示例：
        - Rule:IncrementalLinearFunctionAggregateRule
        - Rule:IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766417_Delta:L_Snapshot:R

        注意：
        1. 同一个算子（如 #31766417）可能有多个变体，都应该归为一个算法
        2. 根据 prompt original_prompt.md 第 58 行，如果是 deleteplan 相关 hint，则忽略不属于增量算法
           - DeletePlan 相关的 hint 用于表示删除数据的 plan，不属于任何增量算法
           - 测试数据格式：Rule:DeletePlan-delta-join(left)_Delta:L_Snapshot:R
        """
        #打印operator个数
        # print("" + str(len(self.operators)) + "个算子")
        for idx, op in enumerate(self.operators):
            op_str = json.dumps(op)

            # 打印op str
            # print(op_str + " id: " + str(idx) + "\n")

            # 查找 Rule: 模式（扩展正则以支持 - 和 () 符号）
            # 需要匹配如：Rule:DeletePlan-delta-join(left)_Delta:L_Snapshot:R
            rule_pattern = r'Rule:([A-Za-z0-9_:#,\-()]+)'
            matches = re.findall(rule_pattern, op_str)

            for rule_name in matches:
                # ⚠️ 过滤 DeletePlan 相关的 hint
                # 根据 prompt original_prompt.md 第 58 行：
                # "如果是deleteplan相关hint，则忽略不属于增量算法"
                #
                # 测试数据中的格式：Rule:DeletePlan-delta-join(left)_Delta:L_Snapshot:R
                # 需要同时匹配大小写和不同的分隔符格式
                if 'deleteplan' in rule_name.lower() or 'delete_plan' in rule_name.lower():
                    continue

                # 提取基础 rule ID（去除变体后缀）
                base_rule_id = self._extract_base_rule_id(rule_name)

                if base_rule_id not in self.rule_groups:
                    self.rule_groups[base_rule_id] = []
                self.rule_groups[base_rule_id].append(idx)

        # 打印调试信息，打印所有base_rule_id和对应的所有operator信息
        # for base_rule_id in self.rule_groups.keys():
        #     print(f'base_rule_id: {base_rule_id}')
        #     print(f'operators: {self.rule_groups[base_rule_id]}')

    def _extract_base_rule_id(self, rule_name: str) -> str:
        """
        提取基础 rule ID，去除变体后缀

        例如：
        - IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766417_Delta:L_Snapshot:R
          -> IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766417
        """
        if '#' in rule_name:
            match = re.match(r'(.+#\d+)(?:_Delta:|_Snapshot:|$)', rule_name)
            if match:
                return match.group(1)
            return rule_name
        else:
            match = re.match(r'(.+?)(?:_Delta:|_Snapshot:|$)', rule_name)
            if match and match.group(1):
                return match.group(1)
            return rule_name

    def _build_operator_dependencies(self):
        """
        构建算子依赖关系

        根据 prompt 4.2.1.3：需要识别算子之间的依赖关系
        """
        for idx in range(len(self.operators)):
            self.operator_dependencies[idx] = []
            self.operator_dependents[idx] = []

        # 尝试从算子中提取输入依赖
        for idx, op in enumerate(self.operators):
            inputs = self._extract_operator_inputs(op, idx)
            self.operator_dependencies[idx] = inputs

            # 构建反向依赖
            for input_idx in inputs:
                if 0 <= input_idx < len(self.operators):
                    self.operator_dependents[input_idx].append(idx)

    def _extract_operator_inputs(self, op: Dict, current_idx: int) -> List[int]:
        """
        提取算子的输入依赖

        从 plan.json 的 inputIds 字段提取真实的依赖关系。
        这支持跨 stage 的依赖追踪（例如通过 ShuffleRead/ShuffleWrite 连接）。

        实现逻辑：
        1. 优先使用 inputIds 字段（真实的依赖关系）
        2. inputIds 中的算子 ID 需要映射到索引
        3. 如果没有 inputIds，回退到启发式方法（向后兼容测试）
        """
        inputs = []

        # 方法1：使用 inputIds 字段（推荐，支持跨 stage）
        if 'inputIds' in op:
            input_ids = op['inputIds']
            if isinstance(input_ids, list):
                for input_id in input_ids:
                    if isinstance(input_id, str) and input_id in self.id_to_index:
                        inputs.append(self.id_to_index[input_id])
                return inputs

        # 方法2：回退到启发式方法（用于测试和简单场景）
        # 假设算子按拓扑顺序排列
        op_str = json.dumps(op).lower()
        if 'join' in op_str and current_idx >= 2:
            # Join 依赖前面两个算子
            inputs = [current_idx - 2, current_idx - 1]
        elif current_idx > 0:
            # 其他算子依赖前一个算子
            inputs = [current_idx - 1]

        return inputs

    def _propagate_data_types(self):
        """
        根据算子类型传播数据类型

        根据 prompt 4.2.1.1 的规则：
        - 一元算子：输入 delta → 输出 delta；输入 snapshot → 输出 snapshot
        - Join：只有 left 和 right 都是 snapshot，结果才是 snapshot
        - Union：所有输入都是 snapshot → 输出 snapshot；所有输入都是 delta → 输出 delta
        """
        max_iterations = 10
        for iteration in range(max_iterations):
            changed = False

            for idx, op in enumerate(self.operators):
                if idx in self.operator_data_types:
                    continue

                input_indices = self.operator_dependencies.get(idx, [])
                input_types = []
                for input_idx in input_indices:
                    if input_idx in self.operator_data_types:
                        input_types.append(self.operator_data_types[input_idx])

                if not input_types or len(input_types) < len(input_indices):
                    continue

                op_type = self._get_operator_type(op)
                output_type = self._infer_output_type(op_type, input_types)

                if output_type != DataType.UNKNOWN:
                    self.operator_data_types[idx] = output_type
                    changed = True

            if not changed:
                break

    def _infer_output_type(self, op_type: str, input_types: List[DataType]) -> DataType:
        """根据算子类型和输入类型推导输出类型"""
        if not input_types:
            return DataType.UNKNOWN

        if op_type == 'join':
            if all(dt == DataType.SNAPSHOT for dt in input_types):
                return DataType.SNAPSHOT
            else:
                return DataType.DELTA
        elif op_type == 'union':
            if all(dt == DataType.SNAPSHOT for dt in input_types):
                return DataType.SNAPSHOT
            elif all(dt == DataType.DELTA for dt in input_types):
                return DataType.DELTA
            else:
                return DataType.SNAPSHOT
        else:
            return input_types[0] if input_types else DataType.UNKNOWN

    def _get_aggregate_mode(self, op: Dict) -> Optional[str]:
        """
        提取 Aggregate 算子的模式（P1/P2/Final/Complete等）

        Returns:
            模式字符串，如 'Final', 'P1', 'P2', 'Complete' 等
            如果不是 Aggregate 或无法提取模式，返回 None
        """
        # 检查 hashAgg 字段
        if 'hashAgg' in op and isinstance(op['hashAgg'], dict):
            hash_agg = op['hashAgg']

            # 方法1: 检查 hashAgg.stage 字段（顶层 stage）
            stage = hash_agg.get('stage')
            if stage:
                return str(stage)

            # 方法2: 检查 hashAgg.aggregate.aggregateCalls[].stage 字段
            # 这是实际存储 stage 信息的地方
            if 'aggregate' in hash_agg and isinstance(hash_agg['aggregate'], dict):
                aggregate = hash_agg['aggregate']
                if 'aggregateCalls' in aggregate and isinstance(aggregate['aggregateCalls'], list):
                    calls = aggregate['aggregateCalls']
                    if calls and len(calls) > 0:
                        # 取第一个 aggregateCall 的 stage
                        first_call = calls[0]
                        if isinstance(first_call, dict) and 'stage' in first_call:
                            return str(first_call['stage'])

            # 方法3: 回退到 mode 字段（兼容旧格式）
            mode = hash_agg.get('mode')
            if mode:
                return str(mode)

        # 检查 hashAggregate 字段（可能的别名）
        if 'hashAggregate' in op and isinstance(op['hashAggregate'], dict):
            hash_aggregate = op['hashAggregate']

            # 同样的逻辑
            stage = hash_aggregate.get('stage')
            if stage:
                return str(stage)

            if 'aggregate' in hash_aggregate and isinstance(hash_aggregate['aggregate'], dict):
                aggregate = hash_aggregate['aggregate']
                if 'aggregateCalls' in aggregate and isinstance(aggregate['aggregateCalls'], list):
                    calls = aggregate['aggregateCalls']
                    if calls and len(calls) > 0:
                        first_call = calls[0]
                        if isinstance(first_call, dict) and 'stage' in first_call:
                            return str(first_call['stage'])

            mode = hash_aggregate.get('mode')
            if mode:
                return str(mode)

        return None

    def _get_aggregate_functions(self, op: Dict) -> List[str]:
        """
        提取 Aggregate 算子的聚集函数名称列表

        Args:
            op: 算子对象

        Returns:
            聚集函数名称列表，如 ['SUM', 'COUNT', 'MULTI_RANGE_COLLECT']
        """
        functions = []

        # 检查 hashAgg 字段
        if 'hashAgg' in op and isinstance(op['hashAgg'], dict):
            hash_agg = op['hashAgg']
            if 'aggregate' in hash_agg and isinstance(hash_agg['aggregate'], dict):
                aggregate = hash_agg['aggregate']
                if 'aggregateCalls' in aggregate and isinstance(aggregate['aggregateCalls'], list):
                    for call in aggregate['aggregateCalls']:
                        if isinstance(call, dict) and 'function' in call:
                            func_obj = call['function']
                            # 可能的结构：function.function.name 或 function.name
                            if isinstance(func_obj, dict):
                                if 'function' in func_obj and isinstance(func_obj['function'], dict):
                                    func_name = func_obj['function'].get('name')
                                    if func_name:
                                        functions.append(str(func_name))
                                elif 'name' in func_obj:
                                    func_name = func_obj.get('name')
                                    if func_name:
                                        functions.append(str(func_name))

        # 检查 hashAggregate 字段（可能的别名）
        if 'hashAggregate' in op and isinstance(op['hashAggregate'], dict):
            hash_aggregate = op['hashAggregate']
            if 'aggregate' in hash_aggregate and isinstance(hash_aggregate['aggregate'], dict):
                aggregate = hash_aggregate['aggregate']
                if 'aggregateCalls' in aggregate and isinstance(aggregate['aggregateCalls'], list):
                    for call in aggregate['aggregateCalls']:
                        if isinstance(call, dict) and 'function' in call:
                            func_obj = call['function']
                            if isinstance(func_obj, dict):
                                if 'function' in func_obj and isinstance(func_obj['function'], dict):
                                    func_name = func_obj['function'].get('name')
                                    if func_name:
                                        functions.append(str(func_name))
                                elif 'name' in func_obj:
                                    func_name = func_obj.get('name')
                                    if func_name:
                                        functions.append(str(func_name))

        return functions

    def _get_operator_type(self, op: Dict) -> str:
        """
        获取算子类型

        根据 plan.json 中算子对象的键名来判断类型，而不是通过 json.dumps 查找关键字。
        plan.json 中的算子结构通常是：{"算子类型": {...算子详情...}}

        常见的算子类型键名：
        - tableScan, TableScan: 表扫描
        - join, hashJoin, nestedLoopJoin, broadcastHashJoin: Join 算子
        - hashAgg, hashAggregate: Aggregate 算子
        - calc, Calc: Calc 算子
        - filter, Filter: Filter 算子
        - project, Project: Project 算子
        - union, Union, unionAll: Union 算子
        - window, Window: Window 算子
        - exchange, Exchange: Exchange 算子
        - sort, Sort: Sort 算子
        """
        # 遍历算子对象的顶层键，查找算子类型
        for key in op.keys():
            key_lower = key.lower()

            # Join 类型（包括各种 join 变体）
            if 'join' in key_lower:
                return 'join'

            # Aggregate 类型
            elif 'agg' in key_lower or 'aggregate' in key_lower:
                return 'aggregate'

            # Calc 类型
            elif key_lower == 'calc':
                return 'calc'

            # Filter 类型
            elif key_lower == 'filter':
                return 'filter'

            # Project 类型
            elif key_lower == 'project':
                return 'project'

            # Union 类型
            elif 'union' in key_lower:
                return 'union'

            # Window 类型
            elif key_lower == 'window':
                return 'window'

            # TableScan 类型
            elif 'tablescan' in key_lower or 'scan' in key_lower:
                return 'tablescan'

            # Exchange 类型
            elif 'exchange' in key_lower:
                return 'exchange'

            # Sort 类型
            elif key_lower == 'sort':
                return 'sort'

        # 如果没有匹配到，返回 unknown
        return 'unknown'

    def _identify_incremental_algorithms_with_subplan(self) -> List[Dict]:
        """
        识别增量算法及其完整 subplan

        根据 prompt 4.2.1.2 和 4.2.1.3 的要求：
        - 通过 Rule hints 识别增量算法
        - 找到每个算法的完整 subplan（包括没有 hint 的算子）
        - 使用严格的边界检测，避免跨算法包含

        Returns:
            增量算法列表，每个算法包含完整的 subplan
        """
        algorithms = []

        # 预先构建所有算子的 hint 归属映射
        operator_hint_map = {}
        for rule_id, indices in self.rule_groups.items():
            for idx in indices:
                operator_hint_map[idx] = rule_id

        # 按照拓扑顺序处理算法（从上游到下游）
        sorted_rule_groups = self._sort_rule_groups_by_topology()

        # 记录已经被分配给某个算法的算子
        assigned_operators = {}

        for rule_id, rule_op_indices in sorted_rule_groups:
            # 识别算法类型
            algo_type = self._identify_algorithm_type(rule_id)

            # 找到目标算子
            target_op_idx = self._find_target_operator(rule_id, rule_op_indices)

            # 构建起始点列表
            start_indices = list(rule_op_indices)
            if target_op_idx is not None and target_op_idx not in start_indices:
                start_indices.append(target_op_idx)

            # 打印 start_indices
            # print(f"Start indices for rule {rule_id}: {start_indices}")

            # 使用改进的 subplan 查找算法
            subplan_indices = self._find_algorithm_subplan_strict(
                start_indices,
                algorithm_type=algo_type,
                current_rule_id=rule_id,
                operator_hint_map=operator_hint_map,
                assigned_operators=assigned_operators
            )

            # 打印subplan_indices
            # print(f"Subplan indices for rule {rule_id}: {subplan_indices}")

            # 标记这些算子已被分配
            for idx in subplan_indices:
                if idx not in assigned_operators:
                    assigned_operators[idx] = rule_id

            # 判断是否是原始 SQL 的算子
            is_original_sql = self._is_original_sql_operator(algo_type, rule_op_indices)

            # 找到 root 算子
            root_op_idx = self._find_root_operator_index(subplan_indices)

            # 收集算子详细信息
            operator_details = []
            for idx in subplan_indices:
                op = self.operators[idx]
                op_id = self.operator_ids[idx]
                data_type = self.operator_data_types.get(idx, DataType.UNKNOWN)

                operator_details.append({
                    'operator_id': op_id,
                    'operator_type': self._get_operator_type(op),
                    'data_type': data_type.value,
                    'has_hint': (idx in rule_op_indices)
                })

            algorithms.append({
                'type': algo_type,
                'rule_id': rule_id,
                'is_original_sql': is_original_sql,
                'operators': [self.operator_ids[idx] for idx in subplan_indices],
                'rule_operators': [self.operator_ids[idx] for idx in rule_op_indices],
                'target_operator_id': self.operator_ids[target_op_idx] if target_op_idx is not None else None,
                'root_operator_id': self.operator_ids[root_op_idx] if root_op_idx is not None else None,
                'operator_details': operator_details,
                'total_operators': len(subplan_indices)
            })

        return algorithms

    def _sort_rule_groups_by_topology(self) -> List[tuple]:
        """
        按照拓扑顺序对 rule groups 排序

        返回排序后的 (rule_id, indices) 列表
        上游算法排在前面，下游算法排在后面
        """
        rule_order = []
        for rule_id, indices in self.rule_groups.items():
            # 使用算法中最小的算子索引作为排序依据
            min_idx = min(indices) if indices else float('inf')
            rule_order.append((min_idx, rule_id, indices))

        # 按照最小索引排序
        rule_order.sort(key=lambda x: x[0])

        return [(rule_id, indices) for _, rule_id, indices in rule_order]

    def _identify_algorithm_type(self, rule_id: str) -> str:
        """从 rule 名称推断算法类型"""
        if 'Aggregate' in rule_id:
            return 'aggregate'
        elif 'Join' in rule_id:
            return 'join'
        elif 'Window' in rule_id:
            return 'window'
        else:
            return 'unknown'

    def _find_target_operator(self, rule_id: str, rule_op_indices: List[int]) -> Optional[int]:
        """找到目标算子（被优化的原始算子）"""
        # 从 Rule ID 中提取目标算子 ID
        target_op_id = self._extract_target_operator_id(rule_id)
        if target_op_id and target_op_id in self.id_to_index:
            return self.id_to_index[target_op_id]
        return None

    def _extract_target_operator_id(self, rule_id: str) -> Optional[str]:
        """
        从 Rule ID 中提取目标算子 ID

        例如：
        - IncrementalAggPositiveDeltaDedupRule_cz::optimizer::LogicalAggregate#31766669
          -> 31766669
        - IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766417
          -> 31766417

        Returns:
            目标算子的 ID，如果没有则返回 None
        """
        # 查找 # 后面的数字
        match = re.search(r'#(\d+)', rule_id)
        if match:
            return match.group(1)
        return None

    def _find_algorithm_subplan_strict(self, start_indices: List[int], algorithm_type: str = None,
                                       current_rule_id: str = None, operator_hint_map: Dict = None,
                                       assigned_operators: Dict = None) -> List[int]:
        """
        使用严格边界检测查找增量算法的完整 subplan

        根据 prompt 4.2.1.3 的要求，设置严格的边界条件：
        1. 碰到不同的 hint 要终止
        2. aggregate 查找上游碰到 Final/Complete 要终止
        3. 碰到已经被其他算法占用的算子要终止（除了 TableScan）

        Args:
            start_indices: 起始算子索引列表
            algorithm_type: 算法类型
            current_rule_id: 当前算法的 rule ID
            operator_hint_map: 算子到 hint 的映射
            assigned_operators: 已分配的算子映射

        Returns:
            完整 subplan 的所有算子索引列表
        """
        if operator_hint_map is None:
            operator_hint_map = {}
        if assigned_operators is None:
            assigned_operators = {}

        subplan = set()
        current_algo_hint_indices = set(start_indices)

        def should_stop_at_operator(idx: int, direction: str = 'any') -> bool:
            """
            判断是否应该在此算子停止遍历

            停止条件（按优先级排序）：
            1. ⚠️ 算子包含 DeletePlan hint（最高优先级 - DeletePlan 不属于任何增量算法）
            2. 算子有不同的 hint（属于其他增量算法）
            3. 算子已被其他算法占用（除了 TableScan）
            4. 对于 aggregate 算法，遇到非起始点的 Final/Complete Aggregate
            5. ⚠️ Snapshot 边界：向上游遍历时，如果当前是 snapshot 且上游也是 snapshot，必须终止
            6. ⚠️ 邻居边界：如果当前算子的所有邻居（在遍历方向上）都属于其他算法，则当前算子是边界

            Args:
                idx: 算子索引
                direction: 遍历方向 ('down'=向上游, 'up'=向下游, 'any'=任意方向)
            """
            if idx < 0 or idx >= len(self.operators):
                return True

            # 条件 1: ⚠️ 检查是否包含 DeletePlan hint（最高优先级）
            # 根据 prompt original_prompt.md 第 60 行：
            # "如果是deleteplan相关算子应该不能继续查找，因为它不属于任何增量算法，
            #  由于plan是执行路径肯定不能跳过，所以不能继续找"
            #
            # 语义理解：
            # - DeletePlan 算子在执行路径中表示删除操作
            # - 如果遇到 DeletePlan，说明这条路径包含删除逻辑
            # - 必须终止遍历，不能跳过后继续查找（否则 subplan 不完整）
            #
            # ⚠️ 重要：这个检查必须在所有其他检查之前，因为 DeletePlan hint 在 _parse_rule_hints() 中被过滤了
            #         所以 DeletePlan 算子不在 operator_hint_map 中，条件 2 不会触发
            op = self.operators[idx]
            op_str = json.dumps(op)
            if 'deleteplan' in op_str.lower() or 'delete_plan' in op_str.lower():
                # 检查是否真的包含 DeletePlan Rule hint
                rule_pattern = r'Rule:([A-Za-z0-9_:#,\-()]+)'
                matches = re.findall(rule_pattern, op_str)
                for rule_name in matches:
                    if 'deleteplan' in rule_name.lower() or 'delete_plan' in rule_name.lower():
                        # 遇到 DeletePlan 算子，必须终止遍历
                        return True

            # 条件 2: 检查是否有不同的 hint
            if idx in operator_hint_map:
                hint_rule_id = operator_hint_map[idx]
                # 打印其他算法的 hint
                # print(f'xxxxxxxx operator {idx} hint: {hint_rule_id}')
                if hint_rule_id != current_rule_id:
                    return True

            # 条件 3: 检查是否已被其他算法占用
            if idx in assigned_operators:
                assigned_rule_id = assigned_operators[idx]
                if assigned_rule_id != current_rule_id:
                    # TableScan 可以被多个算法共享
                    op_id = self.operator_ids.get(idx, '')
                    is_table_scan = 'TableScan' in op_id or 'tablescan' in op_id.lower()
                    if not is_table_scan:
                        return True

            # debug： 如果rule id是Rule:IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766934，则打印信息
            # if current_rule_id == 'IncrementalJoinWithoutCondenseRule_cz::optimizer::LogicalJoin#31766934':
            #     print(f'{algorithm_type} xxxxxxxx operator {idx} rule id: {self.operators[idx]}, {self._get_operator_type(op), self._get_aggregate_mode(op)}')

            # 条件 4: 对于 aggregate 算法，检查 Final/Complete
            if algorithm_type == 'aggregate' and idx not in current_algo_hint_indices:
                op = self.operators[idx]
                op_type = self._get_operator_type(op)
                if op_type == 'aggregate':
                    agg_mode = self._get_aggregate_mode(op)
                    if agg_mode in ['Final', 'Complete', 'FINAL', 'COMPLETE']:
                        return True

            # 条件 5: ⚠️ Snapshot 边界检查（仅在向上游遍历时）
            # 根据 prompt original_prompt.md 第 70 行：
            # "对于snapshot的算子，向上游遍历时如果遇到上游也是snapshot，必须终止，
            #  因为snapshot表示完整状态，其上游的snapshot不应该再属于增量算法一部分"
            #
            # 语义理解：
            # - 如果当前算子是 snapshot，向上游遍历时遇到上游也是 snapshot，应该终止
            # - 因为 snapshot 表示完整状态，其上游的 snapshot 不应该属于增量算法
            # - 这是边界条件，不能跳过继续查找（否则 subplan 不完整）
            #
            # 实现逻辑：
            # - 检查当前算子的上游（输入）是否是 snapshot
            # - 如果当前是 snapshot 且上游也是 snapshot，则当前算子作为边界，不继续向上游遍历
            if direction == 'down':  # 向上游遍历
                current_data_type = self.operator_data_types.get(idx, DataType.UNKNOWN)
                if current_data_type == DataType.SNAPSHOT:
                    # 检查上游是否也是 snapshot
                    for input_idx in self.operator_dependencies.get(idx, []):
                        input_data_type = self.operator_data_types.get(input_idx, DataType.UNKNOWN)
                        if input_data_type == DataType.SNAPSHOT:
                            # 上游是 snapshot，当前算子作为边界，终止遍历
                            return True

            # 条件 6: ⚠️ Calc 算子的 DeltaState 和 Incremental hint 边界检查
            # 根据 prompt original_prompt.md 第 71 行：
            # "如果是calc有hint，且hint包含了DeltaState和Incremental这些也需要终止，避免跨越算法边界；
            #  如，类似HINT=delta,DeltaState:[1,14] - [1,43]_IncrementalJoinWithoutCondenseRule#cz::optimizer::LogicalJoin#973"
            #
            # 语义理解：
            # - Calc 算子如果包含 DeltaState 和 Incremental 相关的 hint，说明它是某个增量算法的边界
            # - 这种 hint 通常表示状态计算的边界，不应该跨越到其他算法
            # - 需要检查 hint 中是否同时包含 "DeltaState" 和 "Incremental" 关键字
            #
            # 实现逻辑：
            # - 检查算子是否是 calc 类型
            # - 检查算子的 hint 中是否同时包含 "DeltaState" 和 "Incremental"
            # - 如果满足条件，则作为边界，但在 bottom-up 遍历时应该包含该算子
            # - 返回特殊标记 'calc_boundary' 而不是 True/False
            #
            # 注意：这个检查需要特殊处理，所以单独提取到一个辅助函数中
            # 这里先不返回，让后续逻辑处理

            # 条件 7: ⚠️ 邻居边界检查
            # 根据用户反馈：如果当前算子的任何一个邻居（在遍历方向上）属于其他算法，
            # 则当前算子应该被视为边界，不应该继续遍历
            #
            # 问题场景：
            # - UnionAll22 的输入包含 Calc23（属于算法 #966）
            # - 但 UnionAll22 被包含在算法 #973 中
            # - 这导致算法 #973 通过 UnionAll22 继续遍历到了算法 #966 的算子
            #
            # 根本原因：
            # - 算法按拓扑顺序处理（#973 先于 #966）
            # - 当处理 #973 时，#966 的算子还没有被分配
            # - 所以 assigned_operators 检查无法阻止
            #
            # 解决方案：
            # - 检查当前算子在遍历方向上的邻居
            # - 如果**任何一个**邻居有不同的 hint，则当前算子是边界
            # - 这样可以在算法分配之前就阻止跨算法遍历

            # 注意：这个检查要在遍历**离开**当前算子时进行，而不是**进入**时
            # 所以我们检查的是"下一步要去的邻居"，而不是"当前算子本身"

            # 但是，should_stop_at_operator 是在**进入**算子时调用的
            # 所以我们需要检查：如果进入这个算子，它的邻居是否会导致跨算法

            # 实际上，更简单的方法是：
            # 在 dfs_down 和 dfs_up 中，在递归调用之前检查下一个算子是否有不同的 hint
            # 但这需要修改 dfs 函数，而不是 should_stop_at_operator

            # 所以这里的逻辑应该是：
            # 检查当前算子的输入（向上游遍历时）或输出（向下游遍历时）
            # 如果它们中有任何一个有不同的 hint，说明继续遍历会跨算法
            # 但这不应该阻止当前算子被包含，而是应该阻止继续遍历到邻居

            # 因此，这个检查实际上应该放在 dfs 函数中，而不是 should_stop_at_operator 中
            # should_stop_at_operator 应该只检查当前算子本身是否是边界

            # 让我们保持简单：如果当前算子没有 hint，但它的所有邻居都有不同的 hint，
            # 则当前算子是一个"孤岛"，应该被排除

            # 但根据用户的反馈，问题是：算法 #973 通过 UnionAll22 继续遍历到了 Calc23
            # 这说明在遍历到 Calc23 时，应该检测到它属于其他算法并停止
            # 但 Calc23 没有 hint，所以条件 2 不会触发

            # 真正的问题是：Calc23 应该先被算法 #966 占用，然后算法 #973 遍历到它时
            # 条件 3（assigned_operators）应该阻止

            # 但由于算法是按拓扑顺序处理的，#973 先处理，所以 Calc23 还没有被分配

            # 解决方案：在处理算法时，应该先标记所有有 hint 的算子及其邻居
            # 或者，改变处理顺序，让有更多 hint 的算法先处理

            # 但最简单的方法是：在遍历时，如果遇到一个算子，它的任何邻居有不同的 hint，
            # 就不要继续遍历到那个邻居

            # 这需要在 dfs 函数中实现，而不是在 should_stop_at_operator 中
            # 因为 should_stop_at_operator 检查的是"是否应该包含当前算子"
            # 而我们需要的是"是否应该继续遍历到邻居"

            return False

        def is_calc_boundary(idx: int) -> bool:
            """
            检查是否是 Calc 边界算子（包含 DeltaState 和 Incremental hint）

            这种算子应该被包含在 subplan 中，但不继续向上游或下游遍历
            """
            if idx < 0 or idx >= len(self.operators):
                return False

            op = self.operators[idx]
            op_type = self._get_operator_type(op)

            if op_type == 'calc':
                op_str = json.dumps(op)
                # 检查是否同时包含 DeltaState 和 Incremental 关键字
                if 'DeltaState' in op_str and 'Incremental' in op_str:
                    # 检查是否匹配特定的 hint 模式
                    # 示例格式：DeltaState:[1,14] - [1,43]_IncrementalJoinWithoutCondenseRule#...
                    hint_pattern = r'DeltaState:.*?Incremental'
                    if re.search(hint_pattern, op_str, re.IGNORECASE | re.DOTALL):
                        return True

            return False

        def is_df_aggregate(idx: int) -> bool:
            """
            检查是否是 DF (Dynamic Filter) Aggregate 算子

            根据 prompt original_prompt.md 第 80 行：
            "增量算法查找算子时,如果碰到aggregate,且aggregate的聚集函数包括MULTI_RANGE_COLLECT或者_DF_BF_COLLECT,
             则终止,不需要添加到subplan里,因为这个是一个df的aggregate,仅仅是优化的一个plan,不需要添加"

            这是一个排除边界：不添加到 subplan，直接返回

            Args:
                idx: 算子索引

            Returns:
                是否是 DF aggregate 算子
            """
            if idx < 0 or idx >= len(self.operators):
                return False

            op = self.operators[idx]
            op_type = self._get_operator_type(op)

            # 必须是 aggregate 类型
            if op_type != 'aggregate':
                return False

            # 检查聚集函数
            # 从 hashAgg 或 hashAggregate 中提取聚集函数
            agg_functions = self._get_aggregate_functions(op)

            # 检查是否包含 DF 相关的聚集函数
            df_functions = {'MULTI_RANGE_COLLECT', '_DF_BF_COLLECT', 'DF_BF_COLLECT', 'BF_COLLECT'}

            for func_name in agg_functions:
                if func_name.upper() in df_functions:
                    return True

            return False

        def dfs_down(idx: int, visited: set):
            """向下搜索：找所有输入算子（向上游遍历）"""
            if idx in visited:
                return

            # ⚠️ 步骤1: 先检查"排除边界"（DeletePlan 和 DF Aggregate）- 不添加到subplan
            # 根据 prompt 第 76 行：deleteplan 不需要添加到 subplan 里
            # 根据 prompt 第 80 行：DF aggregate 不需要添加到 subplan 里
            if self._is_deleteplan_operator(idx):
                # DeletePlan 算子不添加到 subplan，直接返回
                return

            if is_df_aggregate(idx):
                # DF Aggregate 算子不添加到 subplan，直接返回
                return

            # ⚠️ 步骤2: 添加到 subplan（在检查其他边界之前）
            visited.add(idx)
            subplan.add(idx)

            # ⚠️ 步骤3: 检查"包含边界"（需要添加但不继续遍历）
            # 根据 prompt 第 73-78 行：
            # - 不同hint：添加到subplan，但终止遍历
            # - final/complete：添加到subplan，但终止遍历
            # - snapshot：添加到subplan，但终止遍历
            # - calc边界：添加到subplan，但终止遍历

            # 检查是否是 Calc 边界算子
            if is_calc_boundary(idx):
                # Calc 边界：包含它但不继续向上游遍历
                return

            # 检查其他包含边界条件
            if should_stop_at_operator(idx, direction='down'):
                # 包含边界：已添加到 subplan，但不继续遍历
                return

            # ⚠️ 步骤4: 继续向上游遍历
            # 递归访问所有输入算子
            for input_idx in self.operator_dependencies.get(idx, []):
                # 检查输入算子是否有不同的 hint
                if input_idx in operator_hint_map:
                    input_hint = operator_hint_map[input_idx]
                    if input_hint != current_rule_id:
                        # 输入算子属于其他算法，不要继续遍历
                        continue

                # 继续遍历
                dfs_down(input_idx, visited)

        def dfs_up(idx: int, visited: set, stop_at_final_agg: bool = False):
            """向上搜索：找所有输出算子（向下游遍历）"""
            if idx in visited:
                return

            # ⚠️ 步骤1: 先检查"排除边界"（DeletePlan 和 DF Aggregate）- 不添加到subplan
            # 根据 prompt 第 76 行：deleteplan 不需要添加到 subplan 里
            # 根据 prompt 第 80 行：DF aggregate 不需要添加到 subplan 里
            if self._is_deleteplan_operator(idx):
                # DeletePlan 算子不添加到 subplan，直接返回
                return

            if is_df_aggregate(idx):
                # DF Aggregate 算子不添加到 subplan，直接返回
                return

            # ⚠️ 步骤2: 添加到 subplan（在检查其他边界之前）
            visited.add(idx)
            subplan.add(idx)

            # ⚠️ 步骤3: 检查"包含边界"（需要添加但不继续遍历）
            # 根据 prompt 第 73-78 行：
            # - 不同hint：添加到subplan，但终止遍历
            # - final/complete：添加到subplan，但终止遍历
            # - snapshot：添加到subplan，但终止遍历
            # - calc边界：添加到subplan，但终止遍历

            # 检查是否是 Calc 边界算子
            if is_calc_boundary(idx):
                # Calc 边界：包含它但不继续向下游遍历
                return

            # 检查其他包含边界条件
            if should_stop_at_operator(idx, direction='up'):
                # 包含边界：已添加到 subplan，但不继续遍历
                return

            # 检查是否是 Final/Complete Aggregate
            is_final_agg = False
            if stop_at_final_agg and algorithm_type == 'aggregate':
                op = self.operators[idx]
                op_type = self._get_operator_type(op)
                if op_type == 'aggregate':
                    agg_mode = self._get_aggregate_mode(op)
                    if agg_mode in ['Final', 'Complete', 'FINAL', 'COMPLETE']:
                        is_final_agg = True

            # ⚠️ 步骤4: 继续向下游遍历
            # 递归访问所有依赖当前算子的算子
            for output_idx in self.operator_dependents.get(idx, []):
                # 检查输出算子是否有不同的 hint
                if output_idx in operator_hint_map:
                    output_hint = operator_hint_map[output_idx]
                    if output_hint != current_rule_id:
                        # 输出算子属于其他算法，不要继续遍历
                        continue

                # 继续遍历
                if is_final_agg:
                    next_op = self.operators[output_idx]
                    next_op_type = self._get_operator_type(next_op)
                    if next_op_type != 'aggregate':
                        dfs_up(output_idx, visited, stop_at_final_agg)
                else:
                    dfs_up(output_idx, visited, stop_at_final_agg)

        # 从所有起始点开始双向搜索
        visited_down = set()
        visited_up = set()

        need_final_agg = (algorithm_type == 'aggregate')

        for idx in start_indices:
            dfs_down(idx, visited_down)
            dfs_up(idx, visited_up, stop_at_final_agg=need_final_agg)

        return sorted(list(subplan))

    def _find_root_operator_index(self, subplan_indices: List[int]) -> Optional[int]:
        """
        找到 subplan 中的 root 算子（最上层算子）

        根据 prompt 4.2.1.3：找到算子对应的 root 阶段

        逻辑：
        - Root 算子是 subplan 中没有后继的算子（在 subplan 内部）
        - 或者是索引最大的算子（最后执行的算子）
        """
        if not subplan_indices:
            return None

        subplan_set = set(subplan_indices)

        # 找到没有后继节点的算子（在 subplan 内部）
        for idx in reversed(subplan_indices):
            dependents = self.operator_dependents.get(idx, [])
            # 检查是否有后继节点在 subplan 内
            has_dependent_in_subplan = any(dep in subplan_set for dep in dependents)
            if not has_dependent_in_subplan:
                return idx

        # 如果都有后继，返回索引最大的
        return max(subplan_indices)

    def _is_original_sql_operator(self, algo_type: str, op_indices: List[int]) -> bool:
        """
        判断是否是原始 SQL 的算子（4.2.1.2）

        如果 rule 出现在对应类型的算子上，则是原始 SQL
        """
        for idx in op_indices:
            if idx >= len(self.operators):
                continue

            op = self.operators[idx]
            op_type = self._get_operator_type(op)

            if op_type == algo_type:
                return True

        return False

    def get_operator_summary(self, op_index: int) -> Dict:
        """获取算子的摘要信息"""
        if op_index >= len(self.operators):
            return {}

        op = self.operators[op_index]
        op_type = self._get_operator_type(op)
        data_type = self.operator_data_types.get(op_index, DataType.UNKNOWN)
        op_id = self.operator_ids.get(op_index, f"op_{op_index}")

        rule_ids = [
            rule_id for rule_id, indices in self.rule_groups.items()
            if op_index in indices
        ]

        return {
            'index': op_index,
            'id': op_id,
            'type': op_type,
            'data_type': data_type.value,
            'rule_ids': rule_ids
        }

    def _build_algorithm_dependencies(self, algorithms: List[Dict]) -> Dict[str, List[str]]:
        """
        构建增量算法之间的依赖关系

        基于算子的执行顺序，如果算法 A 的算子在算法 B 之前执行，
        则 B 依赖于 A
        """
        dependencies = {}

        for algo in algorithms:
            rule_id = algo['rule_id']
            dependencies[rule_id] = []

            # 使用 rule_operators 而不是 operators，因为我们关心的是算法的核心部分
            algo_indices = [
                self.id_to_index[op_id]
                for op_id in algo['rule_operators']
                if op_id in self.id_to_index
            ]

            if not algo_indices:
                continue

            min_idx = min(algo_indices)

            for other_algo in algorithms:
                if other_algo['rule_id'] == rule_id:
                    continue

                other_indices = [
                    self.id_to_index[op_id]
                    for op_id in other_algo['rule_operators']
                    if op_id in self.id_to_index
                ]

                if not other_indices:
                    continue

                other_max_idx = max(other_indices)

                if other_max_idx < min_idx:
                    dependencies[rule_id].append(other_algo['rule_id'])

        return dependencies

    def _generate_dependency_graph(self, algorithms: List[Dict],
                                   dependencies: Dict[str, List[str]]) -> str:
        """
        生成增量算法依赖关系的文本可视化

        格式：
        增量算法依赖关系图：

        [Aggregate#12345] (原始SQL)
          算子: op_10, op_15, op_20
          类型: aggregate
          ↓ 依赖于
          [Join#67890]
        """
        if not algorithms:
            return "未检测到增量算法"

        lines = ["", "=" * 60, "增量算法依赖关系图", "=" * 60, ""]

        # 按照算子索引排序（执行顺序）
        sorted_algos = sorted(
            algorithms,
            key=lambda a: min([
                self.id_to_index[op_id]
                for op_id in a['rule_operators']
                if op_id in self.id_to_index
            ]) if a['rule_operators'] else 0
        )

        for algo in sorted_algos:
            rule_id = algo['rule_id']
            algo_type = algo['type']
            is_original = algo['is_original_sql']
            operators = algo['operators']
            rule_operators = algo['rule_operators']

            tag = "(原始SQL)" if is_original else "(算法辅助)"
            lines.append(f"[{algo_type.upper()}] {tag}")

            if '#' in rule_id:
                short_id = rule_id.split('#')[-1]
                lines.append(f"  ID: #{short_id}")
            else:
                lines.append(f"  Rule: {rule_id[:50]}...")

            # 显示目标算子（从 Rule ID 中提取的）
            target_op_id = algo.get('target_operator_id')
            if target_op_id:
                lines.append(f"  目标算子: {target_op_id}")

            # 显示 Rule hint 算子
            if rule_operators:
                op_list = ', '.join(rule_operators[:5])
                if len(rule_operators) > 5:
                    op_list += f", ... (共{len(rule_operators)}个 hint 算子)"
                lines.append(f"  Rule 算子: {op_list}")

            # 显示完整 subplan 大小
            lines.append(f"  完整 subplan: {len(operators)} 个算子")

            # Root 算子
            if algo['root_operator_id']:
                lines.append(f"  Root 算子: {algo['root_operator_id']}")

            deps = dependencies.get(rule_id, [])
            if deps:
                lines.append(f"  ↓ 依赖于 {len(deps)} 个算法:")
                for dep_id in deps[:3]:
                    dep_algo = next((a for a in algorithms if a['rule_id'] == dep_id), None)
                    if dep_algo:
                        dep_type = dep_algo['type'].upper()
                        lines.append(f"    - {dep_type}")
            else:
                lines.append("  ↓ 无依赖（最底层）")

            lines.append("")

        lines.append("=" * 60)
        lines.append("执行顺序（从上到下）：")
        for i, algo in enumerate(sorted_algos, 1):
            tag = "原始SQL" if algo['is_original_sql'] else "辅助"
            subplan_size = len(algo['operators'])
            lines.append(f"  {i}. {algo['type'].upper()} ({tag}) - {subplan_size} 个算子")

        lines.append("=" * 60)

        return '\n'.join(lines)

    def _validate_algorithms(self, algorithms: List[Dict]) -> List[str]:
        """
        验证增量算法的正确性

        根据 prompt 4.2.1.3 第 59 行和 original_prompt.md 第 76 行的要求：
        1. 同一个 operator 不应该属于两个不同的增量算法（除非是 root 节点或 TableScan）
        2. 如果某个 operator 属于了上游的增量算法，就不应该属于下游的增量算法
        3. 对于 snapshot 的算子，增量算法遍历时应该停止
        4. 从 root 节点开始 top-down 遍历，在碰到边界算子前不应该有其他增量算法的算子

        注意：这些是验证规则，如果不满足说明脚本有问题，需要修改

        Returns:
            验证警告信息列表
        """
        warnings = []

        # 构建算子到算法的映射：operator_id -> [algorithm_rule_ids]
        op_to_algos = {}
        for algo in algorithms:
            rule_id = algo['rule_id']
            root_op_id = algo.get('root_operator_id')

            for op_id in algo['operators']:
                if op_id not in op_to_algos:
                    op_to_algos[op_id] = []
                op_to_algos[op_id].append({
                    'rule_id': rule_id,
                    'is_root': (op_id == root_op_id)
                })

        # 验证规则 1: 同一个 operator 不应该属于两个不同的增量算法
        # 例外：root 节点或 TableScan 可以横跨多个增量算法
        for op_id, algo_list in op_to_algos.items():
            if len(algo_list) > 1:
                # 检查是否是 TableScan
                is_table_scan = 'TableScan' in op_id or 'tablescan' in op_id.lower()

                # 检查是否所有归属都是作为 root 节点
                non_root_algos = [a for a in algo_list if not a['is_root']]

                # 如果不是 TableScan，且有多个非 root 归属，则报告警告
                if not is_table_scan and len(non_root_algos) > 1:
                    algo_names = [a['rule_id'] for a in non_root_algos]
                    warnings.append(
                        f"[算子唯一性] 算子 {op_id} 属于 {len(non_root_algos)} 个不同的增量算法（非 root 节点且非 TableScan）: "
                        f"{', '.join(algo_names[:3])}{'...' if len(algo_names) > 3 else ''}"
                    )

        # 验证规则 2: 如果某个 operator 属于了上游的增量算法，就不应该属于下游的增量算法
        # 构建算法的拓扑顺序（基于算子索引）
        algo_order = {}
        for algo in algorithms:
            rule_id = algo['rule_id']
            # 使用算法中最小的算子索引作为算法的顺序
            min_idx = float('inf')
            for op_id in algo['operators']:
                if op_id in self.id_to_index:
                    min_idx = min(min_idx, self.id_to_index[op_id])
            algo_order[rule_id] = min_idx if min_idx != float('inf') else 0

        # 检查算子是否同时属于上游和下游算法
        for op_id, algo_list in op_to_algos.items():
            if len(algo_list) > 1:
                # 检查是否是 TableScan（TableScan 可以横跨多个算法）
                is_table_scan = 'TableScan' in op_id or 'tablescan' in op_id.lower()

                # 按算法顺序排序
                sorted_algos = sorted(algo_list, key=lambda a: algo_order.get(a['rule_id'], 0))

                # 检查是否有非 root 且非 TableScan 的算子同时属于上游和下游算法
                for i in range(len(sorted_algos) - 1):
                    upstream_algo = sorted_algos[i]
                    downstream_algo = sorted_algos[i + 1]

                    if not upstream_algo['is_root'] and not downstream_algo['is_root'] and not is_table_scan:
                        warnings.append(
                            f"[上下游冲突] 算子 {op_id} 同时属于上游算法 {upstream_algo['rule_id']} "
                            f"和下游算法 {downstream_algo['rule_id']}"
                        )

        # 验证规则 3: 对于 snapshot 的算子，增量算法不应该继续向上游遍历
        for algo in algorithms:
            rule_id = algo['rule_id']

            for op_id in algo['operators']:
                if op_id not in self.id_to_index:
                    continue

                idx = self.id_to_index[op_id]
                data_type = self.operator_data_types.get(idx, DataType.UNKNOWN)

                # 如果这个算子是 snapshot 类型
                if data_type == DataType.SNAPSHOT:
                    # 检查其上游算子是否也在这个算法中
                    upstream_indices = self.operator_dependencies.get(idx, [])
                    for upstream_idx in upstream_indices:
                        upstream_id = self.operator_ids.get(upstream_idx)
                        if upstream_id and upstream_id in algo['operators']:
                            upstream_data_type = self.operator_data_types.get(upstream_idx, DataType.UNKNOWN)
                            if upstream_data_type == DataType.SNAPSHOT:
                                warnings.append(
                                    f"[Snapshot 边界] 算法 {rule_id} 包含 snapshot 算子 {op_id}，"
                                    f"但继续向上游遍历到 snapshot 算子 {upstream_id}"
                                )

        # 验证规则 4: 从 root 节点开始 top-down 遍历，检查是否有其他算法的算子混入
        # 根据 original_prompt.md 第 76 行：
        # "从找到的root节点开始top-down遍历所有算子，在碰到了非边界算子前是不是有其他增量算法的算子，如果有，说明脚本有问题"
        warnings.extend(self._validate_topdown_traversal(algorithms, op_to_algos))

        return warnings

    def _validate_topdown_traversal(self, algorithms: List[Dict], op_to_algos: Dict) -> List[str]:
        """
        验证规则 5: 从 root 节点开始 top-down 遍历，检查是否有其他算法的算子混入

        根据 original_prompt.md 第 76 行：
        "从找到的root节点开始top-down遍历所有算子，在碰到了非边界算子前是不是有其他增量算法的算子，如果有，说明脚本有问题"

        实现逻辑：
        1. 从每个算法的 root 节点开始
        2. 沿着依赖关系（inputIds）向下游（输入方向）遍历
        3. 在遇到边界条件前，检查路径上的算子是否属于其他算法
        4. 如果有，说明 _find_algorithm_subplan_strict 的边界检测有问题

        ⚠️ 重要：这是验证 subplan 识别是否正确的规则
        - 如果从 root 遍历时遇到了其他算法的算子，说明当前算法的 subplan 包含了不该包含的算子
        - 或者说明边界检测没有正确终止遍历

        边界条件（与 _find_algorithm_subplan_strict 中的 should_stop_at_operator 一致）：
        - 算子包含 DeletePlan hint
        - 算子有不同的 Rule hint
        - 算子已被其他算法占用（除了 TableScan）
        - 对于 aggregate 算法，遇到 Final/Complete
        - Snapshot 边界

        Args:
            algorithms: 增量算法列表
            op_to_algos: 算子到算法的映射

        Returns:
            验证警告信息列表
        """
        warnings = []

        # 构建算子到 hint 的映射
        operator_hint_map = {}
        for rule_id, indices in self.rule_groups.items():
            for idx in indices:
                operator_hint_map[idx] = rule_id

        for algo in algorithms:
            rule_id = algo['rule_id']
            root_op_id = algo.get('root_operator_id')

            if not root_op_id or root_op_id not in self.id_to_index:
                continue

            root_idx = self.id_to_index[root_op_id]
            algo_type = algo['type']

            # 构建当前算法的 subplan 算子集合（用于检查算子是否在 subplan 中）
            algo_op_ids = set(algo['operators'])
            algo_op_indices = set()
            for op_id in algo_op_ids:
                if op_id in self.id_to_index:
                    algo_op_indices.add(self.id_to_index[op_id])

            # 从 root 节点开始 top-down 遍历（沿着依赖关系遍历，不限制只遍历 subplan）
            visited = set()
            path_warnings = self._topdown_traverse_and_check(
                root_idx, rule_id, algo_type, operator_hint_map, op_to_algos, algo_op_indices, visited
            )

            warnings.extend(path_warnings)

        return warnings

    def _topdown_traverse_and_check(self, current_idx: int, current_rule_id: str,
                                     algo_type: str, operator_hint_map: Dict,
                                     op_to_algos: Dict, algo_op_indices: Set[int],
                                     visited: Set[int]) -> List[str]:
        """
        从当前节点开始双向遍历并检查是否有其他算法的算子

        ⚠️ 重要：需要双向遍历（向上游和向下游）
        - 向上游（输入方向）：沿着 operator_dependencies 遍历
        - 向下游（输出方向）：沿着 operator_dependents 遍历
        - 这样才能遍历到 subplan 的所有算子

        Args:
            current_idx: 当前算子索引
            current_rule_id: 当前算法的 rule ID
            algo_type: 算法类型
            operator_hint_map: 算子到 hint 的映射
            op_to_algos: 算子到算法的映射
            algo_op_indices: 当前算法的 subplan 算子索引集合（用于检查）
            visited: 已访问的算子集合

        Returns:
            警告信息列表
        """
        warnings = []

        if current_idx in visited:
            return warnings

        visited.add(current_idx)

        # 检查是否到达边界
        if self._is_boundary_operator(current_idx, current_rule_id, algo_type, operator_hint_map):
            # 到达边界，停止遍历
            return warnings

        # 检查当前算子是否在当前算法的 subplan 中
        current_op_id = self.operator_ids.get(current_idx)
        in_current_subplan = current_idx in algo_op_indices

        # 如果当前算子在 subplan 中，检查它是否属于其他算法
        if in_current_subplan and current_op_id and current_op_id in op_to_algos:
            algo_list = op_to_algos[current_op_id]

            # 过滤掉当前算法和 TableScan
            is_table_scan = 'TableScan' in current_op_id or 'tablescan' in current_op_id.lower()

            if not is_table_scan:
                other_algos = [a for a in algo_list if a['rule_id'] != current_rule_id]

                if other_algos:
                    # 发现当前算子在 subplan 中，但属于其他算法
                    # 这说明 _find_algorithm_subplan_strict 的边界检测有问题
                    other_rule_ids = [a['rule_id'] for a in other_algos]
                    warnings.append(
                        f"[Top-Down 遍历] 算法 {current_rule_id} 的 subplan 包含了算子 {current_op_id}，"
                        f"但该算子属于其他算法: {', '.join(other_rule_ids[:3])}{'...' if len(other_rule_ids) > 3 else ''}"
                        f"（说明 subplan 边界检测有问题）"
                    )

        # 双向遍历：向上游（输入方向）
        input_indices = self.operator_dependencies.get(current_idx, [])
        for input_idx in input_indices:
            sub_warnings = self._topdown_traverse_and_check(
                input_idx, current_rule_id, algo_type, operator_hint_map, op_to_algos, algo_op_indices, visited
            )
            warnings.extend(sub_warnings)

        # 双向遍历：向下游（输出方向）
        output_indices = self.operator_dependents.get(current_idx, [])
        for output_idx in output_indices:
            sub_warnings = self._topdown_traverse_and_check(
                output_idx, current_rule_id, algo_type, operator_hint_map, op_to_algos, algo_op_indices, visited
            )
            warnings.extend(sub_warnings)

        return warnings

    def _is_deleteplan_operator(self, idx: int) -> bool:
        """
        检查算子是否包含 DeletePlan hint

        根据 prompt original_prompt.md 第 76 行：
        "deleteplan 不需要添加到 subplan 里"

        Args:
            idx: 算子索引

        Returns:
            是否是 DeletePlan 算子
        """
        if idx < 0 or idx >= len(self.operators):
            return False

        op = self.operators[idx]
        op_str = json.dumps(op)

        if 'deleteplan' in op_str.lower() or 'delete_plan' in op_str.lower():
            rule_pattern = r'Rule:([A-Za-z0-9_:#,\-()]+)'
            matches = re.findall(rule_pattern, op_str)
            for rule_name in matches:
                if 'deleteplan' in rule_name.lower() or 'delete_plan' in rule_name.lower():
                    return True

        return False

    def _is_boundary_operator(self, idx: int, current_rule_id: str, algo_type: str,
                              operator_hint_map: Dict) -> bool:
        """
        判断是否是边界算子（与 _find_algorithm_subplan_strict 中的 should_stop_at_operator 逻辑一致）

        边界条件：
        1. 算子包含 DeletePlan hint
        2. 算子有不同的 Rule hint
        3. 对于 aggregate 算法，遇到 Final/Complete
        4. Snapshot 边界

        Args:
            idx: 算子索引
            current_rule_id: 当前算法的 rule ID
            algo_type: 算法类型
            operator_hint_map: 算子到 hint 的映射

        Returns:
            是否是边界算子
        """
        if idx < 0 or idx >= len(self.operators):
            return True

        # 条件 1: 检查是否包含 DeletePlan hint
        if self._is_deleteplan_operator(idx):
            return True

        # 条件 2: 检查是否有不同的 hint
        op = self.operators[idx]
        if idx in operator_hint_map:
            hint_rule_id = operator_hint_map[idx]
            if hint_rule_id != current_rule_id:
                return True

        # 条件 3: 对于 aggregate 算法，检查 Final/Complete
        if algo_type == 'aggregate':
            op_type = self._get_operator_type(op)
            if op_type == 'aggregate':
                agg_mode = self._get_aggregate_mode(op)
                if agg_mode in ['Final', 'Complete', 'FINAL', 'COMPLETE']:
                    return True

        # 条件 4: Snapshot 边界
        current_data_type = self.operator_data_types.get(idx, DataType.UNKNOWN)
        if current_data_type == DataType.SNAPSHOT:
            for input_idx in self.operator_dependencies.get(idx, []):
                input_data_type = self.operator_data_types.get(input_idx, DataType.UNKNOWN)
                if input_data_type == DataType.SNAPSHOT:
                    return True

        return False


def create_incremental_analyzer(stage_data: Dict) -> IncrementalAlgorithmAnalyzer:
    """为 stage_data 创建 IncrementalAlgorithmAnalyzer"""
    plan = stage_data.get('plan', {})
    return IncrementalAlgorithmAnalyzer(plan)
