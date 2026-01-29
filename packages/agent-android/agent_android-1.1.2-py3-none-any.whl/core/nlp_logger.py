"""
NLP 执行日志记录器

记录所有 NLP 元素查找的执行过程，特别是失败的记录，
用于后续分析和优化。
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class NLPExecutionRecord:
    """NLP 执行记录"""
    # 基本信息
    execution_id: str              # 执行唯一ID
    timestamp: str                 # 时间戳
    device_id: str                 # 设备ID

    # 输入
    user_description: str          # 用户原始描述
    parsed_result: Dict[str, Any]  # 解析结果

    # 执行过程
    strategies_tried: List[str]    # 尝试的查找策略
    candidates_found: int          # 找到的候选数量
    selected_index: int            # 选择的候选索引（-1表示未选择）

    # 结果
    success: bool                  # 是否成功
    failure_reason: str            # 失败原因
    confidence: float              # 置信度 (0-1)

    # 性能
    parse_time_ms: float           # 解析耗时
    search_time_ms: float          # 查找耗时
    total_time_ms: float           # 总耗时

    # 额外信息
    ui_elements_count: int         # UI 元素总数
    screenshot_path: str           # 截图路径（失败时）
    error_message: str             # 错误消息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class NLPExecutionLogger:
    """NLP 执行日志记录器"""

    def __init__(self, log_dir: str = None):
        """
        初始化日志记录器

        Args:
            log_dir: 日志目录，默认为 logs/nlp_logs/
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / "nlp_logs"
        else:
            log_dir = Path(log_dir)

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 日志文件路径
        self.execution_log = self.log_dir / "nlp_execution.log"
        self.failure_log = self.log_dir / "nlp_failure.log"
        self.daily_stats_dir = self.log_dir / "daily_stats"
        self.daily_stats_dir.mkdir(exist_ok=True)

        # 确保日志文件存在
        self.execution_log.touch(exist_ok=True)
        self.failure_log.touch(exist_ok=True)

    def log_execution(self, record: NLPExecutionRecord) -> None:
        """
        记录一次执行

        Args:
            record: 执行记录
        """
        try:
            # 转换为 JSON
            log_entry = json.dumps(record.to_dict(), ensure_ascii=False)

            # 写入执行日志
            with open(self.execution_log, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')

            # 如果失败，额外写入失败日志
            if not record.success:
                with open(self.failure_log, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')

            # 更新每日统计
            self._update_daily_stats(record)

            logger.debug(f"记录执行日志: {record.execution_id}")

        except Exception as e:
            logger.error(f"写入日志失败: {e}")

    def _update_daily_stats(self, record: NLPExecutionRecord) -> None:
        """
        更新每日统计

        Args:
            record: 执行记录
        """
        try:
            # 获取日期字符串
            date_str = datetime.fromisoformat(record.timestamp).strftime('%Y-%m-%d')
            stats_file = self.daily_stats_dir / f"{date_str}.json"

            # 读取或创建统计
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
            else:
                stats = {
                    'date': date_str,
                    'total': 0,
                    'success': 0,
                    'failure': 0,
                    'by_strategy': {},
                    'by_position': {},
                    'by_type': {},
                    'failures': []
                }

            # 更新统计
            stats['total'] += 1
            if record.success:
                stats['success'] += 1
            else:
                stats['failure'] += 1
                # 记录失败详情（只保留最近100条）
                failure_summary = {
                    'time': record.timestamp,
                    'description': record.user_description,
                    'reason': record.failure_reason,
                    'strategies': record.strategies_tried
                }
                stats['failures'].append(failure_summary)
                if len(stats['failures']) > 100:
                    stats['failures'].pop(0)

            # 按策略统计
            for strategy in record.strategies_tried:
                stats['by_strategy'][strategy] = stats['by_strategy'].get(strategy, 0) + 1

            # 按位置统计
            position = record.parsed_result.get('position', 'unknown')
            if position:
                stats['by_position'][position] = stats['by_position'].get(position, 0) + 1

            # 按类型统计
            elem_type = record.parsed_result.get('type', 'unknown')
            if elem_type:
                stats['by_type'][elem_type] = stats['by_type'].get(elem_type, 0) + 1

            # 写回文件
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"更新统计失败: {e}")

    def get_recent_failures(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的失败记录

        Args:
            limit: 返回数量

        Returns:
            失败记录列表
        """
        try:
            failures = []
            with open(self.failure_log, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        failures.append(json.loads(line))
                        if len(failures) >= limit:
                            break

            return failures[::-1]  # 反序返回

        except Exception as e:
            logger.error(f"读取失败日志: {e}")
            return []

    def get_stats(self, date: str = None) -> Optional[Dict[str, Any]]:
        """
        获取统计数据

        Args:
            date: 日期字符串（YYYY-MM-DD），默认为今天

        Returns:
            统计数据字典
        """
        try:
            if date is None:
                date = datetime.now().strftime('%Y-%m-%d')

            stats_file = self.daily_stats_dir / f"{date}.json"

            if not stats_file.exists():
                return None

            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"读取统计数据: {e}")
            return None

    def clear_old_logs(self, days: int = 30) -> int:
        """
        清理旧日志

        Args:
            days: 保留天数

        Returns:
            删除的文件数
        """
        try:
            import time
            cutoff_time = time.time() - (days * 24 * 3600)
            deleted_count = 0

            # 清理旧统计文件
            for stats_file in self.daily_stats_dir.glob("*.json"):
                if stats_file.stat().st_mtime < cutoff_time:
                    stats_file.unlink()
                    deleted_count += 1

            logger.info(f"清理了 {deleted_count} 个旧日志文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理日志失败: {e}")
            return 0


# 便捷函数
def create_execution_record(
    device_id: str,
    user_description: str,
    parsed_result: Dict[str, Any],
    success: bool,
    failure_reason: str = "",
    **kwargs
) -> NLPExecutionRecord:
    """
    创建执行记录的便捷函数

    Args:
        device_id: 设备ID
        user_description: 用户描述
        parsed_result: 解析结果
        success: 是否成功
        failure_reason: 失败原因
        **kwargs: 其他字段

    Returns:
        NLPExecutionRecord 对象
    """
    return NLPExecutionRecord(
        execution_id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        device_id=device_id,
        user_description=user_description,
        parsed_result=parsed_result,
        strategies_tried=kwargs.get('strategies_tried', []),
        candidates_found=kwargs.get('candidates_found', 0),
        selected_index=kwargs.get('selected_index', -1),
        success=success,
        failure_reason=failure_reason,
        confidence=kwargs.get('confidence', 0.0),
        parse_time_ms=kwargs.get('parse_time_ms', 0.0),
        search_time_ms=kwargs.get('search_time_ms', 0.0),
        total_time_ms=kwargs.get('total_time_ms', 0.0),
        ui_elements_count=kwargs.get('ui_elements_count', 0),
        screenshot_path=kwargs.get('screenshot_path', ''),
        error_message=kwargs.get('error_message', '')
    )


if __name__ == '__main__':
    # 测试代码
    logger_instance = NLPExecutionLogger()

    # 创建测试记录
    test_record = create_execution_record(
        device_id="emulator-5554",
        user_description="点击右上角的设置按钮",
        parsed_result={
            'action': '点击',
            'position': '右上',
            'type': '按钮',
            'description': '设置'
        },
        success=False,
        failure_reason="未找到匹配的图标",
        strategies_tried=["text", "description", "position+type"],
        candidates_found=0,
        parse_time_ms=5.2,
        search_time_ms=350.8,
        total_time_ms=356.0
    )

    # 记录
    logger_instance.log_execution(test_record)

    # 读取失败记录
    failures = logger_instance.get_recent_failures(limit=5)
    print(f"\n最近的失败记录 ({len(failures)} 条):")
    for failure in failures:
        print(f"- {failure['timestamp']}: {failure['user_description']}")
        print(f"  原因: {failure['failure_reason']}")

    # 获取统计
    stats = logger_instance.get_stats()
    if stats:
        print(f"\n今日统计:")
        print(f"  总计: {stats['total']}")
        print(f"  成功: {stats['success']}")
        print(f"  失败: {stats['failure']}")
        print(f"  成功率: {stats['success']/stats['total']*100:.1f}%")
