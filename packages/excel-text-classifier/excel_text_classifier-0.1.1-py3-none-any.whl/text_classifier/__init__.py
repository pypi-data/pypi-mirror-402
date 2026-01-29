"""
text_classifier

Excel 多标签文本分类工具，支持 JSON / YAML / Excel 规则配置，
包含规则优先级、排他性标签和组合条件（any/all/exclude）。
"""

from .rules import Rule
from .config_loader import load_rules
from .classifier import classify_text, classify_series, classify_excel

__all__ = [
    "Rule",
    "load_rules",
    "classify_text",
    "classify_series",
    "classify_excel",
]

__version__ = "0.1.0"
