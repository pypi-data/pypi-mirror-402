from __future__ import annotations

import json
import os
from typing import Any, List, Optional

import pandas as pd

from .rules import Rule

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore


class ConfigError(Exception):
    """表示配置文件内容或结构无效的错误。"""


def load_rules(path: str, config_format: Optional[str] = None) -> List[Rule]:
    """从 JSON / YAML / Excel 配置文件中加载规则列表。

    :param path: 配置文件路径
    :param config_format: 显式指定配置格式（json / yaml / excel），缺省根据后缀自动推断
    :return: 规则列表
    :raises FileNotFoundError: 文件不存在
    :raises ConfigError: 配置格式或结构错误
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"配置文件不存在: {path}")

    fmt = (config_format or "").lower().strip()
    if not fmt:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".json":
            fmt = "json"
        elif ext in (".yaml", ".yml"):
            fmt = "yaml"
        elif ext == ".xlsx":
            fmt = "excel"
        else:
            raise ConfigError(f"无法从扩展名推断配置格式: {ext}，请显式指定 config_format")

    if fmt == "json":
        return _load_json_rules(path)
    if fmt == "yaml":
        return _load_yaml_rules(path)
    if fmt == "excel":
        return _load_excel_rules(path)

    raise ConfigError(f"不支持的配置格式: {fmt}")


def _load_json_rules(path: str) -> List[Rule]:
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise ConfigError(f"JSON 格式错误: {exc}") from exc

    return _build_rules_from_dict(data)


def _load_yaml_rules(path: str) -> List[Rule]:
    if yaml is None:
        raise ConfigError("未安装 PyYAML，无法解析 YAML 配置，请安装 PyYAML 或使用 JSON/Excel 配置。")
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except Exception as exc:  # pragma: no cover
            raise ConfigError(f"YAML 格式错误: {exc}") from exc

    return _build_rules_from_dict(data)


def _build_rules_from_dict(data: Any) -> List[Rule]:
    if not isinstance(data, dict):
        raise ConfigError("配置的顶层结构必须是对象/字典。")

    rules: List[Rule] = []

    # 1) 处理 filter_list 简单结构
    filter_list = data.get("filter_list")
    if filter_list is not None:
        if not isinstance(filter_list, dict):
            raise ConfigError("filter_list 必须是字典，键为分类名，值为字符串数组。")
        for label, keywords in filter_list.items():
            if not isinstance(label, str):
                raise ConfigError("filter_list 的键（分类名）必须是字符串。")
            if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
                raise ConfigError(f"分类 '{label}' 的关键词列表必须是字符串数组。")
            rules.append(
                Rule(
                    label=label,
                    any_keywords=list(keywords),
                )
            )

    # 2) 处理 rules 高级结构
    raw_rules = data.get("rules")
    if raw_rules is not None:
        if not isinstance(raw_rules, list):
            raise ConfigError("rules 字段必须是数组列表。")
        for idx, item in enumerate(raw_rules):
            if not isinstance(item, dict):
                raise ConfigError(f"rules[{idx}] 必须是对象/字典。")
            label = item.get("label")
            if not isinstance(label, str) or not label:
                raise ConfigError(f"rules[{idx}] 缺少 label 字段或类型错误。")

            priority = item.get("priority", 100)
            if not isinstance(priority, int):
                raise ConfigError(f"rules[{idx}].priority 必须是整数。")

            exclusive = item.get("exclusive", False)
            if not isinstance(exclusive, bool):
                raise ConfigError(f"rules[{idx}].exclusive 必须是布尔值。")

            any_keywords = _ensure_str_list(item.get("any", []), f"rules[{idx}].any")
            all_keywords = _ensure_str_list(item.get("all", []), f"rules[{idx}].all")
            exclude_keywords = _ensure_str_list(item.get("exclude", []), f"rules[{idx}].exclude")

            rules.append(
                Rule(
                    label=label,
                    priority=priority,
                    exclusive=exclusive,
                    any_keywords=any_keywords,
                    all_keywords=all_keywords,
                    exclude_keywords=exclude_keywords,
                )
            )

    if not rules:
        raise ConfigError("配置中未找到任何规则，请至少提供 filter_list 或 rules 字段。")

    return rules


def _ensure_str_list(value: Any, field_name: str) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ConfigError(f"{field_name} 必须是字符串数组。")
    if not all(isinstance(v, str) for v in value):
        raise ConfigError(f"{field_name} 中的元素必须全部为字符串。")
    return list(value)


def _load_excel_rules(path: str) -> List[Rule]:
    try:
        df = pd.read_excel(path)
    except Exception as exc:  # pragma: no cover
        raise ConfigError(f"读取 Excel 配置失败: {exc}") from exc

    for col in ("label", "keyword"):
        if col not in df.columns:
            raise ConfigError(f"Excel 配置缺少必需列: {col}")

    rules: List[Rule] = []

    grouped = df.groupby("label", dropna=True)
    for label, group in grouped:
        if not isinstance(label, str) or not label:
            continue

        keywords = [
            str(v)
            for v in group["keyword"].tolist()
            if isinstance(v, str) and v
        ]
        if not keywords:
            continue

        # 取该标签第一行的 priority / exclusive 作为整条规则的设置
        priority = 100
        if "priority" in group.columns:
            for v in group["priority"]:
                if pd.notna(v):
                    try:
                        priority = int(v)
                    except (TypeError, ValueError):
                        raise ConfigError(f"标签 '{label}' 的 priority 不是有效整数: {v}")
                    break

        exclusive = False
        if "exclusive" in group.columns:
            for v in group["exclusive"]:
                if pd.isna(v):
                    continue
                if isinstance(v, bool):
                    exclusive = v
                    break
                if isinstance(v, str):
                    val = v.strip().lower()
                    if val in ("true", "1", "yes", "y"):
                        exclusive = True
                        break
                    if val in ("false", "0", "no", "n"):
                        exclusive = False
                        break
                raise ConfigError(f"标签 '{label}' 的 exclusive 必须是布尔或可识别的字符串: {v}")

        rules.append(
            Rule(
                label=label,
                priority=priority,
                exclusive=exclusive,
                any_keywords=keywords,
            )
        )

    if not rules:
        raise ConfigError("Excel 配置中未解析出任何有效规则。")

    return rules
