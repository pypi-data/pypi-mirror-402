from dataclasses import dataclass, field
from typing import List


@dataclass
class Rule:
    """表示一条文本分类规则。

    :param label: 标签名称/分类名称
    :param priority: 优先级，数值越小越高，决定规则评估顺序
    :param exclusive: 是否为排他规则；命中后将停止评估低优先级规则
    :param any_keywords: 任意包含这些关键词之一即满足（OR）
    :param all_keywords: 必须全部包含这些关键词才满足（AND）
    :param exclude_keywords: 如果包含这些关键词中的任意一个则不命中（NOT）
    """

    label: str
    priority: int = 100
    exclusive: bool = False
    any_keywords: List[str] = field(default_factory=list)
    all_keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)

    def matches(self, text: str, case_sensitive: bool = False) -> bool:
        """判断指定文本是否命中本规则。

        :param text: 待匹配文本
        :param case_sensitive: 是否大小写敏感
        :return: 是否命中本规则
        """
        if not text:
            return False

        candidate = text if case_sensitive else text.lower()

        def norm_list(values: List[str]) -> List[str]:
            if case_sensitive:
                return [v for v in values if v]
            return [v.lower() for v in values if v]

        any_list = norm_list(self.any_keywords)
        all_list = norm_list(self.all_keywords)
        exclude_list = norm_list(self.exclude_keywords)

        # NOT: 出现任一 exclude 则直接不命中
        for kw in exclude_list:
            if kw and kw in candidate:
                return False

        # AND: all_list 中每个都必须出现
        if all_list:
            for kw in all_list:
                if kw and kw not in candidate:
                    return False

        # OR: any_list 至少一个出现；若 any_list 为空，则表示“不限制”
        if any_list:
            return any(kw in candidate for kw in any_list)

        # 没有 any_list，且 all 条件已满足，则视为命中
        return True
