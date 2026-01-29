#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re


def remove_extra_spaces(text: str) -> str:
    """
    移除混合字符串中多余的空格
    """
    # 匹配中文字符之间的空格
    pattern1 = r"(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])\s+(?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"

    # 匹配中英文字符之间的空格
    pattern2 = r"(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])\s+(?=[a-zA-Z])|(?<=[a-zA-Z])\s+(?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"

    # 匹配中文字符与英文符号之间的空格
    pattern3 = r"(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])\s+(?=[\[\]\(\)\{\}\"\'\:\;\?\!\,\.\`\~])|(?<=[\[\]\(\)\{\}\"\'\:\;\?\!\,\.\`\~])\s+(?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])"

    # 处理英文单词与标点之间的空格
    pattern4a = r"(\w)\s+([^\w\s])"  # 单词和标点之间无空格
    pattern4b = r"([^\w\s])\s+(\w)"  # 标点和单词之间保留一个空格
    pattern4c = r"(\w)\s{2,}(\w)"    # 单词间多余空格替换为一个空格

    # 处理英文符号之间的多余空格
    pattern5 = r"([^\w\s])\s{2,}([^\w\s])"
    
    # 移除英文标点之间的空格
    pattern7 = r"([^\w\s])\s+([^\w\s])"
    
    # 按顺序处理各种空格
    text = re.sub(pattern2, "", text)  # 处理中英文之间的空格
    text = re.sub(pattern1, "", text)  # 处理中文之间的空格
    text = re.sub(pattern3, "", text)  # 处理中文与英文符号之间的空格
    text = re.sub(pattern4a, r"\1\2", text)   # 单词和标点之间无空格
    text = re.sub(pattern4b, r"\1 \2", text)  # 标点和单词之间保留一个空格
    text = re.sub(pattern4c, r"\1 \2", text)  # 单词间多余空格替换为一个空格
    text = re.sub(pattern5, r"\1\2", text)    # 处理英文符号之间的多余空格
    text = re.sub(pattern7, r"\1\2", text)    # 移除英文标点之间的空格

    return text


def count_eff_len(text: str) -> int:
    """
    根据指定规则统计文本字数，支持：
    - i'm, don't 等带撇号单词计为 1 字
    - 数字、等式、日期等复杂结构整体计 1 字
    - 所有标点各计 1 字
    """
    if not text or not text.strip():
        return 0

    # 预处理：统一空白字符
    text = re.sub(r"\s+", " ", text.strip())
    count = 0
    remaining_text = text

    # 1. 带连接符的数字（如日期、电话、版本号）
    connected_numbers = re.findall(r"\b\d+[-\/.]\d+(?:[-\/.]\d+)*\b", remaining_text)
    count += len(connected_numbers)
    for match in connected_numbers:
        remaining_text = remaining_text.replace(match, " ", 1)

    # 2. 简单等式和比较式（如 1+1=2, x>y, 5<=10）
    equations = re.findall(
        r"\b(?:\d+|[a-zA-Z])+(?:[+\-*/=<>≤≥]+(?:\d+|[a-zA-Z])+)+\b", remaining_text
    )
    count += len(equations)
    for match in equations:
        remaining_text = remaining_text.replace(match, " ", 1)

    # 3. 各种数字：整数、小数、百分数、分数
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?|\d+/\d+\b", remaining_text)
    valid_numbers = [n for n in numbers if re.search(r"\d", n)]
    count += len(valid_numbers)
    for match in valid_numbers:
        remaining_text = remaining_text.replace(match, " ", 1)

    # 3a. 特殊处理中文文本中的年份（4位数字+年）
    years = re.findall(r"\d{4}(?=年)", remaining_text)
    count += len(years)
    for match in years:
        remaining_text = remaining_text.replace(match + "年", "年", 1)

    # 4. 英文单词（含撇号，如 i'm, don't, it's, can't，以及下划线连接的单词）
    # 使用之前调试时工作正常的正则表达式
    words = re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*(?![\u4e00-\u9fff\uf900-\ufaff])", remaining_text)
    # 过滤掉纯下划线和没有字母的词
    english_words = [w for w in words if re.search(r"[a-zA-Z]", w)]
    count += len(english_words)
    for match in english_words:
        remaining_text = remaining_text.replace(match, " ", 1)

    # 5. 中文字符（含中文标点）
    chinese_chars = re.findall(r"[\u4e00-\u9fff\uf900-\ufaff]", remaining_text)
    count += len(chinese_chars)
    for char in chinese_chars:
        remaining_text = remaining_text.replace(char, " ", 1)

    # 6. 剩余的所有标点符号（中英文）
    punctuation = re.findall(r"[^\w\s]", remaining_text)
    count += len(punctuation)

    return count


def fix_punctuation(text):
    """修复文本的标点符号"""
    def replace_punc(match):
        punc = match.group()
        return {
            ',': '，',
            '.': '。',
            ';': '；',
            ':': '：',
            '?': '？',
            '!': '！',
            '(': '（',
            ')': '）',
        }.get(punc, punc)
    
    pattern = r'(?<=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef])[,.;:?!()](?=[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\s])'
    text = re.sub(pattern, replace_punc, text)
    
    text = re.sub(r'，+', '，', text)
    text = re.sub(r'。+', '。', text)
    
    return text