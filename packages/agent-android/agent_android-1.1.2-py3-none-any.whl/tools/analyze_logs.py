#!/usr/bin/env python3
"""
NLP 日志分析工具

分析 NLP 执行日志，生成统计报告和优化建议
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import Counter, defaultdict

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nlp_logger import NLPExecutionLogger


class NLPLogAnalyzer:
    """NLP 日志分析器"""

    def __init__(self, log_dir: str = None):
        """
        初始化分析器

        Args:
            log_dir: 日志目录
        """
        self.logger = NLPExecutionLogger(log_dir)
        self.log_dir = self.logger.log_dir

    def analyze_failures(self, limit: int = 100) -> Dict[str, Any]:
        """
        分析失败记录

        Args:
            limit: 分析的记录数量

        Returns:
            分析结果字典
        """
        failures = self.logger.get_recent_failures(limit)

        if not failures:
            return {"total": 0, "message": "没有失败记录"}

        # 统计失败原因
        failure_reasons = Counter([f['failure_reason'] for f in failures])

        # 统计失败的描述模式
        descriptions = [f['user_description'] for f in failures]

        # 按位置统计
        positions = Counter([
            f['parsed_result'].get('position', 'unknown')
            for f in failures
        ])

        # 按类型统计
        types = Counter([
            f['parsed_result'].get('type', 'unknown')
            for f in failures
        ])

        # 按策略统计
        strategies = Counter()
        for f in failures:
            for strategy in f['strategies_tried']:
                strategies[strategy] += 1

        # 分析失败的描述模式
        description_patterns = self._analyze_description_patterns(descriptions)

        return {
            "total": len(failures),
            "failure_reasons": dict(failure_reasons.most_common(10)),
            "positions": dict(positions.most_common(10)),
            "types": dict(types.most_common(10)),
            "strategies": dict(strategies.most_common(10)),
            "description_patterns": description_patterns,
            "recent_failures": failures[:10]
        }

    def _analyze_description_patterns(self, descriptions: List[str]) -> Dict[str, Any]:
        """
        分析描述模式

        Args:
            descriptions: 描述列表

        Returns:
            模式分析结果
        """
        patterns = {
            "length_distribution": {"short": 0, "medium": 0, "long": 0},
            "has_position": 0,
            "has_type": 0,
            "has_quotes": 0,
            "complexity": {"simple": 0, "medium": 0, "complex": 0}
        }

        for desc in descriptions:
            # 长度分布
            length = len(desc)
            if length < 10:
                patterns["length_distribution"]["short"] += 1
            elif length < 20:
                patterns["length_distribution"]["medium"] += 1
            else:
                patterns["length_distribution"]["long"] += 1

            # 关键词检查
            for pos in ['左上', '右上', '左下', '右下', '顶部', '底部', '左侧', '右侧', '中间', '中央']:
                if pos in desc:
                    patterns["has_position"] += 1
                    break

            for type_kw in ['图标', '按钮', '文字', '输入框']:
                if type_kw in desc:
                    patterns["has_type"] += 1
                    break

            if '"' in desc or "'" in desc:
                patterns["has_quotes"] += 1

            # 复杂度
            complexity_score = 0
            if patterns["has_position"]:
                complexity_score += 1
            if patterns["has_type"]:
                complexity_score += 1
            if patterns["has_quotes"]:
                complexity_score += 1

            if complexity_score == 0:
                patterns["complexity"]["simple"] += 1
            elif complexity_score <= 1:
                patterns["complexity"]["medium"] += 1
            else:
                patterns["complexity"]["complex"] += 1

        # 计算百分比
        total = len(descriptions) if descriptions else 1
        patterns["has_position"] = f"{patterns['has_position']/total*100:.1f}%"
        patterns["has_type"] = f"{patterns['has_type']/total*100:.1f}%"
        patterns["has_quotes"] = f"{patterns['has_quotes']/total*100:.1f}%"

        return patterns

    def generate_optimization_suggestions(self) -> List[str]:
        """
        生成优化建议

        Returns:
            建议列表
        """
        analysis = self.analyze_failures()
        suggestions = []

        # 检查失败原因
        if "未找到匹配的图标" in analysis.get("failure_reasons", {}):
            suggestions.append(
                "💡 建议: 添加更多描述关键词到 desc_keywords 列表"
            )
            suggestions.append(
                "💡 建议: 考虑使用 AI 视觉识别作为备选策略"
            )

        # 检查位置关键词使用
        positions = analysis.get("positions", {})
        if positions.get("unknown", 0) > 10:
            suggestions.append(
                "💡 建议: 很多失败没有位置信息，鼓励用户使用位置关键词"
            )

        # 检查类型关键词使用
        types = analysis.get("types", {})
        if types.get("unknown", 0) > 10:
            suggestions.append(
                "💡 建议: 很多失败没有类型信息，鼓励用户明确元素类型"
            )

        # 检查描述长度
        patterns = analysis.get("description_patterns", {})
        length_dist = patterns.get("length_distribution", {})
        if length_dist.get("short", 0) > length_dist.get("medium", 0):
            suggestions.append(
                "💡 建议: 很多失败描述过短，建议用户提供更详细的描述"
            )

        # 检查策略效果
        strategies = analysis.get("strategies", {})
        if strategies.get("position+type", 0) > strategies.get("text", 0):
            suggestions.append(
                "💡 建议: position+type 策略失败较多，优化位置范围或类型匹配"
            )

        return suggestions

    def generate_daily_report(self, date: str = None) -> str:
        """
        生成每日报告

        Args:
            date: 日期（YYYY-MM-DD），默认为今天

        Returns:
            Markdown 格式的报告
        """
        stats = self.logger.get_stats(date)

        if not stats:
            return f"# NLP 执行报告\n\n日期: {date or datetime.now().strftime('%Y-%m-%d')}\n\n没有数据"

        report = f"""# NLP 执行报告

