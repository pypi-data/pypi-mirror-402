"""
自然语言图标助手

使用自然语言描述来查找和点击图标
支持中文描述，例如："点击右上角的设置按钮"
"""

import re
import logging
from typing import Optional, Dict, Any, List
from .icon_helper import IconHelper

logger = logging.getLogger(__name__)


class NLPIconHelper:
    """自然语言图标助手"""

    def __init__(self, device):
        """
        初始化 NLP 图标助手

        Args:
            device: AndroidDeviceManager 实验实例
        """
        self.device = device
        self.helper = IconHelper(device)

        # 关键词映射
        self.position_keywords = {
            '左上': {'x_range': (0, 400), 'y_range': (0, 400)},
            '右上': {'x_range': (800, 1080), 'y_range': (0, 400)},
            '左下': {'x_range': (0, 400), 'y_range': (1800, 2264)},
            '右下': {'x_range': (800, 1080), 'y_range': (1800, 2264)},
            '顶部': {'y_range': (0, 600)},
            '底部': {'y_range': (1800, 2264)},
            '左侧': {'x_range': (0, 400)},
            '右侧': {'x_range': (800, 1080)},
            '中间': {'x_range': (400, 800), 'y_range': (600, 1800)},
            '中央': {'x_range': (400, 800), 'y_range': (600, 1800)},
        }

        self.type_keywords = {
            '图标': ['ImageView', 'ImageButton'],
            '按钮': ['Button', 'ImageButton', 'FrameLayout'],
            '文字': ['TextView', 'EditText'],
            '输入框': ['EditText'],
        }

    def parse_description(self, description: str) -> Dict[str, Any]:
        """
        解析自然语言描述

        Args:
            description: 自然语言描述，例如："点击右上角的设置按钮"

        Returns:
            解析结果字典，包含位置、类型、文本等
        """
        result = {
            'action': '点击',
            'position': None,
            'type': None,
            'text': None,
            'description': None,
            'id': None,
        }

        # 解析动作
        if '点击' in description:
            result['action'] = '点击'
        elif '长按' in description:
            result['action'] = '长按'
        elif '滑动' in description:
            result['action'] = '滑动'

        # 解析位置关键词
        for pos_name, pos_range in self.position_keywords.items():
            if pos_name in description:
                result['position'] = pos_name
                result['position_range'] = pos_range
                break

        # 解析类型关键词
        for type_name, type_classes in self.type_keywords.items():
            if type_name in description:
                result['type'] = type_name
                result['type_classes'] = type_classes
                break

        # 解析文本内容（使用引号或直接提取）
        # 查找引号中的内容
        quoted_texts = re.findall(r'["\"](.*?)["\"]', description)
        if quoted_texts:
            result['text'] = quoted_texts[0]
        else:
            # 查找常见关键词后面的内容
            for keyword in ['名为', '叫做', '显示', '内容是', '文字是']:
                if keyword in description:
                    parts = description.split(keyword)
                    if len(parts) > 1:
                        result['text'] = parts[1].strip().split(' ')[0].strip('的，。')
                        break

        # 解析描述性关键词（content-desc）
        desc_keywords = ['设置', '搜索', '返回', '菜单', '首页', '我的', '收藏', '分享', '删除', '编辑']
        for keyword in desc_keywords:
            if keyword in description and result['text'] is None:
                result['description'] = keyword
                break

        return result

    def find_icon_by_nlp(self, description: str) -> Optional[Dict[str, Any]]:
        """
        根据自然语言描述查找图标

        Args:
            description: 自然语言描述

        Returns:
            匹配的图标元素，如果未找到返回 None
        """
        parsed = self.parse_description(description)

        logger.info(f"解析结果: {parsed}")

        # 策略1: 如果有明确的文本描述，优先使用文本查找
        if parsed['text']:
            logger.info(f"通过文本查找: {parsed['text']}")
            icon = self.helper.find_icon_by_text(parsed['text'])
            if icon:
                return icon

        # 策略2: 如果有描述关键词，使用描述查找
        if parsed['description']:
            logger.info(f"通过描述查找: {parsed['description']}")
            icon = self.helper.find_icon_by_description(parsed['description'])
            if icon:
                return icon

        # 策略3: 根据位置和类型筛选
        candidates = []

        # 获取所有可点击图标
        if parsed.get('type') == '图标':
            icons = self.helper.find_all_icons('ImageView')
        elif parsed.get('type') == '按钮':
            icons = self.helper.find_clickable_icons()
        else:
            icons = self.helper.find_clickable_icons()

        # 根据位置筛选
        if parsed.get('position'):
            pos_range = parsed['position_range']

            for icon in icons:
                center = icon.get('center', {})
                x, y = center.get('x', 0), center.get('y', 0)

                # 检查是否在位置范围内
                in_range = True

                if 'x_range' in pos_range:
                    x_min, x_max = pos_range['x_range']
                    if not (x_min <= x <= x_max):
                        in_range = False

                if 'y_range' in pos_range:
                    y_min, y_max = pos_range['y_range']
                    if not (y_min <= y <= y_max):
                        in_range = False

                if in_range:
                    candidates.append(icon)
        else:
            candidates = icons

        # 返回第一个候选
        if candidates:
            logger.info(f"找到 {len(candidates)} 个候选图标，返回第一个")
            return candidates[0]

        logger.warning("未找到匹配的图标")
        return None

    def parse_bounds(self, bounds_str: str):
        """解析 bounds 字符串"""
        matches = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
        if len(matches) == 2:
            x1, y1 = int(matches[0][0]), int(matches[0][1])
            x2, y2 = int(matches[1][0]), int(matches[1][1])
            return (x1, y1, x2, y2)
        return None

    def parse_relative_description(self, description: str) -> Optional[Dict[str, Any]]:
        """
        解析相对位置描述

        支持的模式：
        - "点击背词有道左侧的图标"
        - "点击设置按钮右边的箭头"
        - "点击标题下方的输入框"

        Returns:
            包含 reference, direction, target_type 的字典，如果未匹配返回 None
        """
        # 定义相对位置模式
        patterns = [
            (r'点击?(.*?)左侧的?(.+)', '左侧'),
            (r'点击?(.*?)左边的?(.+)', '左侧'),
            (r'点击?(.*?)左侧', '左侧'),
            (r'点击?(.*?)左边的', '左侧'),
            (r'点击?(.*?)右侧的?(.+)', '右侧'),
            (r'点击?(.*?)右边的?(.+)', '右侧'),
            (r'点击?(.*?)右侧', '右侧'),
            (r'点击?(.*?)右边的', '右侧'),
            (r'点击?(.*?)上方的?(.+)', '上方'),
            (r'点击?(.*?)上边的?(.+)', '上方'),
            (r'点击?(.*?)上方', '上方'),
            (r'点击?(.*?)上边的', '上方'),
            (r'点击?(.*?)下方的?(.+)', '下方'),
            (r'点击?(.*?)下边的?(.+)', '下方'),
            (r'点击?(.*?)下方', '下方'),
            (r'点击?(.*?)下边的', '下方'),
        ]

        for pattern, direction in patterns:
            match = re.search(pattern, description)
            if match:
                reference = match.group(1).strip()
                target_type = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else None

                # 过滤掉空的目标类型
                if target_type in ['的', '了', '是']:
                    target_type = None

                return {
                    'reference': reference,
                    'direction': direction,
                    'target_type': target_type
                }

        return None

    def find_relative_to_reference(self, reference: str, direction: str, max_distance: int = 200) -> Optional[Dict[str, Any]]:
        """
        查找相对于参考元素的元素

        Args:
            reference: 参考元素的文本描述
            direction: 相对方向（左侧、右侧、上方、下方）
            max_distance: 最大距离（像素）

        Returns:
            找到的元素字典，未找到返回 None
        """
        # 步骤 1: 找到参考元素
        ref_elem = self.helper.find(reference)
        if not ref_elem:
            logger.warning(f"未找到参考元素: {reference}")
            return None

        # 步骤 2: 解析参考元素位置
        ref_bounds = ref_elem.get('bounds', '')
        ref_coords = self.parse_bounds(ref_bounds)
        if not ref_coords:
            logger.warning(f"无法解析参考元素的 bounds: {ref_bounds}")
            return None

        ref_x1, ref_y1, ref_x2, ref_y2 = ref_coords
        ref_center_x = (ref_x1 + ref_x2) // 2
        ref_center_y = (ref_y1 + ref_y2) // 2

        logger.info(f"参考元素 '{reference}' 位置: ({ref_center_x}, {ref_center_y}), bounds: {ref_bounds}")

        # 步骤 3: 获取所有UI元素
        ui_dump = self.device.get_ui_dump_list()

        # 步骤 4: 查找相对位置的元素
        candidates = []

        for elem in ui_dump:
            bounds = elem.get('bounds', '')
            if not bounds:
                continue

            coords = self.parse_bounds(bounds)
            if not coords:
                continue

            x1, y1, x2, y2 = coords
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # 判断方向和距离
            is_in_direction = False
            distance = 0

            if direction == '左侧':
                # 在参考元素左边，且Y坐标有重叠
                if x2 < ref_x1 and not (y2 < ref_y1 or y1 > ref_y2):
                    is_in_direction = True
                    distance = ref_x1 - x2

            elif direction == '右侧':
                # 在参考元素右边，且Y坐标有重叠
                if x1 > ref_x2 and not (y2 < ref_y1 or y1 > ref_y2):
                    is_in_direction = True
                    distance = x1 - ref_x2

            elif direction == '上方':
                # 在参考元素上方，且X坐标有重叠
                if y2 < ref_y1 and not (x2 < ref_x1 or x1 > ref_x2):
                    is_in_direction = True
                    distance = ref_y1 - y2

            elif direction == '下方':
                # 在参考元素下方，且X坐标有重叠
                if y1 > ref_y2 and not (x2 < ref_x1 or x1 > ref_x2):
                    is_in_direction = True
                    distance = y1 - ref_y2

            if is_in_direction and distance <= max_distance:
                candidates.append((distance, elem))

        # 步骤 5: 返回最近的元素
        if candidates:
            candidates.sort(key=lambda x: x[0])
            best_match = candidates[0][1]
            best_distance = candidates[0][0]

            logger.info(f"找到 {len(candidates)} 个候选元素，选择最近的 (距离: {best_distance}px)")

            # 添加评分信息
            best_match['_score'] = 100 - min(best_distance, 100)  # 距离越近分数越高
            best_match['_matched_text'] = f"{reference}{direction}"
            best_match['_distance'] = best_distance

            return best_match

        logger.warning(f"未找到在 {direction} 的元素 (max_distance={max_distance})")
        return None

    def tap_by_nlp(self, description: str) -> bool:
        """
        根据自然语言描述点击图标（支持相对定位）

        Args:
            description: 自然语言描述
                - "点击设置" - 直接文本匹配
                - "点击背词有道左侧的图标" - 相对位置匹配

        Returns:
            是否成功点击
        """
        print(f"\n🔍 查找: \"{description}\"")

        # 策略 1: 尝试解析相对位置描述
        relative_info = self.parse_relative_description(description)

        if relative_info:
            print(f"📍 检测到相对位置描述:")
            print(f"   参考元素: {relative_info['reference']}")
            print(f"   方向: {relative_info['direction']}")
            if relative_info['target_type']:
                print(f"   目标类型: {relative_info['target_type']}")

            # 使用相对位置查找
            icon = self.find_relative_to_reference(
                relative_info['reference'],
                relative_info['direction']
            )

            if icon:
                # 显示匹配信息
                score = icon.get('_score', 0)
                distance = icon.get('_distance', 0)
                text_attr = icon.get('text', '')
                desc_attr = icon.get('content_desc', '')
                class_name = icon.get('class', '').split('.')[-1]
                clickable = icon.get('clickable', False)
                bounds = icon.get('bounds', '')

                # 计算中心点
                coords = self.parse_bounds(bounds)
                center = None
                if coords:
                    x1, y1, x2, y2 = coords
                    center = {'x': (x1 + x2) // 2, 'y': (y1 + y2) // 2}

                print(f"✅ 找到目标元素 (评分: {score}):")
                print(f"   距离参考元素: {distance}px")
                if text_attr:
                    print(f"   text属性: \"{text_attr}\"")
                if desc_attr:
                    print(f"   content-desc: \"{desc_attr}\"")
                print(f"   类型: {class_name}")
                print(f"   可点击: {clickable}")
                if center:
                    print(f"   位置: ({center['x']}, {center['y']})")

                # 点击
                success = self.helper.tap_icon(icon)
                if success:
                    print(f"✅ 成功点击")
                else:
                    print(f"❌ 点击失败")

                return success

        # 策略 2: 尝试直接文本匹配（向后兼容）
        text = description.replace("点击", "").strip()
        icon = self.helper.find(text)

        if icon:
            # 显示匹配信息
            score = icon.get('_score', 0)
            matched_text = icon.get('_matched_text', '')
            text_attr = icon.get('text', '')
            desc_attr = icon.get('content_desc', '')
            class_name = icon.get('class', '').split('.')[-1]
            clickable = icon.get('clickable', False)
            center = icon.get('center', {})

            print(f"✅ 找到最佳匹配 (评分: {score}):")
            print(f"   匹配文本: \"{matched_text}\"")
            if text_attr and text_attr != matched_text:
                print(f"   text属性: \"{text_attr}\"")
            if desc_attr:
                print(f"   content-desc: \"{desc_attr}\"")
            print(f"   类型: {class_name}")
            print(f"   可点击: {clickable}")
            print(f"   位置: ({center.get('x', 0)}, {center.get('y', 0)})")

            # 点击
            success = self.helper.tap_icon(icon)
            if success:
                print(f"✅ 成功点击")
            else:
                print(f"❌ 点击失败")

            return success

        print(f"❌ 未找到匹配的元素")
        return False

    def batch_tap_by_nlp(self, descriptions: List[str]) -> List[bool]:
        """
        批量执行自然语言描述的点击操作

        Args:
            descriptions: 描述列表

        Returns:
            结果列表
        """
        results = []

        for desc in descriptions:
            result = self.tap_by_nlp(desc)
            results.append(result)

            import time
            time.sleep(1)  # 等待操作完成

        return results

    def interactive_mode(self):
        """交互式模式：让用户输入描述并执行"""
        print("\n" + "=" * 60)
        print("自然语言图标点击 - 交互式模式")
        print("=" * 60)
        print("\n输入描述来点击图标，例如：")
        print("  - 点击设置按钮")
        print("  - 点击右上角的菜单图标")
        print("  - 点击底部的学习标签")
        print("  - 点击返回按钮")
        print("\n输入 'quit' 退出\n")

        while True:
            try:
                user_input = input("请输入描述: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q', '退出']:
                    print("\n退出交互模式")
                    break

                if not user_input:
                    continue

                self.tap_by_nlp(user_input)

                import time
                time.sleep(1)

            except KeyboardInterrupt:
                print("\n\n退出交互模式")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")


class AdvancedNLPIconHelper:
    """
    高级 NLP 图标助手 - 可选增强版

    集成了轻量级 NLP 匹配器，提供更强的元素定位能力
    适用于复杂 UI 和模糊匹配场景

    使用方式：
        # 默认使用基础模式（简单快速）
        helper = AdvancedNLPIconHelper(device, mode='basic')

        # 启用高级模式（更准确）
        helper = AdvancedNLPIconHelper(device, mode='advanced')

        # 或者在调用时指定
        helper.tap_by_nlp("点击设置按钮", use_advanced=True)
    """

    def __init__(self, device, mode: str = 'basic', threshold: float = 0.7):
        """
        初始化高级 NLP 图标助手

        Args:
            device: AndroidDeviceManager 实例
            mode: 模式选择
                - 'basic': 使用基础 NLPIconHelper（默认）
                - 'advanced': 启用 NLP 匹配器增强
            threshold: 高级模式的相似度阈值
        """
        self.device = device
        self.mode = mode
        self.basic_helper = NLPIconHelper(device)

        # 延迟导入（避免不必要的依赖）
        if mode == 'advanced':
            try:
                from .nlp_matcher import SimpleNLPMatcher
                self.advanced_matcher = SimpleNLPMatcher(threshold=threshold)
                self.has_advanced = True
            except ImportError:
                logger.warning("SimpleNLPMatcher not available, falling back to basic mode")
                self.has_advanced = False
        else:
            self.has_advanced = False

    def tap_by_nlp(
        self,
        description: str,
        use_advanced: bool = None
    ) -> bool:
        """
        使用自然语言点击元素

        Args:
            description: 元素描述，例如 "点击设置按钮"
            use_advanced: 是否使用高级匹配
                - None: 使用初始化时的 mode 设置
                - True: 强制使用高级匹配
                - False: 强制使用基础匹配

        Returns:
            是否成功点击
        """
        # 决定使用哪种模式
        should_use_advanced = use_advanced if use_advanced is not None else (self.mode == 'advanced')

        if should_use_advanced and self.has_advanced:
            return self._tap_with_advanced(description)
        else:
            return self._tap_with_basic(description)

    def _tap_with_basic(self, description: str) -> bool:
        """使用基础模式点击"""
        return self.basic_helper.tap_by_nlp(description)

    def _tap_with_advanced(self, description: str) -> bool:
        """使用高级模式点击（NLP 匹配器增强）"""
        try:
            # 解析描述，提取关键词
            parsed = self.basic_helper.parse_description(description)
            logger.debug(f"解析描述: {parsed}")

            # 获取当前 UI 元素
            elements = self.device.get_ui_dump_list()
            if not elements:
                logger.warning("无法获取 UI 元素")
                return False

            # 如果解析出明确的文本，优先使用
            if parsed.get('text'):
                query_text = parsed['text']
            else:
                # 从描述中提取关键词（去除动作词）
                query_text = self._extract_query(description)

            # 使用 NLP 匹配器查找元素
            result = self.advanced_matcher.match(elements, query_text)

            if result:
                logger.info(
                    f"✅ 找到匹配: {result.element.get('text', 'N/A')} "
                    f"(策略: {result.strategy}, 分数: {result.score:.2f})"
                )

                # 计算元素中心坐标
                bounds = result.element.get('bounds', '')
                if bounds:
                    x, y = self._calculate_center(bounds)
                    self.device.tap(x, y)
                    return True
                else:
                    logger.warning("元素没有 bounds 信息")
                    return False
            else:
                # 高级模式未找到，降级到基础模式
                logger.info("高级模式未找到，尝试基础模式...")
                return self._tap_with_basic(description)

        except Exception as e:
            logger.error(f"高级模式失败: {e}")
            # 降级到基础模式
            return self._tap_with_basic(description)

    def _extract_query(self, description: str) -> str:
        """
        从描述中提取查询关键词

        去除常见的动作前缀词
        """
        # 移除动作词
        for prefix in ['点击', '选择', '长按', '滑动', '找到', '查找', '搜索']:
            if description.startswith(prefix):
                description = description[len(prefix):]
                break

        # 移除类型后缀
        for suffix in ['按钮', '图标', '标签', '项', '输入框', '文字']:
            if description.endswith(suffix):
                description = description[:-len(suffix)]
                break

        return description.strip()

    def _calculate_center(self, bounds: str) -> tuple:
        """
        计算元素中心坐标

        Args:
            bounds: 边界字符串，例如 "[100,200][300,400]"

        Returns:
            (x, y) 中心坐标
        """
        try:
            # 解析 bounds: "[x1,y1][x2,y2]"
            coords = re.findall(r'\[(\d+),(\d+)\]', bounds)
            if len(coords) == 2:
                x1, y1 = int(coords[0][0]), int(coords[0][1])
                x2, y2 = int(coords[1][0]), int(coords[1][1])
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                return (center_x, center_y)
        except Exception as e:
            logger.error(f"解析 bounds 失败: {e}")

        return (0, 0)


# 演示和测试
if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')

    from rpa_core.android import create_android_device
    import time

    device = create_android_device()
    nlp_helper = NLPIconHelper(device)

    print("=" * 60)
    print("自然语言图标点击演示")
    print("=" * 60)

    # 测试用例
    test_descriptions = [
        "点击学习标签",
        "点击设置按钮",
        "点击返回按钮",
        "点击右上角的菜单图标",
        "点击底部的我的标签",
    ]

    print("\n执行测试用例:\n")

    for desc in test_descriptions:
        print(f"\n描述: {desc}")
        print("-" * 40)

        parsed = nlp_helper.parse_description(desc)
        print(f"解析: {parsed}")

        icon = nlp_helper.find_icon_by_nlp(desc)
        if icon:
            print("✅ 找到图标")
            # 不实际点击，只演示
        else:
            print("❌ 未找到图标")

    # 交互式模式
    print("\n\n" + "=" * 60)
    nlp_helper.interactive_mode()

    device.close()
