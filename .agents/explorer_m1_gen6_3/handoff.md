# 核心发现与问题定位

## 1. Observation
- **`server/adapters/bigquery_adapter.py`**:
  - 第 64 行：`focus_keywords` 依赖硬编码的流控关键字列表 `["流", "stream", "中断", "pause", "恢复", "resume"]`。
  - 第 97 行：`regex_pattern` 回退值被硬编码为 `"agent|stream|pause|resume"`。
  - 第 137-148 行：`features` 数组被完全硬编码。如果文本包含 "stream"，则注入 `"focus": "SSE流式传输"` 等强设定的特征词；否则注入 `"focus": "法官协调代理"`，这是典型的硬编码门面模式（Facade），并没有将真实的专利数据泛化给下游 Agent 使用。
- **`server/llm_factory.py`**:
  - 第 354 行：存在不安全的链式调用 `props = tool_schema.get("function", {}).get("parameters", {}).get("properties")`。当 JSON 显式传递 `"parameters": null` 时，中间的 `.get("parameters", {})` 会返回 `None` 而不是默认值 `{}`（因为键存在但值为 null）。导致下一步对 `None` 执行 `.get("properties")` 时抛出 `AttributeError: 'NoneType' object has no attribute 'get'`，并在字典属性抽取和遍历 (`.items()`) 时引发系统崩溃。

## 2. Logic Chain
- **BigQuery Adapter 通用化修复策略**：为了将真实的专利数据回传给下游 Agent，必须移除根据 "stream" 关键字进行分支注入的 `if-else`。泛化的解决策略是：根据文本内容（`claim_text` 或 `abstract`）按标准分隔符（如分号、句号）进行动态切分，将真实文本子句组装成所需的 `features` 格式回传。同时，`focus_keywords` 应当直接从用户的入参 `query` 中动态截取，而非基于硬编码列表。
- **LLM Factory 空指针修复策略**：由于 `.get("key", {})` 无法防御键存在但值为 `None` 的场景，必须改用 `or {}` 模式。即逐步解析层级结构 `func_obj.get("parameters") or {}`，利用 Python `None or {}` 会返回 `{}` 的特性，确保无论是 `null` 还是缺失键，后续的字典遍历 `.items()` 以及特征读取都不会引发 `NoneType` 报错。

## 3. Caveats
- `BigQueryAdapter` 内由于缺乏 LLM 实时总结能力，直接使用标点符号（`;`, `.`）切分 `claim_text` 作为 `features`，可能会产生文本切片长短不一的情形。但这是在无 LLM 环境下最纯粹且真实的通用数据泛化方法。
- 逻辑中假设工具参数在遇到 `null` 时将其视为无参数空字典 `{}` 处理，这对于标准 JSON Schema 的工具调用规范是合理且兼容的。

## 4. Conclusion
- **文件 1：`server/adapters/bigquery_adapter.py`**
  - **移除硬编码**：删除第 137-148 行的 `if "stream" in claim_lower:` 代码块。
  - **泛化实现**：编写通用逻辑，通过 `re.split(r'[;.]', claim_text)` 切分专利声明，将前 3 个有效子句作为实际的 `features` 返回，`focus` 字段可截取子句的前缀。同时重构 `focus_keywords` 获取逻辑，从 `query` 中正则提取单词。
- **文件 2：`server/llm_factory.py`**
  - **重构字典抽取**：修改第 354 行附近逻辑，以防止 `NoneType` 异常：
    ```python
    func_obj = tool_schema.get("function") or {}
    params_obj = func_obj.get("parameters") or {}
    props = params_obj.get("properties") or {}
    
    mock_args = {}
    for k, v in props.items():
    ```

## 5. Verification Method
1. 对 `server/llm_factory.py` 进行修改后，在 Python 中模拟注入包含 `{"parameters": null}` 的工具 Schema，调用 `_call_local_fallback_template`，验证是否能安全渡过字典 `items()` 遍历并且不抛出异常。
2. 对 `server/adapters/bigquery_adapter.py` 修改后，使用脱离预设领域的查询词（如 `"quantum mechanics"`）调用 `BigQueryAdapter.retrieve()`，观察日志和返回的 `features` 列表，验证其是否包含了真实来自 BigQuery 查询的数据子句，且不再含有 "法官协调代理" 等无关字符串。
3. 运行后端的单元测试或执行 Python 编译检查，确保没有语法错误。
