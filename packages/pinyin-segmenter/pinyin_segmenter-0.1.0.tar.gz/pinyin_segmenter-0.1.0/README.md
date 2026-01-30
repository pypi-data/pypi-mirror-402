# Pinyin Segmenter 拼音分割器

[![Python Versions](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/pinyin-segmenter.svg)](https://pypi.org/project/pinyin-segmenter/)

一个高效的中文拼音分割器，用于将连续的拼音字符串分割为有效的拼音片段。

## 功能特点

- ✅ **准确分割**：能够准确分割连续的拼音字符串
- ✅ **智能识别**：支持带声调和不带声调的拼音
- ✅ **高效算法**：使用递归回溯算法，性能优秀
- ✅ **完整覆盖**：基于 pypinyin 的标准拼音字典
- ✅ **易于使用**：简洁的 API 接口

## 安装

### 使用 pip 安装

```bash
pip install pinyin-segmenter
```

## 快速开始

### 基础用法


```python
from pinyin_segmenter import PinyinSegmenter, segment_pinyin

# 创建分割器实例
segmenter = PinyinSegmenter()

# 分割连续的拼音字符串
result = segmenter.segment("zhongguoren")
print(result)  # 输出: ['zhong', 'guo', 'ren']

# 使用便捷函数
result = segment_pinyin("nihao")
print(result)  # 输出: ['ni', 'hao']
```

### 更多示例


```python
from pinyin_segmenter import segment_pinyin

# 示例 1：基本分割
print(segment_pinyin("woaizhongguo"))  # ['wo', 'ai', 'zhong', 'guo']

# 示例 2：长字符串分割
print(segment_pinyin("mingyuejishiyoubajiuwenqingtian。")) # ['ming', 'yue', 'ji', 'shi', 'you', 'ba', 'jiu', 'wen', 'qing', 'tian']

# 示例 3：特殊拼音
print(segment_pinyin("erzi"))  # ['er', 'zi']

# 示例 4：无法分割的情况
print(segment_pinyin("xyz"))  # []
```


## API 文档

### PinyinSegmenter 类

    PinyinSegmenter()

        创建拼音分割器实例。

    segment(pinyin_str: str) -> List[str]

        分割拼音字符串。

        参数:

            pinyin_str: 待分割的拼音字符串（可以包含声调符号）

        返回:

            分割后的拼音列表，如果无法分割则返回空列表。 

### segment_pinyin(pinyin_str: str) -> List[str] 便捷函数

    使用 PinyinSegmenter 将拼音字符串分割。

    参数:
        pinyin_str: 待分割的拼音字符串（可以包含声调符号）
    返回:
        分割后的拼音列表，如果无法分割则返回空列表。


## 工作原理

拼音分割器基于以下原理工作：

- 字典匹配：使用标准的拼音字典进行匹配
- 结构验证：检查拼音的声母-韵母结构是否合法
- 递归回溯：使用深度优先搜索算法寻找所有可能的分割方案
- 最长匹配：优先尝试较长的拼音匹配
- 支持的拼音特征：
    - 所有标准声母（包括 zh, ch, sh）
    - 所有标准韵母（包括 er, ng 等特殊组合）
    - 自动去除 Unicode 声调符号

## 注意（AI生成标识）

- 本代码核心算法由DeepSeek大模型生成和完善。
- 包管理者对由AI生成的代码局部进行了修改和优化。

## 版本信息

### v0.1.0

- 初始版本发布
- 实现核心分割功能
- 提供完整的 API 接口
- 添加测试用例
