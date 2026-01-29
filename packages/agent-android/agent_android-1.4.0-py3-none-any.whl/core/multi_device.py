"""
多设备管理器

支持同时连接和操作多个 Android 设备
"""

import logging
import time
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .android import AndroidDeviceManager, create_android_device
from .adb_config import ADBConfig

logger = logging.getLogger(__name__)


class MultiDeviceManager:
    """多设备管理器"""

    def __init__(self, config: Optional[ADBConfig] = None):
        """
        初始化多设备管理器

        Args:
            config: ADB 配置
        """
        self.config = config or ADBConfig()
        self.devices: Dict[str, AndroidDeviceManager] = {}
        self.device_info: Dict[str, Dict[str, Any]] = {}

    def connect_all(self, max_devices: Optional[int] = None) -> int:
        """
        连接所有可用设备

        Args:
            max_devices: 最大连接设备数（None 表示全部）

        Returns:
            成功连接的设备数量
        """
        logger.info("开始连接所有可用设备...")

        # 获取所有设备列表
        temp_device = AndroidDeviceManager(self.config)
        all_devices = temp_device.list_devices()
        temp_device.close()

        if not all_devices:
            logger.warning("未找到任何可用设备")
            return 0

        # 限制设备数量
        devices_to_connect = all_devices[:max_devices] if max_devices else all_devices

        logger.info(f"找到 {len(all_devices)} 个设备，连接前 {len(devices_to_connect)} 个")

        # 并行连接所有设备
        connected_count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_device = {
                executor.submit(self._connect_single, device_id): device_id
                for device_id in devices_to_connect
            }

            for future in as_completed(future_to_device):
                device_id = future_to_device[future]
                try:
                    success = future.result()
                    if success:
                        connected_count += 1
                        logger.info(f"✓ 设备 {device_id} 连接成功")
                    else:
                        logger.warning(f"✗ 设备 {device_id} 连接失败")
                except Exception as e:
                    logger.error(f"✗ 设备 {device_id} 连接出错: {e}")

        logger.info(f"成功连接 {connected_count}/{len(devices_to_connect)} 个设备")
        return connected_count

    def _connect_single(self, device_id: str) -> bool:
        """
        连接单个设备

        Args:
            device_id: 设备序列号

        Returns:
            是否成功
        """
        try:
            device = create_android_device(device_id)
            self.devices[device_id] = device
            self.device_info[device_id] = device.device_info
            return True
        except Exception as e:
            logger.error(f"连接设备 {device_id} 失败: {e}")
            return False

    def connect_device(self, device_id: str) -> bool:
        """
        连接指定设备

        Args:
            device_id: 设备序列号

        Returns:
            是否成功
        """
        if device_id in self.devices:
            logger.warning(f"设备 {device_id} 已经连接")
            return True

        logger.info(f"连接设备 {device_id}...")
        return self._connect_single(device_id)

    def disconnect_all(self):
        """断开所有设备连接"""
        logger.info(f"断开所有 {len(self.devices)} 个设备的连接...")

        for device_id, device in list(self.devices.items()):
            try:
                device.close()
                logger.info(f"✓ 设备 {device_id} 已断开")
            except Exception as e:
                logger.error(f"✗ 断开设备 {device_id} 出错: {e}")

        self.devices.clear()
        self.device_info.clear()

    def disconnect_device(self, device_id: str):
        """
        断开指定设备

        Args:
            device_id: 设备序列号
        """
        if device_id in self.devices:
            try:
                self.devices[device_id].close()
                del self.devices[device_id]
                del self.device_info[device_id]
                logger.info(f"设备 {device_id} 已断开")
            except Exception as e:
                logger.error(f"断开设备 {device_id} 出错: {e}")

    def get_device(self, device_id: str) -> Optional[AndroidDeviceManager]:
        """
        获取指定设备实例

        Args:
            device_id: 设备序列号

        Returns:
            设备管理器实例，如果不存在返回 None
        """
        return self.devices.get(device_id)

    def get_devices(self) -> List[str]:
        """
        获取所有已连接设备的 ID 列表

        Returns:
            设备 ID 列表
        """
        return list(self.devices.keys())

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        获取设备信息

        Args:
            device_id: 设备序列号

        Returns:
            设备信息字典
        """
        return self.device_info.get(device_id)

    def list_devices(self) -> List[Dict[str, Any]]:
        """
        列出所有已连接设备的信息

        Returns:
            设备信息列表
        """
        devices_info = []

        for device_id in self.get_devices():
            info = self.get_device_info(device_id)
            if info:
                devices_info.append({
                    'device_id': device_id,
                    **info
                })

        return devices_info

    # ========== 并行操作方法 ==========

    def parallel_execute(
        self,
        func: Callable[[AndroidDeviceManager], Any],
        device_ids: Optional[List[str]] = None,
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        并行执行函数在所有设备上

        Args:
            func: 要执行的函数，接收设备管理器作为参数
            device_ids: 设备 ID 列表（None 表示所有设备）
            max_workers: 最大并行数（None 表示自动）

        Returns:
            设备 ID 到执行结果的映射
        """
        if device_ids is None:
            device_ids = self.get_devices()

        if not device_ids:
            logger.warning("没有可用的设备")
            return {}

        logger.info(f"在 {len(device_ids)} 个设备上并行执行任务...")

        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_device = {
                executor.submit(func, self.devices[device_id]): device_id
                for device_id in device_ids if device_id in self.devices
            }

            for future in as_completed(future_to_device):
                device_id = future_to_device[future]
                try:
                    result = future.result()
                    results[device_id] = result
                    logger.info(f"✓ 设备 {device_id} 执行成功")
                except Exception as e:
                    logger.error(f"✗ 设备 {device_id} 执行失败: {e}")
                    results[device_id] = None

        return results

    def parallel_screenshot(
        self,
        path_template: str = "screenshot_{device_id}.png",
        device_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        并行截图所有设备

        Args:
            path_template: 截图路径模板，{device_id} 会被替换为设备 ID
            device_ids: 设备 ID 列表（None 表示所有设备）

        Returns:
            设备 ID 到截图成功状态的映射
        """
        def screenshot_func(device: AndroidDeviceManager) -> bool:
            device_id = device.device_id
            path = path_template.format(device_id=device_id)

            # 确保目录存在
            Path(path).parent.mkdir(parents=True, exist_ok=True)

            return device.screenshot(path)

        return self.parallel_execute(screenshot_func, device_ids)

    def parallel_tap(
        self,
        x: int,
        y: int,
        device_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        并行在所有设备上点击

        Args:
            x: X 坐标
            y: Y 坐标
            device_ids: 设备 ID 列表（None 表示所有设备）

        Returns:
            设备 ID 到点击成功状态的映射
        """
        def tap_func(device: AndroidDeviceManager) -> bool:
            return device.tap(x, y)

        return self.parallel_execute(tap_func, device_ids)

    def parallel_start_app(
        self,
        package: str,
        device_ids: Optional[List[str]] = None,
        activity: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        并行在所有设备上启动应用

        Args:
            package: 应用包名
            device_ids: 设备 ID 列表（None 表示所有设备）
            activity: 应用 Activity

        Returns:
            设备 ID 到启动成功状态的映射
        """
        def start_app_func(device: AndroidDeviceManager) -> bool:
            return device.start_app(package, activity)

        return self.parallel_execute(start_app_func, device_ids)

    def parallel_input_text(
        self,
        text: str,
        device_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        并行在所有设备上输入文本

        Args:
            text: 要输入的文本
            device_ids: 设备 ID 列表（None 表示所有设备）

        Returns:
            设备 ID 到输入成功状态的映射
        """
        def input_func(device: AndroidDeviceManager) -> bool:
            return device.input_text(text)

        return self.parallel_execute(input_func, device_ids)

    def parallel_press_key(
        self,
        keycode: int,
        device_ids: Optional[List[str]] = None
    ) -> Dict[str, bool]:
        """
        并行在所有设备上按下按键

        Args:
            keycode: 按键代码
            device_ids: 设备 ID 列表（None 表示所有设备）

        Returns:
            设备 ID 到按键成功状态的映射
        """
        def press_func(device: AndroidDeviceManager) -> bool:
            return device.press_key(keycode)

        return self.parallel_execute(press_func, device_ids)

    # ========== 辅助方法 ==========

    def get_device_count(self) -> int:
        """
        获取已连接设备数量

        Returns:
            设备数量
        """
        return len(self.devices)

    def is_device_connected(self, device_id: str) -> bool:
        """
        检查设备是否已连接

        Args:
            device_id: 设备序列号

        Returns:
            是否已连接
        """
        return device_id in self.devices

    def get_device_by_index(self, index: int) -> Optional[AndroidDeviceManager]:
        """
        通过索引获取设备（从0开始）

        Args:
            index: 设备索引

        Returns:
            设备管理器实例
        """
        device_ids = self.get_devices()
        if 0 <= index < len(device_ids):
            device_id = device_ids[index]
            return self.devices.get(device_id)
        return None

    def get_device_by_name(self, name: str) -> Optional[AndroidDeviceManager]:
        """
        通过设备名称查找设备

        Args:
            name: 设备名称（model 或 manufacturer）

        Returns:
            设备管理器实例
        """
        for device_id, device in self.devices.items():
            info = device.device_info
            if (name.lower() in info.get('model', '').lower() or
                name.lower() in info.get('manufacturer', '').lower()):
                return device
        return None

    def execute_on_device(
        self,
        device_id: str,
        func: Callable[[AndroidDeviceManager], Any]
    ) -> Any:
        """
        在指定设备上执行函数

        Args:
            device_id: 设备序列号
            func: 要执行的函数

        Returns:
            函数执行结果
        """
        device = self.get_device(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 未连接")

        return func(device)

    def broadcast(self, func: Callable[[AndroidDeviceManager], Any]) -> Dict[str, Any]:
        """
        广播执行函数到所有设备

        Args:
            func: 要执行的函数

        Returns:
            设备 ID 到执行结果的映射
        """
        return self.parallel_execute(func, None)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect_all()

    def __repr__(self) -> str:
        return f"MultiDeviceManager(devices={len(self.devices)}, connected={list(self.devices.keys())})"


# 便捷函数
def create_multi_device_manager() -> MultiDeviceManager:
    """
    创建多设备管理器

    Returns:
        多设备管理器实例
    """
    return MultiDeviceManager()


def connect_all_devices(max_devices: Optional[int] = None) -> MultiDeviceManager:
    """
    连接所有可用设备并返回管理器

    Args:
        max_devices: 最大连接设备数

    Returns:
        多设备管理器实例
    """
    manager = create_multi_device_manager()
    manager.connect_all(max_devices)
    return manager


if __name__ == '__main__':
    # 测试
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=== 多设备管理器测试 ===\n")

    # 创建管理器
    manager = create_multi_device_manager()

    # 连接所有设备
    count = manager.connect_all()

    if count > 0:
        print(f"\n成功连接 {count} 个设备")

        # 列出设备
        devices = manager.list_devices()
        print("\n设备列表:")
        for device_info in devices:
            print(f"  - {device_info['device_id']}: {device_info['model']}")

        # 并行截图
        print("\n并行截图...")
        results = manager.parallel_screenshot("screenshots/multi_{device_id}.png")
        print(f"截图完成: {sum(results.values())}/{len(results)} 成功")

        # 关闭所有连接
        manager.disconnect_all()
        print("\n所有设备已断开")
    else:
        print("\n未找到可用的设备")

    print("\n=== 测试完成 ===")
