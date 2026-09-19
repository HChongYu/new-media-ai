"""节点公共工具：LLM JSON 输出的容错解析"""
import json
import re
from typing import Any


def parse_json_array(raw: str) -> list[dict[str, Any]] | None:
    """
    从 LLM 输出中提取 JSON 数组。

    依次尝试：
    1. 整体 json.loads
    2. ```json ... ``` 代码块
    3. 第一个 [ 到最后一个 ] 的切片
    """
    if not raw:
        return None

    candidates = [raw.strip()]

    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        candidates.append(fence.group(1).strip())

    start, end = raw.find("["), raw.rfind("]") + 1
    if start != -1 and end > start:
        candidates.append(raw[start:end])

    for text in candidates:
        try:
            data = json.loads(text)
            if isinstance(data, list) and data:
                return data
        except (json.JSONDecodeError, TypeError):
            continue
    return None
