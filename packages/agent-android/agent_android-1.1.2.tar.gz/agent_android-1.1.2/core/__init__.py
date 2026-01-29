"""
agent-android Core Module

Android ADB 自动化核心模块
"""

from .android import AndroidDeviceManager, create_android_device
from .adb_config import ADBConfig
from .icon_helper import IconHelper
from .nlp_icon_helper import NLPIconHelper, AdvancedNLPIconHelper
from .ai_client import AndroidAIClient, create_ai_client, analyze_screenshot
from .ui_analyzer import UIAnalyzer, create_ui_analyzer

__all__ = [
    'AndroidDeviceManager',
    'create_android_device',
    'ADBConfig',
    'IconHelper',
    'NLPIconHelper',
    'AdvancedNLPIconHelper',  # 新增：高级 NLP 助手
    'AndroidAIClient',
    'create_ai_client',
    'analyze_screenshot',
    'UIAnalyzer',
    'create_ui_analyzer',
]

__version__ = '1.3.0'
