# base_adapter.py
# 数据源 API 适配器抽象基类 (内聚 PII 脱敏过滤与 Token Budget 滑动窗口截断机制)

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAdapter(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mock_fallback: bool = config.get("mock_fallback", True)
        self.token_budget_chars: int = config.get("token_budget_chars", 800)

    @abstractmethod
    def retrieve(self, query: str) -> Any:
        """
        核心检索方法由各具体子类实现
        """
        pass

    def filter_pii(self, text: str) -> str:
        """
        前置钩子: 模拟 PII 敏感信息脱敏校验
        """
        # 简单仿真: 脱敏公司名称及敏感地址
        sensitive_keywords = ["华为", "腾讯", "百度", "阿里", "Huawei", "Tencent", "Alibaba"]
        desensitized_text = text
        for kw in sensitive_keywords:
            desensitized_text = desensitized_text.replace(kw, "[SENSITIVE_ENTITY]")
        return desensitized_text

    def truncate_by_budget(self, text: str, focus_keywords: List[str]) -> str:
        """
        后置钩子: Token Budget 滑动窗口截断。
        根据焦点关键词定位核心冲突句段，只保留上下文，其余部分截断。
        """
        if len(text) <= self.token_budget_chars:
            return text

        # 寻找第一个出现的焦点关键词
        match_index = -1
        for kw in focus_keywords:
            idx = text.lower().find(kw.lower())
            if idx != -1:
                match_index = idx
                break

        # 如果没有找到任何关键词，从正中截断
        if match_index == -1:
            match_index = len(text) // 2

        half_budget = self.token_budget_chars // 2
        start_idx = max(0, match_index - half_budget)
        end_idx = min(len(text), match_index + half_budget)

        trimmed_text = text[start_idx:end_idx]
        
        prefix = "...[前部已截断]...\n" if start_idx > 0 else ""
        suffix = "\n...[后部已截断]..." if end_idx < len(text) else ""

        return f"{prefix}{trimmed_text}{suffix}"
