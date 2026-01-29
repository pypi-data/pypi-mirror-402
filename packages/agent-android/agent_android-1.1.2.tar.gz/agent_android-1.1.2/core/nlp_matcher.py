"""
轻量级 NLP 元素匹配器 - agent-android 增强版

简化版 NLP 匹配，专为 agent-android 设计
- 无自动调优（保持轻量）
- 核心策略：精确、包含、相似度
- 零外部依赖（只使用标准库）
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    """匹配结果"""
    element: Dict[str, Any]
    score: float
    strategy: str


class SimpleNLPMatcher:
    """
    简单的 NLP 元素匹配器

    只包含核心匹配策略，无自动调优
    适合集成到 agent-android 等轻量级项目
    """

    def __init__(self, threshold: float = 0.7):
        """
        初始化匹配器

        Args:
            threshold: 相似度阈值（0.0-1.0）
        """
        self.threshold = threshold

    def match(
        self,
        elements: List[Dict[str, Any]],
        query: str
    ) -> Optional[MatchResult]:
        """
        使用多种策略匹配元素

        Args:
            elements: 元素列表
            query: 查询文本

        Returns:
            MatchResult 或 None
        """
        # 策略 1: 精确匹配
        result = self._exact_match(elements, query)
        if result:
            return result

        # 策略 2: 包含匹配
        result = self._contains_match(elements, query)
        if result:
            return result

        # 策略 3: 相似度匹配
        result = self._similarity_match(elements, query)
        if result:
            return result

        return None

    def _exact_match(
        self,
        elements: List[Dict[str, Any]],
        query: str
    ) -> Optional[MatchResult]:
        """精确匹配"""
        for elem in elements:
            text = elem.get('text', '')
            if text == query:
                return MatchResult(
                    element=elem,
                    score=1.0,
                    strategy='exact'
                )
        return None

    def _contains_match(
        self,
        elements: List[Dict[str, Any]],
        query: str
    ) -> Optional[MatchResult]:
        """包含匹配"""
        best_match = None
        best_score = 0.0

        for elem in elements:
            text = elem.get('text', '')
            if query in text:
                # Jaccard 相似度
                score = self._jaccard_similarity(query, text)
                if score > best_score:
                    best_score = score
                    best_match = elem

        if best_match:
            return MatchResult(
                element=best_match,
                score=best_score,
                strategy='contains'
            )
        return None

    def _similarity_match(
        self,
        elements: List[Dict[str, Any]],
        query: str
    ) -> Optional[MatchResult]:
        """相似度匹配（Jaccard）"""
        best_match = None
        best_score = 0.0

        for elem in elements:
            text = elem.get('text', '')
            if not text:
                continue

            score = self._jaccard_similarity(query, text)
            if score >= self.threshold and score > best_score:
                best_score = score
                best_match = elem

        if best_match:
            return MatchResult(
                element=best_match,
                score=best_score,
                strategy='similarity'
            )
        return None

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """
        计算 Jaccard 相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0.0-1.0）
        """
        set1 = set(text1)
        set2 = set(text2)

        if not set1 or not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0


# 便捷函数
def find_element(
    elements: List[Dict[str, Any]],
    query: str,
    threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    便捷函数：查找匹配的元素

    Args:
        elements: 元素列表
        query: 查询文本
        threshold: 相似度阈值

    Returns:
        匹配的元素或 None
    """
    matcher = SimpleNLPMatcher(threshold=threshold)
    result = matcher.match(elements, query)
    return result.element if result else None
