"""
图标查找和点击工具类

提供多种方式定位和点击 Android 应用中的图标
"""

import re
import logging
from typing import Optional, Dict, Any, List
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class IconHelper:
    """图标查找和点击助手"""

    def __init__(self, device):
        """
        初始化图标助手

        Args:
            device: AndroidDeviceManager 实例
        """
        self.device = device

    def find(self, text: str) -> Optional[Dict[str, Any]]:
        """
        简洁的查找方法：同时匹配 text 和 content-desc，使用评分机制选择最佳匹配

        评分规则：
        - 完全匹配: +100 分
        - 包含匹配: +50 分
        - 可点击: +20 分
        - 按钮类型: +10 分
        - 图标类型: +5 分
        - 文本越短: +10 分（长度 < 10）

        Args:
            text: 要查找的文本

        Returns:
            元素信息字典，未找到返回 None
        """
        # 优先使用 get_ui_dump_list()（如果有）
        ui_dump = None
        if hasattr(self.device, 'get_ui_dump_list'):
            # AndroidDeviceManager 有 get_ui_dump_list()
            ui_dump = self.device.get_ui_dump_list(force_refresh=False)
            # 直接在 dict list 上查找
            if isinstance(ui_dump, list) and len(ui_dump) > 0:
                return self._find_in_dict_list(ui_dump, text)

        # 回退到兼容模式
        try:
            ui_dump = self.device.get_ui_dump(force_refresh=False)
        except TypeError:
            ui_dump = self.device.get_ui_dump()

        # 处理不同的 UI dump 格式
        if isinstance(ui_dump, list):
            # core/android.py 格式：字典列表
            return self._find_in_dict_list(ui_dump, text)
        elif isinstance(ui_dump, ET.Element):
            # AndroidDeviceManager 格式：XML Element（无 get_ui_dump_list）
            return self._find_in_xml_tree(ui_dump, text)
        else:
            logger.error(f"不支持的 UI dump 类型: {type(ui_dump)}")
            return None

    def _find_in_dict_list(self, ui_dump: list, text: str) -> Optional[Dict[str, Any]]:
        """在字典列表中查找（推荐，速度最快）"""
        candidates = []

        for item in ui_dump:
            node_text = item.get('text', '')
            content_desc = item.get('content_desc', '')
            clickable = item.get('clickable', False)
            class_name = item.get('class', '')

            score = 0
            matched_text = None

            # 检查 text 属性
            if node_text:
                if text == node_text:
                    score += 100  # 完全匹配
                    matched_text = node_text
                elif text in node_text:
                    score += 50   # 包含匹配
                    matched_text = node_text

            # 检查 content-desc 属性（权重略低）
            if content_desc and not matched_text:
                if text == content_desc:
                    score += 90   # 完全匹配（content-desc）
                    matched_text = content_desc
                elif text in content_desc:
                    score += 45   # 包含匹配（content-desc）
                    matched_text = content_desc

            # 如果有匹配，计算额外分数
            if matched_text:
                # 可点击优先
                if clickable:
                    score += 20

                # 类型优先级
                if 'Button' in class_name:
                    score += 10
                elif 'ImageButton' in class_name:
                    score += 8
                elif 'ImageView' in class_name:
                    score += 5

                # 文本越短越好（可能是按钮/图标）
                if len(matched_text) < 10:
                    score += 10
                elif len(matched_text) < 20:
                    score += 5

                # 直接使用 item，不需要重新解析
                item['_score'] = score
                item['_matched_text'] = matched_text
                candidates.append(item)

        # 返回得分最高的候选
        if candidates:
            # 按分数降序排序
            candidates.sort(key=lambda x: x.get('_score', 0), reverse=True)

            # 输出调试信息
            if len(candidates) > 1:
                logger.debug(f"找到 {len(candidates)} 个匹配，选择得分最高的")
                logger.debug(f"最佳匹配: score={candidates[0]['_score']}, text={candidates[0].get('_matched_text')}")

            return candidates[0]

        return None

    def _find_in_xml_tree(self, ui_root: ET.Element, text: str) -> Optional[Dict[str, Any]]:
        """在 XML 树中查找（兼容模式）"""
        candidates = []

        for node in ui_root.iter():
            node_text = node.get('text', '')
            content_desc = node.get('content-desc', '')
            clickable = node.get('clickable', 'false') == 'true'
            class_name = node.get('class', '')

            score = 0
            matched_text = None

            # 检查 text 属性
            if node_text:
                if text == node_text:
                    score += 100  # 完全匹配
                    matched_text = node_text
                elif text in node_text:
                    score += 50   # 包含匹配
                    matched_text = node_text

            # 检查 content-desc 属性（权重略低）
            if content_desc and not matched_text:
                if text == content_desc:
                    score += 90   # 完全匹配（content-desc）
                    matched_text = content_desc
                elif text in content_desc:
                    score += 45   # 包含匹配（content-desc）
                    matched_text = content_desc

            # 如果有匹配，计算额外分数
            if matched_text:
                # 可点击优先
                if clickable:
                    score += 20

                # 类型优先级
                if 'Button' in class_name:
                    score += 10
                elif 'ImageButton' in class_name:
                    score += 8
                elif 'ImageView' in class_name:
                    score += 5

                # 文本越短越好（可能是按钮/图标）
                if len(matched_text) < 10:
                    score += 10
                elif len(matched_text) < 20:
                    score += 5

                # 解析元素信息
                try:
                    element = self.device._parse_element_info(node)
                except AttributeError:
                    # 如果设备没有 _parse_element_info 方法，手动解析
                    element = self._parse_element_info_manual(node)

                element['_score'] = score
                element['_matched_text'] = matched_text
                candidates.append(element)

        # 返回得分最高的候选
        if candidates:
            # 按分数降序排序
            candidates.sort(key=lambda x: x.get('_score', 0), reverse=True)

            # 输出调试信息
            if len(candidates) > 1:
                logger.debug(f"找到 {len(candidates)} 个匹配，选择得分最高的")
                logger.debug(f"最佳匹配: score={candidates[0]['_score']}, text={candidates[0].get('_matched_text')}")

            return candidates[0]

        return None

    def _parse_element_info_manual(self, node: ET.Element) -> Dict[str, Any]:
        """手动解析 XML 元素信息（备用方法）"""
        import re
        bounds = node.get("bounds", "")
        if bounds:
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

    def tap(self, text: str) -> bool:
        """
        简洁的点击方法：查找并点击

        Args:
            text: 要点击的文本

        Returns:
            是否成功点击
        """
        icon = self.find(text)
        if icon:
            return self.tap_icon(icon)
        return False

    def find_icon_by_text(self, text: str, exact_match: bool = False) -> Optional[Dict[str, Any]]:
        """
        通过文本查找图标（推荐用于有文字的图标）

        Args:
            text: 图标文本
            exact_match: 是否精确匹配（False 为包含匹配）

        Returns:
            元素信息字典
        """
        strategy = "text" if exact_match else "text_contains"
        return self.device.find_element({"strategy": strategy, "value": text})

    def find_icon_by_description(self, description: str) -> Optional[Dict[str, Any]]:
        """
        通过 content-desc 查找图标（推荐）

        Args:
            description: 图标的内容描述

        Returns:
            元素信息字典
        """
        return self.device.find_element({
            "strategy": "content-desc",
            "value": description
        })

    def find_icon_by_id(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        通过 resource-id 查找图标

        Args:
            resource_id: 资源 ID

        Returns:
            元素信息字典
        """
        return self.device.find_element({
            "strategy": "id",
            "value": resource_id
        })

    def find_all_icons(self, icon_type: str = "ImageView") -> List[Dict[str, Any]]:
        """
        查找所有指定类型的图标

        Args:
            icon_type: 图标类型 (ImageView, ImageButton, FrameLayout 等)

        Returns:
            图标元素列表
        """
        ui_dump = self.device.get_ui_dump(force_refresh=False)
        icons = []

        for node in ui_dump.iter():
            class_name = node.get('class', '')

            if icon_type in class_name:
                element = self.device._parse_element_info(node)
                icons.append(element)

        return icons

    def find_clickable_icons(self) -> List[Dict[str, Any]]:
        """
        查找所有可点击的图标

        Returns:
            可点击图标列表
        """
        ui_dump = self.device.get_ui_dump(force_refresh=False)
        clickable_icons = []

        for node in ui_dump.iter():
            clickable = node.get('clickable', 'false') == 'true'
            class_name = node.get('class', '')

            # 检查是否是图标类型
            is_icon = any(t in class_name for t in ['ImageView', 'ImageButton', 'FrameLayout'])

            if is_icon and clickable:
                element = self.device._parse_element_info(node)
                clickable_icons.append(element)

        return clickable_icons

    def find_icon_by_position(self, x: int, y: int, tolerance: int = 50) -> Optional[Dict[str, Any]]:
        """
        通过坐标附近查找图标

        Args:
            x: X 坐标
            y: Y 坐标
            tolerance: 容差范围（像素）

        Returns:
            图标元素字典
        """
        ui_dump = self.device.get_ui_dump(force_refresh=False)

        for node in ui_dump.iter():
            bounds = node.get('bounds', '')
            if bounds:
                match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())

                    # 检查坐标是否在 bounds 容差范围内
                    if (x1 - tolerance <= x <= x2 + tolerance and
                        y1 - tolerance <= y <= y2 + tolerance):

                        element = self.device._parse_element_info(node)
                        return element

        return None

    def find_icon_near_text(self, text: str, max_distance: int = 200) -> Optional[Dict[str, Any]]:
        """
        查找文本附近的图标（例如：文字旁边的图标按钮）

        Args:
            text: 参考文本
            max_distance: 最大距离（像素）

        Returns:
            图标元素字典
        """
        # 先找到文本元素
        text_element = self.find_icon_by_text(text)
        if not text_element:
            return None

        text_center = text_element.get('center', {})
        text_x, text_y = text_center.get('x', 0), text_center.get('y', 0)

        # 查找附近的图标
        ui_dump = self.device.get_ui_dump(force_refresh=False)

        closest_icon = None
        min_distance = float('inf')

        for node in ui_dump.iter():
            class_name = node.get('class', '')
            is_icon = any(t in class_name for t in ['ImageView', 'ImageButton'])

            if is_icon:
                element = self.device._parse_element_info(node)
                icon_center = element.get('center', {})
                icon_x, icon_y = icon_center.get('x', 0), icon_center.get('y', 0)

                # 计算距离
                distance = ((icon_x - text_x) ** 2 + (icon_y - text_y) ** 2) ** 0.5

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    closest_icon = element

        return closest_icon

    def tap_icon(self, icon: Dict[str, Any]) -> bool:
        """
        点击图标（自动查找可点击父容器）

        Args:
            icon: 图标元素字典

        Returns:
            是否成功
        """
        if not icon:
            logger.warning("图标元素为空，无法点击")
            return False

        # 检查元素是否可点击
        if not icon.get('clickable', False):
            logger.debug(f"元素本身不可点击，尝试查找可点击的父容器")
            clickable_parent = self._find_clickable_parent(icon)
            if clickable_parent:
                logger.info(f"使用可点击父容器进行点击")
                icon = clickable_parent
            else:
                logger.warning("未找到可点击的父容器，仍尝试点击原元素")

        center = icon.get('center', {})
        x, y = center.get('x', 0), center.get('y', 0)

        # 如果坐标为 (0, 0)，尝试从 bounds 解析或查找父元素
        if x == 0 and y == 0:
            logger.debug("图标坐标为 (0, 0)，尝试查找有效坐标")
            valid_coords = self._find_valid_coordinates(icon)
            if valid_coords:
                x, y = valid_coords
                logger.info(f"使用父元素坐标: ({x}, {y})")
            else:
                logger.warning("无法找到有效坐标，点击失败")
                return False

        return self.device.tap(x, y)

    def _find_valid_coordinates(self, element: Dict[str, Any]) -> Optional[tuple]:
        """
        查找有效的坐标（使用相对定位合并策略）

        策略：
        1. 尝试从当前元素的 bounds 解析坐标
        2. 如果坐标无效，查找包含当前元素的父元素
        3. 使用父元素的 bounds 和当前元素的相对位置计算合并坐标

        相对定位原理：
          - 父元素: bounds [px1, py1][px2, py2]
          - 当前元素: bounds [cx1, cy1][cx2, cy2] (可能为 0,0)
          - 合并坐标: 使用当前元素相对于父元素的位置
          - 如果当前元素完全在父元素内部，使用当前元素的中心
          - 如果当前元素超出父元素，使用父元素的中心

        Args:
            element: 元素字典

        Returns:
            (x, y) 坐标元组，未找到返回 None
        """
        import re

        # 步骤 1: 尝试从当前元素的 bounds 解析
        bounds_str = element.get('bounds', '')
        if bounds_str:
            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
            if match:
                x1, y1, x2, y2 = map(int, match.groups())
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2

                # 验证坐标是否有效（非零）
                if center_x > 0 and center_y > 0:
                    logger.debug(f"从当前元素 bounds 解析出坐标: ({center_x}, {center_y})")
                    return (center_x, center_y)

                # 坐标为 0，但 bounds 有值，继续尝试相对定位
                logger.debug(f"当前元素 bounds 存在但中心坐标为 (0, 0)，尝试相对定位")

        # 步骤 2: 查找父元素并使用相对定位
        if not bounds_str:
            logger.debug("当前元素无 bounds，无法查找父元素")
            return None

        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if not match:
            logger.debug(f"无法解析 bounds: {bounds_str}")
            return None

        current_x1, current_y1, current_x2, current_y2 = map(int, match.groups())
        current_area = (current_x2 - current_x1) * (current_y2 - current_y1)
        current_center_x = (current_x1 + current_x2) // 2
        current_center_y = (current_y1 + current_y2) // 2

        # 获取所有 UI 元素
        items = None
        if hasattr(self.device, 'get_ui_dump_list'):
            items = self.device.get_ui_dump_list(force_refresh=False)

        if items is None or not isinstance(items, list):
            try:
                ui_dump = self.device.get_ui_dump()
            except:
                return None

            if isinstance(ui_dump, list) and len(ui_dump) > 0 and isinstance(ui_dump[0], dict):
                items = ui_dump
            elif isinstance(ui_dump, ET.Element):
                items = self._element_list_to_dict_list(ui_dump)
            else:
                return None

        # 查找包含当前元素的父元素
        candidates = []

        for item in items:
            item_bounds = item.get('bounds', '')
            if not item_bounds:
                continue

            item_match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', item_bounds)
            if not item_match:
                continue

            item_x1, item_y1, item_x2, item_y2 = map(int, item_match.groups())

            # 检查是否包含当前元素（完全包含或部分包含）
            if (item_x1 <= current_x1 and item_y1 <= current_y1 and
                item_x2 >= current_x2 and item_y2 >= current_y2):

                item_area = (item_x2 - item_x1) * (item_y2 - item_y1)

                # 父元素应该比当前元素大
                if item_area > current_area:
                    # 计算父元素中心
                    item_center_x = (item_x1 + item_x2) // 2
                    item_center_y = (item_y1 + item_y2) // 2

                    # 只考虑有效的坐标
                    if item_center_x > 0 and item_center_y > 0:
                        # 使用当前元素的中心点（即使它可能为0，我们重新计算）
                        # 或者使用相对位置：偏向当前元素在父元素中的位置
                        candidates.append((item_area, current_center_x, current_center_y, item))

        # 返回面积最小的父元素（最接近的父元素），使用当前元素的中心坐标
        if candidates:
            candidates.sort(key=lambda x: x[0])  # 按面积升序排序
            best_match = candidates[0]
            center_x, center_y = best_match[1], best_match[2]

            # 验证合并后的坐标
            if center_x > 0 and center_y > 0:
                logger.info(f"使用相对定位合并坐标: ({center_x}, {center_y}), 父元素面积: {best_match[0]}")
                return (center_x, center_y)
            else:
                # 如果当前元素中心仍为0，使用父元素中心
                parent_center_x = (best_match[3].get('bounds', '').split(']')[0].split(',')[0] if best_match[3].get('bounds') else 0)
                if parent_center_x == 0:
                    # 从父元素 bounds 重新计算
                    p_bounds = best_match[3].get('bounds', '')
                    p_match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', p_bounds)
                    if p_match:
                        px1, py1, px2, py2 = map(int, p_match.groups())
                        parent_center_x = (px1 + px2) // 2
                        parent_center_y = (py1 + py2) // 2
                        logger.info(f"使用父元素中心坐标: ({parent_center_x}, {parent_center_y})")
                        return (parent_center_x, parent_center_y)

        logger.warning("未找到有效的父元素坐标")
        return None

    def _find_clickable_parent(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查找元素的可点击父容器

        Args:
            element: 元素字典

        Returns:
            可点击的父容器，未找到返回 None
        """
        import re

        bounds_str = element.get('bounds', '')
        if not bounds_str:
            return None

        # 获取当前元素的边界
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
        if not match:
            return None

        current_x1, current_y1, current_x2, current_y2 = map(int, match.groups())
        current_area = (current_x2 - current_x1) * (current_y2 - current_y1)

        # 优先使用 get_ui_dump_list()
        items = None
        if hasattr(self.device, 'get_ui_dump_list'):
            # AndroidDeviceManager 有 get_ui_dump_list()
            items = self.device.get_ui_dump_list(force_refresh=False)

        # 回退到兼容模式
        if items is None or not isinstance(items, list):
            try:
                ui_dump = self.device.get_ui_dump()
            except:
                ui_dump = []

            # 处理不同的 UI dump 格式
            if isinstance(ui_dump, list) and len(ui_dump) > 0 and isinstance(ui_dump[0], dict):
                # core/android.py 格式：字典列表
                items = ui_dump
            elif isinstance(ui_dump, ET.Element):
                # AndroidDeviceManager 格式：XML Element
                items = self._element_list_to_dict_list(ui_dump)
            else:
                return None

        # 遍历所有元素，查找包含当前元素的可点击父元素
        candidates = []

        for item in items:
            if not item.get('clickable', False):
                continue

            item_bounds = item.get('bounds', '')
            if not item_bounds:
                continue

            match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', item_bounds)
            if not match:
                continue

            x1, y1, x2, y2 = map(int, match.groups())

            # 检查是否包含当前元素
            if x1 <= current_x1 and y1 <= current_y1 and x2 >= current_x2 and y2 >= current_y2:
                # 计算面积
                area = (x2 - x1) * (y2 - y1)

                # 只选择面积比当前元素大的（避免选择自己）
                if area > current_area:
                    # 重新计算中心坐标
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2

                    candidates.append({
                        **item,
                        'center': {'x': center_x, 'y': center_y},
                        '_area': area,
                    })

        if not candidates:
            return None

        # 按面积排序（选择最小的包含父元素）
        candidates.sort(key=lambda x: x.get('_area', 0))

        logger.debug(f"找到 {len(candidates)} 个可点击父容器，选择面积最小的")
        return candidates[0] if candidates else None

    def _element_list_to_dict_list(self, root: ET.Element) -> List[Dict[str, Any]]:
        """将 XML Element 树转换为字典列表（备用）"""
        try:
            # 如果设备有 _parse_element_info 方法，使用它
            if hasattr(self.device, '_parse_element_info'):
                return [self.device._parse_element_info(node) for node in root.iter()]
            else:
                return [self._parse_element_info_manual(node) for node in root.iter()]
        except:
            return []

    def tap_icon_by_description(self, description: str) -> bool:
        """
        通过描述点击图标（便捷方法）

        Args:
            description: 图标描述

        Returns:
            是否成功
        """
        icon = self.find_icon_by_description(description)
        if icon:
            logger.info(f"通过描述点击图标: {description}")
            return self.tap_icon(icon)
        else:
            logger.warning(f"未找到描述为 '{description}' 的图标")
            return False

    def tap_icon_by_text(self, text: str) -> bool:
        """
        通过文本点击图标（便捷方法）

        Args:
            text: 图标文本

        Returns:
            是否成功
        """
        icon = self.find_icon_by_text(text)
        if icon:
            logger.info(f"通过文本点击图标: {text}")
            return self.tap_icon(icon)
        else:
            logger.warning(f"未找到文本为 '{text}' 的图标")
            return False

    def print_all_clickable_icons(self):
        """打印所有可点击的图标（调试用）"""
        icons = self.find_clickable_icons()

        print(f"\n找到 {len(icons)} 个可点击图标:\n")

        for i, icon in enumerate(icons, 1):
            text = icon.get('text', '')
            resource_id = icon.get('resource_id', '')
            content_desc = icon.get('content_desc', '')
            class_name = icon.get('class', '').split('.')[-1]
            center = icon.get('center', {})

            print(f"{i}. {class_name}")
            if text:
                print(f"   文本: \"{text}\"")
            if content_desc:
                print(f"   描述: \"{content_desc}\"")
            if resource_id:
                print(f"   ID: {resource_id}")
            print(f"   位置: ({center.get('x', 0)}, {center.get('y', 0)})")
            print()


if __name__ == '__main__':
    """测试图标助手"""
    import sys
    sys.path.insert(0, '.')

    from rpa_core.android import create_android_device
    import time

    device = create_android_device()
    helper = IconHelper(device)

    # 打印所有可点击图标
    helper.print_all_clickable_icons()

    device.close()
