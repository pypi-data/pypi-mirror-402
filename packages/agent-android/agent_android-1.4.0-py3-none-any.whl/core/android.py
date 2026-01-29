"""
Android ADB 设备管理

提供 Android 设备的 ADB 连接、操作和管理功能
"""

import os
import time
import logging
import subprocess
import xml.etree.ElementTree as ET
import threading
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

# 支持相对导入和绝对导入（兼容模块加载器）
try:
    from .adb_config import ADBConfig
except ImportError:
    from adb_config import ADBConfig

logger = logging.getLogger(__name__)


class AndroidDeviceManager:
    """Android 设备管理类（对标 PlaywrightBrowserManager）"""

    # 用于快速字符串比较的真值集合
    TRUE_VALUES = {'true', 'True', '1', 'yes'}

    def __init__(self, config: Optional[ADBConfig] = None, auto_refresh_ui: bool = True):
        """
        初始化 Android 设备管理器

        Args:
            config: ADB 配置对象
            auto_refresh_ui: 是否在操作后自动刷新 UI dump（默认 True）
        """
        self.config = config or ADBConfig()
        self.device_id: Optional[str] = None
        self.device_info: Dict[str, Any] = {}
        self.current_app: Optional[str] = None
        self._ui_dump_cache: Optional[ET.Element] = None
        self._ui_dump_list_cache: Optional[list] = None
        self._optimized_ui_dump_cache: Optional[list] = None  # 优化后的 UI dump 缓存
        self._cache_version: int = 0
        self._connected = False

        # UI dump 优化器（延迟加载）
        self._optimizer = None

        # 自动刷新 UI dump 配置
        self._auto_refresh_ui = auto_refresh_ui
        self._refresh_thread: Optional[threading.Thread] = None
        self._refresh_lock = threading.Lock()
        self._pending_refresh = False

    def _get_optimizer(self):
        """获取 UI dump 优化器实例"""
        if self._optimizer is None:
            try:
                # 尝试从 core.utils 导入优化器
                import sys
                from pathlib import Path
                # 添加项目路径
                project_root = Path(__file__).parent.parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                from core.utils.ui_dump_optimizer import get_optimizer
                self._optimizer = get_optimizer()  # 使用默认 max_depth=10
                logger.info("UI dump 优化器已加载")
            except ImportError:
                logger.warning("无法导入 UI dump 优化器，使用未优化的数据")
                self._optimizer = None
        return self._optimizer

    def _auto_refresh_ui_dump_background(self, wait_time: float = 1.0):
        """
        后台自动刷新和优化 UI dump

        Args:
            wait_time: 等待时间（秒），让 UI 渲染完成
        """
        def refresh_task():
            try:
                # 等待 UI 渲染
                if wait_time > 0:
                    logger.debug(f"⏳ 等待 UI 渲染: {wait_time:.1f} 秒")
                    time.sleep(wait_time)

                # 获取稳定的 UI dump
                logger.debug("🔄 开始后台刷新 UI dump")
                xml_root = self.get_ui_dump(force_refresh=True, wait_for_stable=True)

                if xml_root is not None:
                    # 触发优化器更新
                    optimizer = self._get_optimizer()
                    if optimizer and self.device_id:
                        # 检查是否需要重新优化
                        if self.device_id not in optimizer.cache:
                            logger.debug("🔄 触发 UI dump 优化")
                            optimized = optimizer.optimize_dump(xml_root, self.device_id)
                            logger.debug(f"✅ 后台优化完成: {len(optimized)} 个元素")
                        else:
                            logger.debug("✅ 使用缓存优化数据")
                    logger.debug("✅ 后台 UI dump 刷新完成")
                else:
                    logger.warning("⚠️ 后台 UI dump 刷新失败")

            except Exception as e:
                logger.warning(f"⚠️ 后台刷新 UI dump 失败: {e}")
            finally:
                with self._refresh_lock:
                    self._pending_refresh = False

        # 启动后台线程
        with self._refresh_lock:
            if self._pending_refresh:
                logger.debug("⏸️ 已有刷新任务在执行，跳过")
                return

            self._pending_refresh = True
            self._refresh_thread = threading.Thread(
                target=refresh_task,
                name=f"UIRefresh-{self.device_id}",
                daemon=True
            )
            self._refresh_thread.start()
            logger.debug(f"🚀 已启动后台 UI dump 刷新任务 (等待 {wait_time:.1f}s)")

    def _schedule_auto_refresh(self, wait_time: float = 1.0):
        """
        调度自动刷新 UI dump（在操作后调用）

        Args:
            wait_time: 等待时间（秒）
        """
        if not self._auto_refresh_ui:
            return

        if not self._connected:
            return

        # 异步刷新，不阻塞主流程
        self._auto_refresh_ui_dump_background(wait_time)

    def wait_auto_refresh_complete(self, timeout: float = 5.0) -> bool:
        """
        等待后台自动刷新完成

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否在超时前完成
        """
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            return True

        try:
            self._refresh_thread.join(timeout=timeout)
            return not self._refresh_thread.is_alive()
        except Exception as e:
            logger.warning(f"等待刷新完成失败: {e}")
            return False

    def connect(self, device_serial: Optional[str] = None) -> 'AndroidDeviceManager':
        """
        连接到 Android 设备

        Args:
            device_serial: 设备序列号（可选，默认使用配置中的序列号）

        Returns:
            自身，支持链式调用
        """
        # 使用传入的设备序列号或配置中的序列号
        target_device = device_serial or self.config.device_serial

        if target_device:
            # 连接到指定设备
            self.device_id = target_device
            logger.info(f"连接到设备: {target_device}")
        else:
            # 自动获取第一个可用设备
            devices = self.list_devices()
            if not devices:
                raise RuntimeError("没有可用的 Android 设备")

            self.device_id = devices[0]
            logger.info(f"自动连接到设备: {self.device_id}")

        # 验证设备连接
        if not self._check_device_connection():
            raise RuntimeError(f"无法连接到设备: {self.device_id}")

        # 获取设备信息
        self._fetch_device_info()

        self._connected = True
        logger.info(f"设备已连接: {self.device_id} ({self.device_info.get('model', 'Unknown')})")

        return self

    def disconnect(self):
        """断开设备连接"""
        if self._connected:
            logger.info(f"断开设备连接: {self.device_id}")
            self._connected = False
            self.device_id = None
            self.current_app = None
            self._ui_dump_cache = None
            self._ui_dump_list_cache = None
            self._cache_version = 0

    def list_devices(self) -> List[str]:
        """
        列出所有已连接的设备

        Returns:
            设备序列号列表
        """
        try:
            result = subprocess.run(
                [self.config.adb_path, "devices"],
                capture_output=True,
                text=True,
                timeout=self.config.adb_timeout // 1000
            )

            devices = []
            for line in result.stdout.strip().split('\n')[1:]:
                if '\tdevice' in line:
                    serial = line.split('\t')[0]
                    devices.append(serial)

            return devices

        except Exception as e:
            logger.error(f"列出设备失败: {e}")
            return []

    def get_device(self) -> 'AndroidDeviceManager':
        """
        获取设备实例（如果未连接则自动连接）

        Returns:
            设备管理器实例
        """
        if not self._connected:
            self.connect()

        return self

    def _check_device_connection(self) -> bool:
        """
        检查设备是否已连接

        Returns:
            是否已连接
        """
        try:
            result = self._execute_adb_command(["shell", "echo", "connected"])
            return result is not None
        except Exception as e:
            logger.error(f"检查设备连接失败: {e}")
            return False

    def _fetch_device_info(self):
        """获取设备信息"""
        try:
            # 获取设备属性
            properties = {
                "ro.product.model": "model",
                "ro.product.manufacturer": "manufacturer",
                "ro.build.version.release": "android_version",
                "ro.product.cpu.abi": "cpu_abi",
            }

            for prop, key in properties.items():
                value = self._execute_adb_command(["shell", "getprop", prop])
                if value:
                    self.device_info[key] = value.strip()

        except Exception as e:
            logger.error(f"获取设备信息失败: {e}")

    def _execute_adb_command(
        self,
        command: List[str],
        timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        执行 ADB 命令

        Args:
            command: 命令列表
            timeout: 超时时间（毫秒）

        Returns:
            命令输出
        """
        try:
            # 构建完整的 ADB 命令
            full_command = [self.config.adb_path]
            if self.device_id:
                full_command.extend(["-s", self.device_id])
            full_command.extend(command)

            # 记录命令（如果启用日志）
            if self.config.enable_adb_log:
                logger.debug(f"执行 ADB 命令: {' '.join(full_command)}")

            # 执行命令
            timeout_sec = (timeout or self.config.adb_timeout) // 1000
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )

            if result.returncode != 0:
                logger.error(f"ADB 命令失败: {result.stderr}")
                return None

            return result.stdout

        except subprocess.TimeoutExpired:
            logger.error(f"ADB 命令超时: {' '.join(command)}")
            return None
        except Exception as e:
            logger.error(f"执行 ADB 命令出错: {e}")
            return None

    def screenshot(self, path: str) -> bool:
        """
        截图

        Args:
            path: 截图保存路径

        Returns:
            是否成功
        """
        if not self._connected:
            logger.error("设备未连接，无法截图")
            return False

        try:
            # 确保目录存在
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            # 在设备上截图
            device_path = self.config.device_screenshot_path
            result = self._execute_adb_command(["shell", "screencap", "-p", device_path])

            if result is None:
                logger.error("设备截图失败")
                return False

            # 拉取截图文件到本地
            result = self._execute_adb_command(["pull", device_path, path])

            if result is None:
                logger.error("拉取截图文件失败")
                return False

            # 删除设备上的截图文件
            self._execute_adb_command(["shell", "rm", device_path])

            logger.info(f"截图已保存: {path}")
            return True

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return False

    def tap(self, x: int, y: int) -> bool:
        """
        点击屏幕

        Args:
            x: X 坐标
            y: Y 坐标

        Returns:
            是否成功
        """
        if not self._connected:
            logger.error("设备未连接，无法点击屏幕")
            return False

        if x < 0 or y < 0:
            logger.error(f"点击坐标不能为负数: ({x}, {y})")
            return False

        try:
            time.sleep(self.config.input_delay / 1000)
            result = self._execute_adb_command(["shell", "input", "tap", str(x), str(y)])

            # 自动刷新 UI dump（后台异步）
            if result is not None:
                self._schedule_auto_refresh(wait_time=1.0)

            return result is not None
        except Exception as e:
            logger.error(f"点击失败 ({x}, {y}): {e}")
            return False

    def swipe(
        self,
        x1: int, y1: int,
        x2: int, y2: int,
        duration: Optional[int] = None
    ) -> bool:
        """
        滑动屏幕

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            duration: 滑动持续时间（毫秒）

        Returns:
            是否成功
        """
        try:
            duration = duration or self.config.swipe_duration
            time.sleep(self.config.input_delay / 1000)
            result = self._execute_adb_command([
                "shell", "input", "swipe",
                str(x1), str(y1), str(x2), str(y2), str(duration)
            ])

            # 自动刷新 UI dump（后台异步）
            if result is not None:
                self._schedule_auto_refresh(wait_time=1.5)

            return result is not None
        except Exception as e:
            logger.error(f"滑动失败: {e}")
            return False

    def input_text(self, text: str) -> bool:
        """
        输入文本

        Args:
            text: 要输入的文本

        Returns:
            是否成功
        """
        if not self._connected:
            logger.error("设备未连接，无法输入文本")
            return False

        try:
            # 转义 shell 特殊字符
            # 注意：这些字符需要根据实际情况转义
            escape_map = {
                ' ': '%s',      # 空格
                '&': '\\&',     # & 符号
                '|': '\\|',     # 管道符
                ';': '\\;',     # 分号
                '<': '\\<',     # 小于号
                '>': '\\>',     # 大于号
                '(': '\\(',     # 左括号
                ')': '\\)',     # 右括号
                '$': '\\$',     # 美元符
                '`': '\\`',     # 反引号
                '\\': '\\\\',   # 反斜杠
                '"': '\\"',     # 双引号
                "'": "\\'",     # 单引号
            }

            escaped_text = text
            for char, escaped in escape_map.items():
                escaped_text = escaped_text.replace(char, escaped)

            time.sleep(self.config.input_delay / 1000)
            result = self._execute_adb_command(["shell", "input", "text", escaped_text])

            # 自动刷新 UI dump（后台异步）
            if result is not None:
                self._schedule_auto_refresh(wait_time=0.5)

            return result is not None
        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return False

    def press_key(self, keycode: int) -> bool:
        """
        按下按键

        Args:
            keycode: 按键代码（如 3 = HOME, 4 = BACK）

        Returns:
            是否成功
        """
        try:
            time.sleep(self.config.input_delay / 1000)
            result = self._execute_adb_command(["shell", "input", "keyevent", str(keycode)])

            # 自动刷新 UI dump（后台异步）
            if result is not None:
                self._schedule_auto_refresh(wait_time=1.0)

            return result is not None
        except Exception as e:
            logger.error(f"按键失败 (keycode={keycode}): {e}")
            return False

    def press_back(self) -> bool:
        """按下返回键"""
        return self.press_key(4)

    def press_home(self) -> bool:
        """按下 Home 键"""
        return self.press_key(3)

    def press_enter(self) -> bool:
        """按下 Enter 键"""
        return self.press_key(66)

    def press_recent(self) -> bool:
        """按下最近应用键 (APP_SWITCH)"""
        return self.press_key(187)

    def start_app(self, package: str, activity: Optional[str] = None) -> bool:
        """
        启动应用

        Args:
            package: 应用包名
            activity: 应用 Activity（可选）

        Returns:
            是否成功
        """
        try:
            if activity:
                component = f"{package}/{activity}"
            else:
                # 使用 monkey 命令启动应用
                result = self._execute_adb_command([
                    "shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"
                ])
                return result is not None

            result = self._execute_adb_command(["shell", "am", "start", "-n", component])
            if result:
                self.current_app = package
                logger.info(f"应用已启动: {package}")
                return True

            return False

        except Exception as e:
            logger.error(f"启动应用失败 ({package}): {e}")
            return False

    def stop_app(self, package: str) -> bool:
        """
        停止应用

        Args:
            package: 应用包名

        Returns:
            是否成功
        """
        try:
            result = self._execute_adb_command(["shell", "am", "force-stop", package])
            if result and package == self.current_app:
                self.current_app = None
                logger.info(f"应用已停止: {package}")
                return True

            return False

        except Exception as e:
            logger.error(f"停止应用失败 ({package}): {e}")
            return False

    def clear_app_data(self, package: str) -> bool:
        """
        清除应用数据

        Args:
            package: 应用包名

        Returns:
            是否成功
        """
        try:
            result = self._execute_adb_command(["shell", "pm", "clear", package])
            return result is not None
        except Exception as e:
            logger.error(f"清除应用数据失败 ({package}): {e}")
            return False

    def get_ui_dump(self, force_refresh: bool = False, wait_for_stable: bool = True, max_retries: int = 3, stable_threshold: int = 2) -> Optional[ET.Element]:
        """
        获取 UI 层级结构，支持等待 XML 完全加载和稳定

        Args:
            force_refresh: 是否强制刷新
            wait_for_stable: 是否等待 XML 稳定（推荐）
            max_retries: 最大重试次数（默认3次）
            stable_threshold: 稳定性阈值，连续N次获取内容一致即认为稳定（默认2次）

        Returns:
            XML 根元素
        """
        if not force_refresh and self._ui_dump_cache is not None:
            return self._ui_dump_cache

        # 如果不等待稳定，使用原有逻辑
        if not wait_for_stable:
            return self._get_ui_dump_once()

        # 等待 XML 稳定的逻辑
        return self._get_ui_dump_stable(max_retries, stable_threshold)

    def _get_ui_dump_once(self) -> Optional[ET.Element]:
        """
        获取一次 UI dump（不等待稳定）

        Returns:
            XML 根元素
        """
        try:
            # 执行 uiautomator dump
            device_dump_file = self.config.uiautomator_dump_file
            local_dump_file = self.config.local_dump_file

            # 在设备上生成 UI dump
            result = self._execute_adb_command(["shell", "uiautomator", "dump", device_dump_file])

            if result is None:
                logger.error("UI dump 生成失败")
                return None

            # 拉取 UI dump 文件到本地
            result = self._execute_adb_command(["pull", device_dump_file, local_dump_file])

            if result is None:
                logger.error("拉取 UI dump 文件失败")
                return None

            # 解析 XML
            tree = ET.parse(local_dump_file)
            root = tree.getroot()

            # 更新缓存
            self._update_ui_dump_cache(root)

            return root

        except Exception as e:
            logger.error(f"获取 UI dump 失败: {e}")
            return None

    def _get_ui_dump_stable(self, max_retries: int, stable_threshold: int) -> Optional[ET.Element]:
        """
        获取稳定的 UI dump（多次尝试确保完全加载）

        Args:
            max_retries: 最大重试次数
            stable_threshold: 稳定性阈值

        Returns:
            XML 根元素
        """
        import time
        import hashlib

        device_dump_file = self.config.uiautomator_dump_file
        local_dump_file = self.config.local_dump_file

        previous_hash = None
        stable_count = 0

        for attempt in range(max_retries):
            try:
                # 等待一小段时间让 UI 渲染
                if attempt > 0:
                    wait_time = 0.5 * (attempt + 1)  # 递增等待时间
                    logger.debug(f"等待 UI 渲染: {wait_time:.1f} 秒 (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)

                # 在设备上生成 UI dump
                result = self._execute_adb_command(["shell", "uiautomator", "dump", device_dump_file])

                if result is None:
                    logger.warning(f"UI dump 生成失败 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return None

                # 拉取 UI dump 文件到本地
                result = self._execute_adb_command(["pull", device_dump_file, local_dump_file])

                if result is None:
                    logger.warning(f"拉取 UI dump 文件失败 (尝试 {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return None

                # 读取文件内容计算哈希
                with open(local_dump_file, 'rb') as f:
                    content = f.read()
                    current_hash = hashlib.md5(content).hexdigest()

                # 检查是否稳定
                if previous_hash is not None and current_hash == previous_hash:
                    stable_count += 1
                    logger.debug(f"UI dump 稳定计数: {stable_count}/{stable_threshold}")
                else:
                    stable_count = 0
                    previous_hash = current_hash
                    logger.debug(f"UI dump 变化，哈希: {current_hash[:8]}...")

                # 如果达到稳定阈值，认为已完全加载
                if stable_count >= stable_threshold:
                    logger.info(f"✅ UI dump 已稳定 (连续 {stable_count} 次一致)")
                    break

            except Exception as e:
                logger.warning(f"获取 UI dump 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    continue

        # 解析最终的 XML
        try:
            tree = ET.parse(local_dump_file)
            root = tree.getroot()

            # 验证 XML 是否有效（至少有一些节点）
            node_count = len(list(root.iter()))
            if node_count < 10:
                logger.warning(f"UI dump 节点数过少: {node_count}，可能未完全加载")

            # 更新缓存
            self._update_ui_dump_cache(root)

            logger.info(f"UI dump 加载完成: {node_count} 个节点 (尝试 {attempt + 1}/{max_retries})")
            return root

        except Exception as e:
            logger.error(f"解析 UI dump 失败: {e}")
            return None

    def _update_ui_dump_cache(self, root: ET.Element):
        """
        更新 UI dump 缓存

        Args:
            root: XML 根节点
        """
        self._ui_dump_cache = root

        # 更新缓存版本号，标记列表缓存失效
        self._cache_version += 1
        self._ui_dump_list_cache = None
        self._optimized_ui_dump_cache = None  # 标记优化缓存失效

        # 同步更新优化器缓存
        optimizer = self._get_optimizer()
        if optimizer and self.device_id:
            try:
                optimizer.update_xml_cache(self.device_id, self._ui_dump_cache)
                logger.info(f"已同步更新优化缓存: device_id={self.device_id}")
            except Exception as e:
                logger.warning(f"更新优化缓存失败: {e}")

    def get_ui_dump_list(self, force_refresh: bool = False, include_xml_node: bool = False, use_optimized: bool = True) -> list:
        """
        获取 UI 层级结构并解析为元素列表

        返回元素字典列表，适合用于 IconHelper 等需要 dict list 的场景。
        优先使用优化后的 UI dump（移除无用节点，保留有用元素）。

        Args:
            force_refresh: 是否强制刷新
            include_xml_node: 是否包含原始 XML 节点引用（默认 False，避免 JSON 序列化问题）
            use_optimized: 是否使用优化后的数据（默认 True）

        Returns:
            元素列表，每个元素是一个字典包含属性信息
            格式: [
                {
                    'node_id': '0.1.2',  # 节点 ID（用于缓存）
                    'parent_id': '0.1',  # 父节点 ID
                    'tag': 'node',
                    'resource_id': 'com.example:id/button',
                    'text': '按钮文本',
                    'class': 'android.widget.Button',
                    'bounds': '[100,200][300,400]',
                    'clickable': True,
                    'enabled': True,
                    'content_desc': '按钮描述',
                    'center': {'x': 200, 'y': 300},  # 中心点坐标
                    'depth': 2,  # 深度
                    ...
                },
                ...
            ]
        """
        # 如果需要 xml_node，必须使用未优化的版本
        if include_xml_node:
            use_optimized = False

        # 优先使用优化缓存
        if use_optimized and not force_refresh:
            optimizer = self._get_optimizer()
            if optimizer and self.device_id:
                # 检查优化缓存
                if self.device_id in optimizer.cache:
                    logger.info(f"使用优化缓存: device_id={self.device_id}")
                    return optimizer.cache[self.device_id]

                # 没有优化缓存，尝试生成
                xml_root = self.get_ui_dump(force_refresh=False)
                if xml_root:
                    try:
                        optimized = optimizer.optimize_dump(xml_root, self.device_id)
                        logger.info(f"生成优化缓存: {len(optimized)} 个元素 (原始: {len(list(xml_root.iter()))})")
                        return optimized
                    except Exception as e:
                        logger.warning(f"优化 UI dump 失败: {e}，使用未优化版本")

        # 使用未优化的版本
        if not force_refresh and self._ui_dump_list_cache is not None:
            logger.debug("使用 UI dump 列表缓存（未优化）")
            return self._ui_dump_list_cache

        # 先获取 XML
        xml_root = self.get_ui_dump(force_refresh=force_refresh)
        if xml_root is None:
            return []

        # 解析为列表格式
        elements = []

        def extract_node(node: ET.Element, parent_idx: int = None) -> None:
            """递归提取节点"""
            current_idx = len(elements)

            elem = {
                'tag': node.tag,
                'resource_id': node.get('resource-id', ''),
                'text': node.get('text', ''),
                'hint': node.get('hint', ''),  # 添加 hint 属性（占位符文字）
                'class': node.get('class', ''),
                'bounds': node.get('bounds', ''),
                'clickable': node.get('clickable', 'false') in self.TRUE_VALUES,
                'enabled': node.get('enabled', 'false') in self.TRUE_VALUES,
                'content_desc': node.get('content-desc', ''),
                'parent_idx': parent_idx,
            }

            # 仅在需要时包含 xml_node（避免 JSON 序列化问题）
            if include_xml_node:
                elem['xml_node'] = node

            elements.append(elem)

            # 递归处理子节点
            for child in node:
                extract_node(child, current_idx)

        extract_node(xml_root)

        # 缓存结果（仅当不包含 xml_node 时）
        if not include_xml_node:
            self._ui_dump_list_cache = elements
            logger.debug(f"已缓存 UI dump 列表（未优化），共 {len(elements)} 个元素")

        return elements

    def find_element(self, locator: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查找 UI 元素

        Args:
            locator: 定位器字典，包含策略和值
                例如: {"strategy": "id", "value": "com.example:id/button"}

        Returns:
            元素信息字典（包含 bounds, text, resource_id 等）
        """
        ui_dump = self.get_ui_dump(force_refresh=True)
        if ui_dump is None:
            return None

        strategy = locator.get("strategy", self.config.default_locator_strategy)
        value = locator.get("value", "")

        # 遍历 UI 树查找元素
        for node in ui_dump.iter():
            if self._match_element(node, strategy, value):
                return self._parse_element_info(node)

        return None

    def _match_element(self, node: ET.Element, strategy: str, value: str) -> bool:
        """
        匹配元素

        Args:
            node: XML 节点
            strategy: 定位策略
            value: 定位值

        Returns:
            是否匹配
        """
        if strategy == "id":
            return node.get("resource-id", "") == value
        elif strategy == "text":
            # text 策略同时匹配 text 和 content-desc 属性
            return (node.get("text", "") == value or
                    node.get("content-desc", "") == value)
        elif strategy == "class":
            return node.get("class", "") == value
        elif strategy == "content-desc":
            return node.get("content-desc", "") == value
        elif strategy == "text_contains":
            # text_contains 策略同时匹配 text 和 content-desc 属性
            return (value in node.get("text", "") or
                    value in node.get("content-desc", ""))
        else:
            return False

    def _parse_element_info(self, node: ET.Element) -> Dict[str, Any]:
        """
        解析元素信息

        Args:
            node: XML 节点

        Returns:
            元素信息字典
        """
        bounds = node.get("bounds", "")
        # 解析 bounds: [x1,y1][x2,y2]
        if bounds:
            import re
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
            else:
                center_x = center_y = 0
        else:
            center_x = center_y = 0

        return {
            "resource_id": node.get("resource-id", ""),
            "text": node.get("text", ""),
            "class": node.get("class", ""),
            "package": node.get("package", ""),
            "content_desc": node.get("content-desc", ""),
            "clickable": node.get("clickable", "false") == "true",
            "checkable": node.get("checkable", "false") == "true",
            "bounds": bounds,
            "center": {"x": center_x, "y": center_y},
        }

    def tap_element(self, locator: Dict[str, Any]) -> bool:
        """
        点击元素（自动查找可点击父容器）

        Args:
            locator: 定位器字典

        Returns:
            是否成功
        """
        # 首先尝试直接查找元素
        element = self.find_element(locator)
        if not element:
            logger.error(f"元素未找到: {locator}")
            return False

        # 如果元素本身可点击，直接点击
        if element.get("clickable"):
            center = element.get("center", {})
            x, y = center.get("x", 0), center.get("y", 0)
            logger.info(f"点击元素: {locator}")
            return self.tap(x, y)

        # 元素不可点击，尝试查找可点击的父容器
        logger.debug(f"元素本身不可点击，查找可点击父容器: {locator}")
        clickable_parent = self._find_clickable_parent(locator)
        if clickable_parent:
            center = clickable_parent.get("center", {})
            x, y = center.get("x", 0), center.get("y", 0)
            logger.info(f"点击可点击父容器: {locator}")
            return self.tap(x, y)

        logger.error(f"元素及其父容器均不可点击: {locator}")
        return False

    def _find_clickable_parent(self, locator: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查找元素的可点击父容器

        Args:
            locator: 元素的定位器字典

        Returns:
            可点击父容器的元素信息字典，未找到返回 None
        """
        ui_dump = self.get_ui_dump(force_refresh=True)
        if ui_dump is None:
            return None

        strategy = locator.get("strategy", self.config.default_locator_strategy)
        value = locator.get("value", "")

        # 查找目标元素节点
        target_node = None
        for node in ui_dump.iter():
            if self._match_element(node, strategy, value):
                target_node = node
                break

        if target_node is None:
            return None

        # 向上遍历父节点查找可点击元素
        current = target_node
        while current is not None:
            # 检查当前节点是否可点击
            if current.get("clickable", "false") == "true":
                # 找到可点击的父容器
                element_info = self._parse_element_info(current)
                logger.debug(f"找到可点击父容器: {element_info.get('text', '')} ({element_info.get('class', '')})")
                return element_info

            # 移动到父节点
            # 在XML树中，通过find方法向上查找
            parent_map = {c: p for p in ui_dump.iter() for c in p}
            current = parent_map.get(current)

            # 防止无限循环（最多检查10层）
            if hasattr(self, '_parent_search_depth'):
                self._parent_search_depth += 1
                if self._parent_search_depth > 10:
                    break
            else:
                self._parent_search_depth = 1

        return None

    # ========== 智能等待方法 ==========

    def wait_for_element(
        self,
        locator: Dict[str, Any],
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        等待元素出现

        Args:
            locator: 定位器字典
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            元素信息字典，超时返回 None
        """
        timeout = timeout or self.config.wait_timeout
        if timeout <= 0:
            logger.error(f"超时时间必须为正数: {timeout}")
            return None
        if poll_interval <= 0:
            logger.error(f"轮询间隔必须为正数: {poll_interval}")
            return None

        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        logger.info(f"等待元素: {locator}")

        while (time.time() - start_time) < timeout_sec:
            element = self.find_element(locator)
            if element:
                logger.info(f"✓ 元素已出现: {locator.get('strategy')}={locator.get('value')}")
                return element

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待元素超时: {locator}")
        return None

    def wait_for_element_visible(
        self,
        locator: Dict[str, Any],
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        等待元素可见

        Args:
            locator: 定位器字典
            timeout: 超时时间（毫秒）
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            元素信息字典，超时返回 None
        """
        timeout = timeout or self.config.wait_timeout
        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        logger.info(f"等待元素可见: {locator}")

        while (time.time() - start_time) < timeout_sec:
            element = self.find_element(locator)
            if element:
                # 检查元素是否可见（bounds 不为 [0,0][0,0]）
                bounds = element.get("bounds", "")
                if bounds and "[0,0][0,0]" not in bounds:
                    logger.info(f"✓ 元素已可见: {locator.get('strategy')}={locator.get('value')}")
                    return element

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待元素可见超时: {locator}")
        return None

    def wait_for_element_clickable(
        self,
        locator: Dict[str, Any],
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        等待元素可点击

        Args:
            locator: 定位器字典
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            元素信息字典，超时返回 None
        """
        timeout = timeout or self.config.wait_timeout
        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        logger.info(f"等待元素可点击: {locator}")

        while (time.time() - start_time) < timeout_sec:
            element = self.find_element(locator)
            if element and element.get("clickable", False):
                # 检查元素是否可见
                bounds = element.get("bounds", "")
                if bounds and "[0,0][0,0]" not in bounds:
                    logger.info(f"✓ 元素已可点击: {locator.get('strategy')}={locator.get('value')}")
                    return element

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待元素可点击超时: {locator}")
        return None

    def wait_for_text(
        self,
        text: str,
        exact_match: bool = False,
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> Optional[Dict[str, Any]]:
        """
        等待文本出现

        Args:
            text: 要等待的文本
            exact_match: 是否精确匹配
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            包含该文本的元素信息字典，超时返回 None
        """
        timeout = timeout or self.config.wait_timeout
        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        strategy = "text" if exact_match else "text_contains"
        locator = {"strategy": strategy, "value": text}

        logger.info(f"等待文本出现: {text}")

        while (time.time() - start_time) < timeout_sec:
            element = self.find_element(locator)
            if element:
                logger.info(f"✓ 文本已出现: {text}")
                return element

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待文本超时: {text}")
        return None

    def wait_for_app(
        self,
        package: str,
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> bool:
        """
        等待应用启动

        Args:
            package: 应用包名
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            是否成功启动
        """
        timeout = timeout or self.config.wait_timeout
        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        logger.info(f"等待应用启动: {package}")

        while (time.time() - start_time) < timeout_sec:
            # 检查当前前台应用
            try:
                result = self._execute_adb_command(
                    "shell dumpsys window | grep mCurrentFocus"
                )

                if result and package in result:
                    logger.info(f"✓ 应用已启动: {package}")
                    return True

            except Exception as e:
                logger.debug(f"检查应用状态失败: {e}")

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待应用启动超时: {package}")
        return False

    def wait_for_element_to_disappear(
        self,
        locator: Dict[str, Any],
        timeout: Optional[int] = None,
        poll_interval: int = 500
    ) -> bool:
        """
        等待元素消失

        Args:
            locator: 定位器字典
            timeout: 超时时间（毫秒），None 表示使用默认超时
            poll_interval: 轮询间隔（毫秒）

        Returns:
            是否成功消失
        """
        timeout = timeout or self.config.wait_timeout
        start_time = time.time()
        timeout_sec = timeout / 1000
        poll_interval_sec = poll_interval / 1000

        logger.info(f"等待元素消失: {locator}")

        while (time.time() - start_time) < timeout_sec:
            element = self.find_element(locator)
            if not element:
                logger.info(f"✓ 元素已消失: {locator.get('strategy')}={locator.get('value')}")
                return True

            time.sleep(poll_interval_sec)

        logger.warning(f"✗ 等待元素消失超时: {locator}")
        return False

    def close(self):
        """关闭设备连接"""
        self.disconnect()

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()

    def __repr__(self) -> str:
        return f"AndroidDeviceManager(device_id={self.device_id}, connected={self._connected})"


# 便捷函数
def create_android_device(device_serial: Optional[str] = None) -> AndroidDeviceManager:
    """
    创建 Android 设备实例

    Args:
        device_serial: 设备序列号（可选）

    Returns:
        设备管理器实例
    """
    manager = AndroidDeviceManager()
    manager.connect(device_serial)
    return manager


if __name__ == "__main__":
    # 测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    device = create_android_device()

    try:
        print(f"设备信息: {device.device_info}")

        # 截图测试
        device.screenshot("test_android_screenshot.png")

        # 测试按键
        device.press_home()
        time.sleep(1)

    finally:
        device.close()
