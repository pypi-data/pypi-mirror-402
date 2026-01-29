"""
Complex Text Tools - A package for processing complex text with mixed Chinese and English characters.

This package provides utilities for:
1. Removing extra spaces in mixed-language texts
2. Counting effective text length according to specific rules
"""

from .text_processor import remove_extra_spaces, count_eff_len, fix_punctuation

__all__ = ['remove_extra_spaces', 'count_eff_len', 'fix_punctuation']
__version__ = '0.2.3'