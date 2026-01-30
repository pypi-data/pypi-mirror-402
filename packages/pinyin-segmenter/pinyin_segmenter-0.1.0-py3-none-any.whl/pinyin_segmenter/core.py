import string
import unicodedata
from typing import List, Optional, Set
from pypinyin.constants import PINYIN_DICT

__all__ = [
    "PinyinSegmenter",
    "segment_pinyin",
]


class PinyinSegmenter:
    """拼音分割器，用于将连续的拼音字符串分割为有效的拼音片段"""

    # 定义所有可能的声母（包括复合声母）
    INITIALS = {
        "zh",
        "ch",
        "sh",
        "b",
        "p",
        "m",
        "f",
        "d",
        "t",
        "n",
        "l",
        "g",
        "k",
        "h",
        "j",
        "q",
        "x",
        "z",
        "c",
        "s",
        "r",
        "y",
        "w",
    }

    # 定义所有可能的韵母（用于辅助判断）
    FINALS = {
        "a",
        "o",
        "e",
        "i",
        "u",
        "v",
        "ai",
        "ei",
        "ui",
        "ao",
        "ou",
        "iu",
        "ie",
        "ve",
        "er",
        "an",
        "en",
        "in",
        "un",
        "vn",
        "ang",
        "eng",
        "ing",
        "ong",
    }

    # 特殊韵母组合
    SPECIAL_FINALS = {"er", "ng"}

    # 元音字母集合
    VOWELS = {"a", "o", "e", "i", "u", "v"}

    # 最大拼音长度
    MAX_PINYIN_LENGTH = 6

    def __init__(self):
        """初始化拼音分割器，构建合法的拼音集合"""
        self._pinyin_set: Set[str] = self._build_pinyin_set()

    @staticmethod
    def _remove_tone_unicode(pinyin_str: str) -> str:
        """去除Unicode声调符号

        Args:
            pinyin_str: 带声调的拼音字符串

        Returns:
            去除声调后的拼音字符串
        """
        nfd_str = unicodedata.normalize("NFD", pinyin_str)
        return "".join(char for char in nfd_str if unicodedata.category(char) != "Mn")

    def _build_pinyin_set(self) -> Set[str]:
        """构建合法的拼音集合

        Returns:
            所有合法拼音的集合
        """
        pinyin_set = set()

        for words in PINYIN_DICT.values():
            clean_words = self._remove_tone_unicode(words)
            for word in clean_words.split(","):
                pinyin_set.add(word)

        return pinyin_set

    def segment(self, pinyin_str: str) -> List[str]:
        """分割拼音字符串

        Args:
            pinyin_str: 待分割的拼音字符串

        Returns:
            分割后的拼音列表，如果无法分割则返回空列表
        """
        # 清理输入字符串，只保留小写字母
        clean_pinyin = "".join(
            char.lower()
            for char in pinyin_str
            if char.isalpha() and char.lower() in string.ascii_lowercase
        )

        if not clean_pinyin:
            return []

        # 尝试从长到短的所有可能子串
        for length in range(len(clean_pinyin), 1, -1):
            for start in range(len(clean_pinyin) - length + 1):
                substring = clean_pinyin[start : start + length]
                result = self._segment_substring(substring)
                if result:
                    return result

        return []

    def _segment_substring(self, pinyin_str: str) -> Optional[List[str]]:
        """分割子字符串

        Args:
            pinyin_str: 待分割的拼音子字符串

        Returns:
            分割结果列表或None（如果无法分割）
        """
        results: List[List[str]] = []
        self._recursive_segment(pinyin_str, 0, [], results)

        return results[0] if results else None

    def _recursive_segment(
        self, pinyin_str: str, start: int, current: List[str], results: List[List[str]]
    ) -> bool:
        """递归分割拼音字符串

        Args:
            pinyin_str: 完整的拼音字符串
            start: 当前起始位置
            current: 当前分割路径
            results: 存储所有有效结果的列表

        Returns:
            是否成功分割
        """
        if start >= len(pinyin_str):
            results.append(current.copy())
            return True

        # 尝试不同长度的分割，优先尝试更长的分割
        max_len = min(self.MAX_PINYIN_LENGTH, len(pinyin_str) - start)

        for length in range(max_len, 0, -1):
            segment = pinyin_str[start : start + length]

            if self._is_valid_segment(segment):
                current.append(segment)

                # 递归分割剩余部分
                if self._recursive_segment(
                    pinyin_str, start + length, current, results
                ):
                    return True

                # 回溯
                current.pop()

        return False

    def _is_valid_segment(self, segment: str) -> bool:
        """检查片段是否为合法拼音

        Args:
            segment: 待检查的拼音片段

        Returns:
            是否为合法拼音
        """
        # 基础检查
        if not segment or len(segment) > self.MAX_PINYIN_LENGTH:
            return False

        if not segment.isalpha() or not segment.islower():
            return False

        # 结构检查
        if not self._check_pinyin_structure(segment):
            return False

        # 最终检查：是否在预编译的拼音集合中
        return segment in self._pinyin_set

    def _check_pinyin_structure(self, segment: str) -> bool:
        """检查拼音结构是否合法

        Args:
            segment: 待检查的拼音片段

        Returns:
            结构是否合法
        """
        # 零声母情况
        if segment[0] in self.VOWELS:
            return segment in self.FINALS

        # 复合声母情况
        if len(segment) >= 2 and segment[:2] in {"zh", "ch", "sh"}:
            return len(segment) > 2 and self._is_valid_final_part(segment[2:])

        # 单声母情况
        if segment[0] in self.INITIALS:
            return len(segment) > 1 and self._is_valid_final_part(segment[1:])

        return False

    def _is_valid_final_part(self, final_part: str) -> bool:
        """检查韵母部分是否有效

        Args:
            final_part: 韵母部分

        Returns:
            韵母是否有效
        """
        if not final_part:
            return False

        # 完整的韵母
        if final_part in self.FINALS:
            return True

        # 包含特殊韵母组合
        if any(special in final_part for special in self.SPECIAL_FINALS):
            return True

        # 以元音开头
        return final_part[0] in self.VOWELS


def segment_pinyin(pinyin_str: str) -> List[str]:
    """便捷函数：分割拼音字符串

    Args:
        pinyin_str: 待分割的拼音字符串

    Returns:
        分割后的拼音列表
    """
    segmenter = PinyinSegmenter()
    return segmenter.segment(pinyin_str)
