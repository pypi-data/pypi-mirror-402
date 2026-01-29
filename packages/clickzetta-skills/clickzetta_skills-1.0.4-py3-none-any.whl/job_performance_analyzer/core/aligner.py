#!/usr/bin/env python3
"""Stage 对齐器 - 对齐 Plan 和 Profile 的 Stage 数据"""
from typing import Dict, List, Any

try:
    from loguru import logger
except ImportError:
    import logging
    from loguru import logger


class StageAligner:
    def __init__(self, parsed_data: Dict[str, Any]):
        self.plan_stages = parsed_data.get('plan_stages', {})
        self.profile_stages = parsed_data.get('profile_stages', {})
        self.has_profile = parsed_data.get('has_profile', False)  # 是否有有效的 profile 数据
        self._aligned_stages = {}
        self._stage_metrics = {}
        self._operator_analysis = []
        self._total_job_time = 0
        self._stage_dependencies = {}  # stage_id -> [upstream_stage_ids]

    def align(self) -> Dict[str, Any]:
        self._calculate_stage_metrics()
        self._parse_stage_dependencies()
        self._align_stages()
        self._analyze_operators()
        return {
            'aligned_stages': self._aligned_stages,
            'stage_metrics': self._stage_metrics,
            'operator_analysis': self._operator_analysis,
            'total_job_time': self._total_job_time,
            'stage_dependencies': self._stage_dependencies,
        }

    def _calculate_stage_metrics(self):
        """计算 Stage 指标"""
        # 如果没有 profile 数据，跳过指标计算
        if not self.has_profile:
            logger.info("没有 profile 数据，跳过 Stage 指标计算")
            return

        for stage_id, stage_data in self.profile_stages.items():
            try:
                # 计算 DOP：累加所有 task count
                task_count_detail = stage_data.get('taskCountDetail', {})
                if task_count_detail:
                    dop = sum(int(float(c)) for c in task_count_detail.values() if c)
                else:
                    # 如果没有 taskCountDetail，尝试从其他字段获取
                    dop = int(stage_data.get('taskCount', 0))

                # 防止 DOP 为 0
                if dop == 0:
                    logger.warning(f"Stage {stage_id} DOP 为 0，设置为 1")
                    dop = 1

                elapsed_ms = int(stage_data.get('endTime', 0)) - int(stage_data.get('startTime', 0))
                io_stats = stage_data.get('inputOutputStats', {})

                self._stage_metrics[stage_id] = {
                    'elapsed_ms': elapsed_ms,
                    'dop': dop,
                    'input_bytes': int(io_stats.get('inputBytes', 0)),
                    'output_bytes': int(io_stats.get('outputBytes', 0)),
                    'spill_bytes': int(io_stats.get('spillingBytes', 0)),
                }
                self._total_job_time += elapsed_ms
            except Exception as e:
                logger.error(f"计算 Stage {stage_id} 指标失败: {str(e)}")
                # 设置默认值
                self._stage_metrics[stage_id] = {
                    'elapsed_ms': 0, 'dop': 1,
                    'input_bytes': 0, 'output_bytes': 0, 'spill_bytes': 0,
                }

    def _parse_stage_dependencies(self):
        """解析 Stage 依赖关系"""
        for stage_id, plan in self.plan_stages.items():
            upstream_stages = []

            # 方法1: 从 inputStages 字段提取
            if 'inputStages' in plan:
                input_stages = plan.get('inputStages', [])
                if isinstance(input_stages, list):
                    upstream_stages.extend(input_stages)

            # 方法2: 从 inputs 字段提取
            if 'inputs' in plan:
                inputs = plan.get('inputs', [])
                for inp in inputs:
                    if isinstance(inp, dict) and 'stageId' in inp:
                        upstream_stages.append(inp['stageId'])
                    elif isinstance(inp, str):
                        upstream_stages.append(inp)

            # 方法3: 从 operators 中的 exchange 提取
            operators = plan.get('operators', [])
            for op in operators:
                if 'exchange' in op:
                    exchange = op.get('exchange', {})
                    if 'inputStageId' in exchange:
                        upstream_stages.append(exchange['inputStageId'])
                    elif 'input' in exchange and isinstance(exchange['input'], dict):
                        if 'stageId' in exchange['input']:
                            upstream_stages.append(exchange['input']['stageId'])

            # 去重
            self._stage_dependencies[stage_id] = list(set(upstream_stages))

    def _align_stages(self):
        """对齐 Plan 和 Profile 数据"""
        for stage_id in self.plan_stages:
            plan_data = self.plan_stages[stage_id]
            # 提取 operators 列表
            plan_operators = plan_data.get('operators', [])

            # 如果有 profile 数据，进行对齐；否则只使用 plan 数据
            if self.has_profile and stage_id in self.profile_stages:
                self._aligned_stages[stage_id] = {
                    'stage_id': stage_id,
                    'plan': plan_data,
                    'profile': self.profile_stages[stage_id],
                    'metrics': self._stage_metrics.get(stage_id, {}),
                    'upstream_stages': self._stage_dependencies.get(stage_id, []),
                    'plan_operators': plan_operators,  # 添加 operators 列表
                }
            else:
                # 没有 profile 数据，只使用 plan 数据
                self._aligned_stages[stage_id] = {
                    'stage_id': stage_id,
                    'plan': plan_data,
                    'profile': {},  # 空 profile
                    'metrics': {},  # 空 metrics
                    'upstream_stages': self._stage_dependencies.get(stage_id, []),
                    'plan_operators': plan_operators,
                }

    def _analyze_operators(self):
        """分析 Operator 性能"""
        # 如果没有 profile 数据，跳过 Operator 分析
        if not self.has_profile:
            logger.info("没有 profile 数据，跳过 Operator 性能分析")
            return

        for stage_id, stage_data in self._aligned_stages.items():
            profile = stage_data.get('profile', {})
            metrics = stage_data.get('metrics', {})
            if 'operatorSummary' not in profile:
                continue

            for op_id, op_data in profile['operatorSummary'].items():
                try:
                    wall_time = op_data.get('wallTimeNs', {})
                    max_ms = int(wall_time.get('max', 0)) / 1_000_000
                    avg_ms = int(wall_time.get('avg', 0)) / 1_000_000
                    stage_elapsed = metrics.get('elapsed_ms', 1)  # 防止除零

                    self._operator_analysis.append({
                        'stage_id': stage_id,
                        'operator_id': op_id,
                        'max_time_ms': max_ms,
                        'avg_time_ms': avg_ms,
                        'stage_pct': (max_ms / stage_elapsed * 100) if stage_elapsed else 0,
                        'total_pct': (max_ms / self._total_job_time * 100) if self._total_job_time else 0,
                        'skew_ratio': max_ms / avg_ms if avg_ms > 0 else 1.0,
                        'operator_data': op_data,
                    })
                except Exception as e:
                    logger.error(f"分析 Operator {op_id} 失败: {str(e)}")

        self._operator_analysis.sort(key=lambda x: x['max_time_ms'], reverse=True)

    def get_top_stages(self, n: int = 10) -> List[tuple]:
        """获取 Top N 耗时 Stage"""
        return sorted(self._stage_metrics.items(), key=lambda x: x[1]['elapsed_ms'], reverse=True)[:n]

    def get_top_operators(self, n: int = 10) -> List[Dict]:
        """获取 Top N 耗时 Operator"""
        return self._operator_analysis[:n]

    def get_upstream_stages(self, stage_id: str) -> List[str]:
        """获取指定 Stage 的上游 Stage ID 列表"""
        return self._stage_dependencies.get(stage_id, [])

    def get_upstream_dops(self, stage_id: str) -> List[int]:
        """获取上游 Stage 的 DOP 列表"""
        upstream_ids = self.get_upstream_stages(stage_id)
        dops = []
        for upstream_id in upstream_ids:
            if upstream_id in self._stage_metrics:
                dops.append(self._stage_metrics[upstream_id].get('dop', 0))
        return [d for d in dops if d > 0]  # 过滤掉 0