**日期**: {stats['date']}
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 总体统计

- **总执行次数**: {stats['total']}
- **成功次数**: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)
- **失败次数**: {stats['failure']} ({stats['failure']/stats['total']*100:.1f}%)
- **成功率**: {stats['success']/stats['total']*100:.1f}%

## 📈 按策略统计

| 策略 | 使用次数 | 占比 |
|------|---------|------|
"""

        for strategy, count in stats['by_strategy'].most_common():
            percentage = count / stats['total'] * 100
            report += f"| {strategy} | {count} | {percentage:.1f}% |\n"

        report += f"""
## 📍 按位置统计

| 位置 | 使用次数 | 占比 |
|------|---------|------|
"""

        for position, count in stats['by_position'].most_common():
            percentage = count / stats['total'] * 100
            report += f"| {position} | {count} | {percentage:.1f}% |\n"

        report += f"""
## 🎯 按类型统计

| 类型 | 使用次数 | 占比 |
|------|---------|------|
"""

        for elem_type, count in stats['by_type'].most_common():
            percentage = count / stats['total'] * 100
            report += f"| {elem_type} | {count} | {percentage:.1f}% |\n"

        report += f"""
## ❌ 最近失败记录

| 时间 | 描述 | 原因 |
|------|------|------|
"""

        for failure in stats['failures'][-10:]:
            report += f"| {failure['time'].split('T')[1][:8]} | {failure['description']} | {failure['reason']} |\n"

        return report

    def export_to_csv(self, output_file: str = None) -> str:
        """
        导出日志到 CSV

        Args:
            output_file: 输出文件路径

        Returns:
            输出文件路径
        """
        import csv

        if output_file is None:
            output_file = self.log_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        output_file = Path(output_file)

        # 读取所有执行日志
        records = []
        with open(self.logger.execution_log, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        if not records:
            return "没有数据可导出"

        # 写入 CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

        return str(output_file)


def main():
    """主函数 - 命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='NLP 日志分析工具')
    parser.add_argument('--log-dir', help='日志目录')
    parser.add_argument('--date', help='分析日期 (YYYY-MM-DD)')
    parser.add_argument('--export', action='store_true', help='导出为 CSV')
    parser.add_argument('--report', action='store_true', help='生成每日报告')
    parser.add_argument('--failures', type=int, default=50, help='分析的失败记录数量')

    args = parser.parse_args()

    analyzer = NLPLogAnalyzer(args.log_dir)

    if args.report:
        print("\n" + "="*60)
        print("生成每日报告")
        print("="*60 + "\n")
        report = analyzer.generate_daily_report(args.date)
        print(report)

        # 保存报告
        report_file = analyzer.log_dir / f"report_{args.date or datetime.now().strftime('%Y-%m-%d')}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")

    if args.export:
        print("\n" + "="*60)
        print("导出日志到 CSV")
        print("="*60 + "\n")
        csv_file = analyzer.export_to_csv()
        print(f"已导出到: {csv_file}")

    # 默认分析失败记录
    if not args.report and not args.export:
        print("\n" + "="*60)
        print("分析失败记录")
        print("="*60 + "\n")

        analysis = analyzer.analyze_failures(args.failures)

        print(f"📊 分析最近 {analysis['total']} 条失败记录\n")

        print("❌ 失败原因分布:")
        for reason, count in analysis['failure_reasons'].items():
            print(f"  • {reason}: {count} 次")

        print("\n📍 失败的位置分布:")
        for position, count in analysis['positions'].items():
            print(f"  • {position}: {count} 次")

        print("\n🎯 失败的类型分布:")
        for elem_type, count in analysis['types'].items():
            print(f"  • {elem_type}: {count} 次")

        print("\n🔧 优化建议:")
        suggestions = analyzer.generate_optimization_suggestions()
        if suggestions:
            for suggestion in suggestions:
                print(f"  {suggestion}")
        else:
            print("  ✅ 暂无优化建议")


if __name__ == '__main__':
    main()
