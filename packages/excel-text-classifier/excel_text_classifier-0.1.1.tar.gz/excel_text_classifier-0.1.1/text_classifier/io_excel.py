from __future__ import annotations

from typing import Optional

import pandas as pd


def read_excel(path: str, sheet_name: str | int | None = None) -> pd.DataFrame:
    """读取 Excel 文件并返回 DataFrame。

    :param path: Excel 文件路径
    :param sheet_name: 工作表名称；为 None 时读取第一个工作表 (index 0)
    :return: DataFrame
    """
    # pandas 中 sheet_name=None 会读取所有 sheet 并返回字典
    # 这里我们默认读取第一个 sheet (0)
    target_sheet = sheet_name if sheet_name is not None else 0
    return pd.read_excel(path, sheet_name=target_sheet)


def write_excel_with_column(df: pd.DataFrame, path: str) -> None:
    """将 DataFrame 写回 Excel 文件。

    :param df: 数据表
    :param path: 输出文件路径
    """
    df.to_excel(path, index=False)
