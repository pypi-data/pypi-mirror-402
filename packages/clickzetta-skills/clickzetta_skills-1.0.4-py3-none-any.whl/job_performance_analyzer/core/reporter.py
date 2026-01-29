#!/usr/bin/env python3
"""报告生成器"""
import json
from typing import Dict, List, Any
from datetime import datetime

class Reporter:
    def __init__(self):
        self.findings = []
        self.recommendations = []
        self.insights = []
        self.warnings = []
        self.metadata = {}
        self.incremental_algorithms = None  # 增量算法数据
    
    def add_finding(self, finding: Dict):
        self.findings.append(finding)
    
    def add_recommendation(self, recommendation: Dict):
        self.recommendations.append(recommendation)
    
    def add_insight(self, insight: Dict):
        self.insights.append(insight)
    
    def set_metadata(self, key: str, value: Any):
        self.metadata[key] = value

    def set_incremental_algorithms(self, data: Dict):
        """设置增量算法数据"""
        self.incremental_algorithms = data
    
    def merge_analysis_result(self, result: Dict):
        self.findings.extend(result.get('findings', []))
        self.recommendations.extend(result.get('recommendations', []))
        self.insights.extend(result.get('insights', []))
    
    def generate_console_report(self, context: Dict) -> str:
        lines = ["=" * 80, "Job 性能分析报告", "=" * 80]
        lines.append(f"\n[概况]")
        lines.append(f"  SQL 类型: {self.metadata.get('sql_type', 'Unknown')}")
        lines.append(f"  VC 模式: {self.metadata.get('vc_mode', 'Unknown')}")
        lines.append(f"  总耗时: {self.metadata.get('total_time_seconds', 0):.2f}s")
        lines.append(f"  Stage 数: {self.metadata.get('stage_count', 0)}")
        if self.metadata.get('refresh_type'):
            lines.append(f"  刷新类型: {self.metadata.get('refresh_type')}")
        
        if self.findings:
            lines.append(f"\n[发现问题] ({len(self.findings)})")
            for f in self.findings:
                lines.append(f"  [{f.get('severity')}] {f.get('type')} - Stage {f.get('stage_id')}")
                if f.get('description'):
                    lines.append(f"         {f.get('description')}")
        
        if self.recommendations:
            unique_recs = self._deduplicate_recommendations()
            lines.append(f"\n[参数建议] ({len(unique_recs)})")
            lines.append("=" * 80)
            for i, rec in enumerate(unique_recs, 1):
                lines.append(f"\n{i}. [P{rec.get('priority')}] [Impact: {rec.get('impact')}]")
                lines.append(f"   set {rec.get('setting')} = {rec.get('value')};")
                if rec.get('current_value'):
                    lines.append(f"   当前值: {rec.get('current_value')}")
                lines.append(f"   理由: {rec.get('reason')}")
                if rec.get('warning'):
                    lines.append(f"   ⚠️  {rec.get('warning')}")
            lines.append("=" * 80)
        else:
            lines.append("\n[参数建议]\n  ✓ 未发现需要调整的参数")
        
        if self.insights:
            lines.append(f"\n[关键洞察] (显示前 10 条)")
            for insight in self.insights[:10]:
                lines.append(f"  💡 {insight.get('message', '')}")
        
        return "\n".join(lines)
    
    def generate_json_report(self) -> Dict:
        report = {
            'generated_at': datetime.now().isoformat(),
            'metadata': self.metadata,
            'findings': self.findings,
            'warnings': self.warnings,
            'recommendations': self._deduplicate_recommendations(),
            'insights': self.insights,
        }

        # 如果有增量算法数据，添加到报告中
        if self.incremental_algorithms:
            report['incremental_algorithms'] = self.incremental_algorithms

        return report
    
    def _deduplicate_recommendations(self) -> List[Dict]:
        unique = {}
        for rec in self.recommendations:
            setting = rec.get('setting', '')
            if setting not in unique or rec.get('priority', 9) < unique[setting].get('priority', 9):
                unique[setting] = rec
        return sorted(unique.values(), key=lambda x: x.get('priority', 9))
    
    def save_json_report(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.generate_json_report(), f, indent=2, ensure_ascii=False)
        return output_path
