#!/usr/bin/env python3
"""核心解析器 - 解析 plan.json 和 job_profile.json"""
import json
from typing import Dict, Any

try:
    from loguru import logger
except ImportError:
    import logging
    from loguru import logger


class PlanProfileParser:
    def __init__(self, plan_file: str, profile_file: str):
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                self.plan = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Plan 文件不存在: {plan_file}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Plan 文件 JSON 格式错误: {plan_file}, 错误: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"读取 Plan 文件失败: {plan_file}, 错误: {str(e)}")

        # job_profile.json 是可选的
        self.profile = {}
        self.has_profile = False
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                # 检查是否为空文件或空对象
                if profile_data:
                    if 'data' in profile_data:
                        self.profile = profile_data.get('data', {}).get('jobSummary', {})
                    else:
                        self.profile = profile_data.get('jobSummary', profile_data)

                    # 检查 profile 是否有实际数据
                    if self.profile and self.profile.get('stageSummary'):
                        self.has_profile = True
                        logger.info("成功加载 job_profile.json")
                    else:
                        logger.warning("job_profile.json 为空或无有效数据，将跳过依赖运行时数据的分析")
                else:
                    logger.warning("job_profile.json 为空，将跳过依赖运行时数据的分析")
        except FileNotFoundError:
            logger.warning(f"Profile 文件不存在: {profile_file}，将跳过依赖运行时数据的分析")
        except json.JSONDecodeError as e:
            logger.warning(f"Profile 文件 JSON 格式错误: {profile_file}, 错误: {str(e)}，将跳过依赖运行时数据的分析")
        except Exception as e:
            logger.warning(f"读取 Profile 文件失败: {profile_file}, 错误: {str(e)}，将跳过依赖运行时数据的分析")

        self._parsed_data = None
    
    def parse(self) -> Dict[str, Any]:
        if self._parsed_data:
            return self._parsed_data

        try:
            settings = dict(self.plan.get('settings', {}))
            sql_text = settings.get('cz.sql.text', '')

            # 解析版本信息
            # build_info 可能在两个位置：
            # 1. plan['build_info'] (旧格式)
            # 2. plan['settings']['build_info'] (新格式，字符串格式)
            git_branch = 'Unknown'

            # 先尝试从 settings 中获取（新格式）
            build_info_str = settings.get('build_info', '')
            if build_info_str and isinstance(build_info_str, str):
                # 格式: "BuildInfo:GitBranch:release-v1.2,GitVersion:xxx,..."
                for part in build_info_str.split(','):
                    if 'GitBranch:' in part:
                        git_branch = part.split('GitBranch:')[1].strip()
                        break

            # 如果没找到，尝试从 plan['build_info'] 获取（旧格式）
            if git_branch == 'Unknown':
                build_info_dict = self.plan.get('build_info', {})
                if isinstance(build_info_dict, dict):
                    git_branch = build_info_dict.get('GitBranch', 'Unknown')

            self._parsed_data = {
                'sql_info': {
                    'text': sql_text,
                    'is_refresh': 'REFRESH' in sql_text.upper(),
                    'is_compaction': 'COMPACTION' in sql_text.upper() or 'OPTIMIZE' in sql_text.upper(),
                },
                'version_info': {
                    'git_branch': git_branch,
                },
                'vc_mode': {
                    'is_ap': settings.get('cz.inner.is.ap.vc', '0') == '1',
                    'mode': 'AP' if settings.get('cz.inner.is.ap.vc', '0') == '1' else 'GP',
                },
                'settings': settings,
                'plan_stages': self._parse_plan_stages(),
                'profile_stages': self._parse_profile_stages(),
                'has_profile': self.has_profile,  # 添加标志位
            }
            return self._parsed_data
        except Exception as e:
            logger.error(f"解析数据失败: {str(e)}")
            raise RuntimeError(f"解析数据失败: {str(e)}")
    
    def _parse_plan_stages(self) -> Dict[str, Dict]:
        stages = {}
        if 'dml' in self.plan and 'stages' in self.plan['dml']:
            for stage in self.plan['dml']['stages']:
                stage_id = stage.get('id', stage.get('stageId'))
                if stage_id:
                    stages[stage_id] = stage
        return stages
    
    def _parse_profile_stages(self) -> Dict[str, Dict]:
        stages = {}
        if 'stageSummary' in self.profile:
            for stage_id, stage_data in self.profile['stageSummary'].items():
                stages[stage_id] = stage_data
        return stages
    
    def is_refresh_sql(self) -> bool:
        return 'REFRESH' in self.plan.get('settings', {}).get('cz.sql.text', '').upper()
    
    def is_ap_mode(self) -> bool:
        return self.plan.get('settings', {}).get('cz.inner.is.ap.vc', '0') == '1'
