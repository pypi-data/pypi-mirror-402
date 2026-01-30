# Complex Text Tools

[![PyPI version](https://badge.fury.io/py/complex-text-tools.svg)](https://badge.fury.io/py/complex-text-tools)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/complex-text-tools)
![PyPI - License](https://img.shields.io/pypi/l/complex-text-tools)

一个用于处理包含中英文混合字符的复杂文本的Python包，能够移除多余空格并根据特定规则计算文本长度。

## 功能特性

- 移除中文字符之间的多余空格
- 移除中英文字符之间的多余空格
- 正确处理标点符号周围的间距
- 根据特定规则计算文本长度（中文字符、英文单词、数字、等式等）
- 修复中文文本中的标点符号（将英文标点转换为中文标点）
- 高效处理混合语言文本

## 安装

```bash
pip install complex-text-tools
```

## 使用方法

### 移除多余空格

```python
from complex_text_tools import remove_extra_spaces

text = "这 是  中文 测试  文本 ，  mixed  English  text  here ， 还 有   symbols :  ;  !  "
clean_text = remove_extra_spaces(text)
print(clean_text)
# 输出: "这是中文测试文本，mixed English text here，还有 symbols:;!"
```

### 计算有效文本长度

```python
from complex_text_tools import count_eff_len

text = "这是一段包含 English words 和 123.45 数字的 mixed 文本"
result = count_eff_len(text)
print(result)
# 输出:15
```

### 修复标点符号

```python
from complex_text_tools import fix_punctuation

text = "这是中文文本，但使用了英文标点.这看起来不太自然，对吗？"
fixed_text = fix_punctuation(text)
print(fixed_text)
# 输出: "这是中文文本，但使用了中文标点。这看起来不太自然，对吗？"
```

## 许可证

该项目基于 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件。