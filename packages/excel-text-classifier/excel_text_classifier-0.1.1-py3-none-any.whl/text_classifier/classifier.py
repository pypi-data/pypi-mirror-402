from __future__ import annotations

import os
from typing import Callable, List, Optional, Sequence

import pandas as pd

from .config_loader import ConfigError, load_rules
from .io_excel import read_excel, write_excel_with_column
from .rules import Rule


def classify_text(text: str, rules: Sequence[Rule], case_sensitive: bool = False) -> str:
    """对单条文本进行分类，返回逗号分隔的标签字符串。

    :param text: 待分类文本
    :param rules: 已加载的规则列表
    :param case_sensitive: 是否大小写敏感
    :return: 逗号分隔的标签字符串；若未命中任何标签则返回空字符串
    """
    if text is None:
        return ""

    labels: List[str] = []

    ordered_rules = sorted(rules, key=lambda r: (r.priority, r.label))

    for rule in ordered_rules:
        if rule.matches(text, case_sensitive=case_sensitive):
            labels.append(rule.label)
            if rule.exclusive:
                break

    if not labels:
        return ""

    unique_labels = sorted(set(labels))
    return ",".join(unique_labels)


def classify_series(
    texts: pd.Series,
    rules: Sequence[Rule],
    case_sensitive: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> pd.Series:
    """对 pandas Series 中的每条文本进行分类。

    :param texts: 文本列（Series）
    :param rules: 规则列表
    :param case_sensitive: 是否大小写敏感
    :param progress_callback: 可选的进度回调函数，参数为 (已处理数量, 总数)
    :return: 包含标签字符串的新 Series
    """
    if progress_callback is None:
        return texts.fillna("").apply(lambda x: classify_text(x, rules, case_sensitive=case_sensitive))

    filled = texts.fillna("")
    total = len(filled)
    labels: List[str] = []

    for idx, value in enumerate(filled, start=1):
        labels.append(classify_text(value, rules, case_sensitive=case_sensitive))
        progress_callback(idx, total)

    return pd.Series(labels, index=texts.index)


def classify_excel(
    input_file: str,
    config_file: str,
    text_column: str,
    sheet_name: Optional[str] = None,
    output_file: Optional[str] = None,
    output_column: str = "classification_tags",
    config_format: Optional[str] = None,
    case_sensitive: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> str:
    """对 Excel 文件中指定列的文本进行分类，并将结果写入新列。

    :param input_file: 输入 Excel 文件路径
    :param config_file: 配置文件路径（JSON/YAML/Excel）
    :param text_column: 文本列名
    :param sheet_name: 工作表名；为 None 时使用默认表
    :param output_file: 输出文件路径；为 None 时自动在文件名后添加 _classified
    :param output_column: 输出标签列名
    :param config_format: 配置格式（json/yaml/excel）；为 None 时根据后缀自动推断
    :param case_sensitive: 是否大小写敏感
    :param progress_callback: 可选的进度回调函数，参数为 (已处理数量, 总数)
    :return: 实际写入的输出文件路径
    """
    df = read_excel(input_file, sheet_name=sheet_name)

    if text_column not in df.columns:
        available = ", ".join(map(str, df.columns))
        raise KeyError(f"文本列 '{text_column}' 不存在，可用列名: {available}")

    rules = load_rules(config_file, config_format=config_format)

    labels_series = classify_series(
        df[text_column],
        rules,
        case_sensitive=case_sensitive,
        progress_callback=progress_callback,
    )
    df[output_column] = labels_series

    if output_file is None:
        base, ext = os.path.splitext(input_file)
        if not ext:
            ext = ".xlsx"
        output_file = f"{base}_classified{ext}"

    write_excel_with_column(df, output_file)

    return output_file
