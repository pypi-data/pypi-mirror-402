"""
Android ADB 配置管理

读取和管理 Android 自动化项目的配置
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ADBConfig:
    """Android ADB 配置管理类"""

    def __init__(self, env_file: str = ".env", config_file: Optional[str] = None):
        """
        初始化 ADB 配置

        Args:
            env_file: 环境变量文件路径
            config_file: JSON 配置文件路径（可选）
        """
        # 加载环境变量
        load_dotenv(env_file)

        # ADB 路径配置
        self.adb_path = os.getenv("ADB_PATH", "adb")  # adb 命令路径
        self.adb_timeout = int(os.getenv("ADB_TIMEOUT", "30000"))  # ADB 命令超时（毫秒）

        # 设备配置
        self.device_serial = os.getenv("DEVICE_SERIAL", "")  # 设备序列号（空字符串表示使用默认设备）
        self.device_name = os.getenv("DEVICE_NAME", "default")  # 设备名称

        # 应用配置
        self.app_package = os.getenv("APP_PACKAGE", "")  # 应用包名
        self.app_activity = os.getenv("APP_ACTIVITY", "")  # 应用 Activity

        # 元素定位策略配置
        self.default_locator_strategy = os.getenv("DEFAULT_LOCATOR_STRATEGY", "id")  # 默认定位策略
        self.wait_timeout = int(os.getenv("WAIT_TIMEOUT", "10000"))  # 等待超时（毫秒）
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "500"))  # 轮询间隔（毫秒）

        # UI Automator 配置
        self.uiautomator_dump_file = os.getenv("UIAUTOMATOR_DUMP_FILE", "/sdcard/window_dump.xml")
        # UI dump 保存到项目 static 文件夹
        self.local_dump_file = os.getenv("LOCAL_DUMP_FILE", "./static/ui_dump.xml")

        # 截图配置
        self.device_screenshot_path = os.getenv("DEVICE_SCREENSHOT_PATH", "/sdcard/screenshot.png")
        self.screenshot_dir = os.getenv("SCREENSHOT_DIR", "./resources/screenshots/android")

        # 日志配置
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_dir = os.getenv("LOG_DIR", "./logs")

        # 数据目录
        self.data_dir = os.getenv("DATA_DIR", "./data")
        self.output_dir = os.getenv("OUTPUT_DIR", "./data/output")

        # 性能配置
        self.enable_performance_monitoring = os.getenv("ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true"
        self.performance_log_interval = int(os.getenv("PERFORMANCE_LOG_INTERVAL", "5000"))

        # 调试配置
        self.enable_adb_log = os.getenv("ENABLE_ADB_LOG", "true").lower() == "true"
        self.save_ui_dump_on_error = os.getenv("SAVE_UI_DUMP_ON_ERROR", "true").lower() == "true"

        # 输入配置
        self.input_delay = int(os.getenv("INPUT_DELAY", "100"))  # 输入延迟（毫秒）
        self.swipe_duration = int(os.getenv("SWIPE_DURATION", "300"))  # 滑动持续时间（毫秒）

        # 加载 JSON 配置（如果有）
        if config_file and os.path.exists(config_file):
            self.load_json_config(config_file)

        # 创建必要的目录
        self._create_directories()

    def load_json_config(self, config_file: str):
        """
        加载 JSON 配置文件

        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新配置
            for key, value in config.items():
                if hasattr(self, key):
                    setattr(self, key, value)

            logger.info(f"已加载 ADB 配置文件: {config_file}")

        except Exception as e:
            logger.warning(f"加载 ADB 配置文件失败: {e}")

    def get_adb_command(self, device_specific: bool = True) -> str:
        """
        获取 ADB 命令前缀

        Args:
            device_specific: 是否包含设备序列号

        Returns:
            ADB 命令前缀
        """
        if device_specific and self.device_serial:
            return f"{self.adb_path} -s {self.device_serial}"
        return self.adb_path

    def get_device_info(self) -> Dict[str, str]:
        """
        获取设备信息

        Returns:
            设备信息字典
        """
        return {
            "serial": self.device_serial,
            "name": self.device_name,
            "adb_path": self.adb_path,
        }

    def _create_directories(self):
        """创建必要的目录"""
        directories = [
            self.log_dir,
            self.data_dir,
            self.output_dir,
            self.screenshot_dir,
            f"{self.data_dir}/input",
        ]

        # 创建 UI dump 文件所在的目录
        local_dump_path = Path(self.local_dump_file)
        if local_dump_path.parent != Path("."):
            directories.append(str(local_dump_path.parent))

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """
        将配置转换为字典

        Returns:
            配置字典
        """
        return {
            "adb_path": self.adb_path,
            "adb_timeout": self.adb_timeout,
            "device_serial": self.device_serial,
            "device_name": self.device_name,
            "app_package": self.app_package,
            "app_activity": self.app_activity,
            "default_locator_strategy": self.default_locator_strategy,
            "wait_timeout": self.wait_timeout,
            "poll_interval": self.poll_interval,
            "uiautomator_dump_file": self.uiautomator_dump_file,
            "local_dump_file": self.local_dump_file,
            "device_screenshot_path": self.device_screenshot_path,
            "screenshot_dir": self.screenshot_dir,
            "log_level": self.log_level,
            "log_dir": self.log_dir,
            "data_dir": self.data_dir,
            "output_dir": self.output_dir,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "performance_log_interval": self.performance_log_interval,
            "enable_adb_log": self.enable_adb_log,
            "save_ui_dump_on_error": self.save_ui_dump_on_error,
            "input_delay": self.input_delay,
            "swipe_duration": self.swipe_duration,
        }

    def save_json_config(self, config_file: str):
        """
        保存配置到 JSON 文件

        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

            logger.info(f"ADB 配置已保存: {config_file}")

        except Exception as e:
            logger.error(f"保存 ADB 配置失败: {e}")

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# 全局配置实例
_global_adb_config: Optional[ADBConfig] = None


def get_adb_config() -> ADBConfig:
    """
    获取全局 ADB 配置实例

    Returns:
        ADB 配置对象
    """
    global _global_adb_config
    if _global_adb_config is None:
        _global_adb_config = ADBConfig()
    return _global_adb_config


def set_adb_config(config: ADBConfig):
    """
    设置全局 ADB 配置

    Args:
        config: ADB 配置对象
    """
    global _global_adb_config
    _global_adb_config = config


if __name__ == "__main__":
    # 测试配置
    logging.basicConfig(level=logging.INFO)

    config = ADBConfig()
    print("当前 ADB 配置:")
    print(config)

    # 保存配置
    config.save_json_config("adb_config.json")
