# Handoff Report: bigquery_adapter.py 与 llm_factory.py 的修复策略

## 1. Observation (观察结果)
- 在 `server/adapters/bigquery_adapter.py` 中：
  - 第 64 行：`focus_keywords = [kw for kw in ["流", "stream", "中断", "pause", "恢复", "resume"] if kw in query.lower()]` 硬编码了搜索的关键字列表。
  - 第 97 行：`regex_pattern = "|".join(focus_keywords) if focus_keywords else "agent|stream|pause|resume"` 硬编码了兜底的正则匹配词。
  - 第 140-147 行：代码使用了 `if "stream" in claim_lower or "stream" in title.lower():` 进行显式判断，并强行注入了诸如 `"SSE流式传输"` 和 `"法官协调代理"` 等虚假的 mock 特征，导致无法根据真实的专利文本动态生成特征。
- 在 `server/llm_factory.py` 中：
  - 第 354 行：`props = tool_schema.get("function", {}).get("parameters", {}).get("properties")`。当 JSON Schema 中的 `parameters` 被显式设置为 `null`（解析为 `None`）时，`.get("parameters", {})` 会直接返回 `None` 而不是 `{}`。随后调用的 `.get("properties")` 会抛出 `AttributeError: 'NoneType' object has no attribute 'get'`，导致在执行到 `props.items()` 之前就发生崩溃。

## 2. Logic Chain (逻辑链)
- 针对 **`bigquery_adapter.py`**：为了提供真实的通用搜索能力，必须移除这些硬编码的拦截逻辑。`focus_keywords` 应当通过从用户的 `query` 中提取有意义的英文字符串或词汇来动态生成。同时，必须移除硬编码的模拟特征注入逻辑，改为通过对查询到的真实专利摘要或权利要求 (`claim_text`) 进行分句截取，以此来动态提取和生成 `features`。
- 针对 **`llm_factory.py`**：Python 的字典 `get(key, default)` 方法在键存在但值为 `None` 时，会直接返回 `None`。因此，仅在 `get` 中提供 `{}` 作为默认值不足以应对显式包含 `null` 的 LLM 工具 Schema。我们必须使用 Python 的 `or {}` 语法结构，在每一层级提取时对 `None` 值进行兜底替换，确保能安全地向下链式查找并执行 `.items()` 遍历。

## 3. Caveats (注意事项)
- 针对 `bigquery_adapter.py` 修改后的通用文本提取逻辑：其生成的特征（通过句号等标点符号分割提取）在格式上可能没有手动硬编码的内容工整，存在截取部分不完整或含有无关助词的可能。
- 直接利用正则（如 `\b[A-Za-z]{4,}\b`）从 `query` 提取关键词可能会包含一些英文停用词。但作为 BigQuery 的基础正则匹配回退方案，足以满足通用查询的需求。

## 4. Conclusion (结论)
我们应当按照以下策略执行修复：
1. **修复 `llm_factory.py`（增加 Null 值安全校验）**：
   将第 354-356 行的字典提取逻辑修改为安全的逐层 `or {}` 判断：
   ```python
   func = tool_schema.get("function") or {}
   params = func.get("parameters") or {}
   props = params.get("properties") or {}
   mock_args = {}
   for k, v in props.items():
   ```
2. **修复 `bigquery_adapter.py`（移除硬编码拦截）**：
   - 将第 64 行替换为动态提取查询内容的词汇，例如：`import re; focus_keywords = [w.lower() for w in re.findall(r'\b[A-Za-z]{4,}\b', query)]`。
   - 彻底删除第 137-148 行关于 `"stream"` 的条件判断与硬编码特征注入，将其替换为基于 `claim_text` 的动态句子分割与特征提取逻辑：
   ```python
   features = []
   import re
   sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', claim_text) if len(s.strip()) > 20]
   if not sentences:
       sentences = [claim_text[:100]]
   for i, sentence in enumerate(sentences[:3]):
       features.append({"id": f"{pid}_F{i+1}", "text": sentence, "focus": f"Extracted Feature {i+1}"})
   ```

## 5. Verification Method (验证方法)
- **对于 `llm_factory.py`**：可以编写一个简单的本地 Python 测试脚本，调用包含显式 `None` 参数的 mock 工具 schemas（例如 `tools=[{"type": "function", "function": {"name": "test", "parameters": None}}]`），验证其能否平稳运行不再抛出 `AttributeError`。
- **对于 `bigquery_adapter.py`**：向 Adapter 传入一个完全不相关的自然 query（例如 `"machine learning classification"`）进行测试。检查代码打出的日志，确认生成的 SQL 正则表达式采用的是从 query 中提取的关键字，并检查返回的专利数据字典，确认 `features` 字段中已不再出现 `"SSE流式传输"` 或 `"法官协调代理"` 等硬编码信息。
