#!/usr/bin/env python3
"""
NLP 日志查看工具

交互式查看和分析 NLP 执行日志
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.nlp_logger import NLPExecutionLogger


class NLPLogViewer:
    """NLP 日志查看器"""

    def __init__(self, log_dir: str = None):
        """
        初始化查看器

        Args:
            log_dir: 日志目录
        """
        self.logger = NLPExecutionLogger(log_dir)
        self.log_dir = self.logger.log_dir

    def show_recent_failures(self, limit: int = 20, detailed: bool = False) -> None:
        """
        显示最近的失败记录

        Args:
            limit: 显示数量
            detailed: 是否显示详细信息
        """
        failures = self.logger.get_recent_failures(limit)

        if not failures:
            print("✅ 没有失败记录")
            return

        print(f"\n❌ 最近的 {len(failures)} 条失败记录:\n")

        for i, failure in enumerate(failures, 1):
            print(f"{i}. [{failure['timestamp']}] {failure['user_description']}")

            if detailed:
                print(f"   失败原因: {failure['failure_reason']}")
                print(f"   尝试策略: {', '.join(failure['strategies_tried'])}")
                print(f"   候选数量: {failure['candidates_found']}")

                parsed = failure['parsed_result']
                if parsed.get('position'):
                    print(f"   位置: {parsed['position']}")
                if parsed.get('type'):
                    print(f"   类型: {parsed['type']}")

                if failure.get('screenshot_path'):
                    print(f"   截图: {failure['screenshot_path']}")

            print()

    def show_failure_detail(self, index: int) -> None:
        """
        显示失败记录的详细信息

        Args:
            index: 记录索引（从1开始）
        """
        failures = self.logger.get_recent_failures(100)

        if index < 1 or index > len(failures):
            print(f"❌ 索引超出范围 (1-{len(failures)})")
            return

        failure = failures[index - 1]

        print(f"\n{'='*60}")
        print(f"失败记录 #{index}")
        print(f"{'='*60}\n")

        print(f"⏰ 时间: {failure['timestamp']}")
        print(f"📱 设备: {failure['device_id']}")
        print(f"💬 描述: {failure['user_description']}")

        print(f"\n📋 解析结果:")
        parsed = failure['parsed_result']
        print(f"  • 动作: {parsed.get('action', 'N/A')}")
        print(f"  • 位置: {parsed.get('position', 'N/A')}")
        print(f"  • 类型: {parsed.get('type', 'N/A')}")
        print(f"  • 文本: {parsed.get('text', 'N/A')}")
        print(f"  • 描述: {parsed.get('description', 'N/A')}")

        print(f"\n🔍 执行过程:")
        print(f"  • 尝试策略: {', '.join(failure['strategies_tried'])}")
        print(f"  • 候选数量: {failure['candidates_found']}")
        print(f"  • 选中索引: {failure['selected_index']}")

        print(f"\n⏱ 性能:")
        print(f"  • 解析耗时: {failure['parse_time_ms']:.2f} ms")
        print(f"  • 查找耗时: {failure['search_time_ms']:.2f} ms")
        print(f"  • 总耗时: {failure['total_time_ms']:.2f} ms")

        print(f"\n🎯 结果:")
        print(f"  • 成功: {'✅' if failure['success'] else '❌'}")
        print(f"  • 置信度: {failure['confidence']:.2f}")
        print(f"  • 失败原因: {failure['failure_reason']}")

        if failure.get('screenshot_path'):
            print(f"  • 截图: {failure['screenshot_path']}")

        if failure.get('ui_elements_count'):
            print(f"  • UI 元素数: {failure['ui_elements_count']}")

    def show_stats(self, date: str = None) -> None:
        """
        显示统计数据

        Args:
            date: 日期（YYYY-MM-DD），默认为今天
        """
        stats = self.logger.get_stats(date)

        if not stats:
            print(f"❌ 没有找到 {date or '今天'} 的统计数据")
            return

        print(f"\n{'='*60}")
        print(f"📊 统计数据 - {stats['date']}")
        print(f"{'='*60}\n")

        print(f"总执行次数: {stats['total']}")
        print(f"成功次数: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        print(f"失败次数: {stats['failure']} ({stats['failure']/stats['total']*100:.1f}%)")

        print(f"\n按策略统计:")
        for strategy, count in stats['by_strategy'].most_common():
            percentage = count / stats['total'] * 100
            bar = '█' * int(percentage / 5)
            print(f"  {strategy:15s}: {count:3d} ({percentage:5.1f}%) {bar}")

        print(f"\n按位置统计:")
        for position, count in stats['by_position'].most_common():
            percentage = count / stats['total'] * 100
            bar = '█' * int(percentage / 5)
            print(f"  {position:10s}: {count:3d} ({percentage:5.1f}%) {bar}")

        print(f"\n按类型统计:")
        for elem_type, count in stats['by_type'].most_common():
            percentage = count / stats['total'] * 100
            bar = '█' * int(percentage / 5)
            print(f"  {elem_type:10s}: {count:3d} ({percentage:5.1f}%) {bar}")

    def search_logs(self, keyword: str, limit: int = 20) -> None:
        """
        搜索日志

        Args:
            keyword: 搜索关键词
            limit: 返回数量
        """
        keyword_lower = keyword.lower()

        # 搜索执行日志
        matches = []
        with open(self.logger.execution_log, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                record = json.loads(line)
                # 搜索描述
                if keyword_lower in record['user_description'].lower():
                    matches.append(record)
                    if len(matches) >= limit:
                        break
                # 搜索失败原因
                elif keyword_lower in record['failure_reason'].lower():
                    matches.append(record)
                    if len(matches) >= limit:
                        break

        if not matches:
            print(f"❌ 没有找到包含 '{keyword}' 的记录")
            return

        print(f"\n🔍 找到 {len(matches)} 条匹配 '{keyword}' 的记录:\n")

        for i, match in enumerate(matches, 1):
            status = "✅" if match['success'] else "❌"
            print(f"{i}. {status} [{match['timestamp']}] {match['user_description']}")

            if not match['success']:
                print(f"   原因: {match['failure_reason']}")

    def interactive_mode(self):
        """交互式查看模式"""
        print("\n" + "="*60)
        print("NLP 日志查看器 - 交互式模式")
        print("="*60)

        print("\n可用命令:")
        print("  failures [数量]    - 查看失败记录")
        print("  detail <索引>      - 查看记录详情")
        print("  stats [日期]       - 查看统计数据")
        print("  search <关键词>    - 搜索日志")
        print("  help              - 显示帮助")
        print("  quit/exit         - 退出")

        print("\n示例:")
        print("  failures 10       - 查看最近10条失败记录")
        print("  detail 1          - 查看第1条记录的详情")
        print("  stats 2024-01-15  - 查看2024-01-15的统计")
        print("  search 设置       - 搜索包含'设置'的记录")

        print("\n")

        while True:
            try:
                cmd = input("log-viewer> ").strip()

                if not cmd:
                    continue

                if cmd.lower() in ['quit', 'exit', 'q']:
                    print("\n退出查看器")
                    break

                if cmd.lower() == 'help':
                    print("\n可用命令:")
                    print("  failures [数量]    - 查看失败记录")
                    print("  detail <索引>      - 查看记录详情")
                    print("  stats [日期]       - 查看统计数据")
                    print("  search <关键词>    - 搜索日志")
                    print("  quit              - 退出")
                    continue

                parts = cmd.split()
                command = parts[0].lower()

                if command == 'failures':
                    limit = int(parts[1]) if len(parts) > 1 else 20
                    self.show_recent_failures(limit, detailed=False)

                elif command == 'detail':
                    if len(parts) < 2:
                        print("❌ 请提供记录索引，例如: detail 1")
                        continue
                    index = int(parts[1])
                    self.show_failure_detail(index)

                elif command == 'stats':
                    date = parts[1] if len(parts) > 1 else None
                    self.show_stats(date)

                elif command == 'search':
                    if len(parts) < 2:
                        print("❌ 请提供搜索关键词，例如: search 设置")
                        continue
                    keyword = ' '.join(parts[1:])
                    self.search_logs(keyword)

                else:
                    print(f"❌ 未知命令: {command}")
                    print("   输入 'help' 查看可用命令")

            except KeyboardInterrupt:
                print("\n\n退出查看器")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='NLP 日志查看工具')
    parser.add_argument('--log-dir', help='日志目录')
    parser.add_argument('--failures', type=int, default=20,
                       help='查看最近的失败记录数量')
    parser.add_argument('--detail', type=int,
                       help='查看指定索引的记录详情')
    parser.add_argument('--stats', nargs='?', const='today',
                       help='查看统计数据（可选日期 YYYY-MM-DD）')
    parser.add_argument('--search', type=str,
                       help='搜索关键词')
    parser.add_argument('--interactive', action='store_true',
                       help='进入交互式模式')

    args = parser.parse_args()

    viewer = NLPLogViewer(args.log_dir)

    if args.interactive:
        viewer.interactive_mode()

    elif args.failures:
        viewer.show_recent_failures(args.failures, detailed=False)

    elif args.detail:
        viewer.show_failure_detail(args.detail)

    elif args.stats:
        date = None if args.stats == 'today' else args.stats
        viewer.show_stats(date)

    elif args.search:
        viewer.search_logs(args.search)

    else:
        # 默认显示最近10条失败记录
        viewer.show_recent_failures(10, detailed=False)


if __name__ == '__main__':
    main()
