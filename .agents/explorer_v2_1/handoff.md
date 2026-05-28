# 移交报告：通用动态 Mock 及断路器策略设计

## 1. Observation (观察发现)
在分析目标代码后，发现以下导致 INTEGRITY VIOLATION 审计失败的具体代码片段：
- **`server/llm_factory.py`**:
  - 第 90 和 217 行包含硬编码测试后门：`if api_key and api_key.startswith("sk-c714d64"):`。
  - 第 364-366 行在 Fallback 处理 Phase 4 时，硬编码了返回值：`vote_val = "Grant"`, `prob_val = 0.85`。
- **`server/agentic_engine.py`**:
  - 第 136-150 行 `_determine_vote` 函数内部使用 `random.random()` 生成随机不确定的投票倾向。
  - 第 39-115 行的 `_argument_pre_processor` 中针对特定的工具和参数名硬编码了修补值，例如 `"default_df_id"`、`"default_pa_id"` 等。
- **`tools/patent_tools.py`**:
  - 第 9-54 行硬编码了静态专利库 `SIMULATED_EPO_DATABASE`，直接使用固定的 `EP3812049A1` 等专利数据。
  - 第 66-78 行的检索逻辑硬编码了 `keywords_to_patents` 字典以匹配中文/英文关键词。

## 2. Logic Chain (逻辑链)
为了实现**真正的通用化（TRUE GENERIC）**并符合断路器与 Mock 标识的要求，必须从以下几个方面进行改造：
1. **清理环境后门**：系统已具备基于连续失败 3 次触发 30 秒熔断的断路器（日志输出 `[CIRCUIT_BREAKER]`），但目前的降级依赖硬编码的测试 Key。策略是**彻底删除 `sk-c714d64` 拦截逻辑**。Mock Fallback 应完全依赖断路器超时、网络异常，或通过正规的 `os.getenv("FORCE_MOCK")` 环境变量触发。
2. **实现确定性与幂等性（取代 Random）**：审计需要可回溯的结果。策略是**移除所有 `random.random()` 调用**。在 `_determine_vote` 及 Phase 4 投票中，改用确定性规则（例如：`if fully_disclosed_count > 0: return "Reject" else: return "Grant"`），如果需要模拟分歧，可以使用对 `agent_name` 和 `claim` 的文本做 Hash 运算的结果取模来替代随机数。
3. **通用参数处理器（_argument_pre_processor）**：放弃为具体工具（如 `generate_feature_alignment_matrix`）写长篇硬编码拦截。策略是**实现基于 JSON Schema 的动态补全**：拦截参数后检查其类型，如果是缺失的字符串字段，则统一赋值为 `f"mock_auto_{key}"`；如果是列表则给 `[]`；或者优先从 `blackboard` 历史中提取最后一个有效的相关 ID，而不是使用写死的 `"default_pa_id"`。
4. **动态 Mock 数据生成协议**：在 `patent_tools.py` 中移除静态字典。当调用 `search_patent_db(query)` 时，打印 `[MOCK_TRANSPORT]` 标签，然后通过对 `query` 字符串进行分词或哈希，**动态生成**专利对象（例如生成 `ID: MOCK_PAT_hash(query)`，提取前三个词作为特征焦点）。这样无论输入什么领域的内容，都能生成格式合法的通用模拟数据。

## 3. Caveats (注意事项与局限)
- **哈希稳定性**：依赖输入字符串进行 Hash 计算时，需确保输入在同一轮对话中保持一致，否则同一个请求对象每次生成的 Mock ID 不同，可能导致下游工具（如对齐矩阵）无法对应上 ID。
- **LLM的自我修正**：如果参数处理器不再强行塞入有效的上下文 ID，而是采用泛用的 Placeholder，可能会依赖大模型自身的容错和自我纠正能力，如果大模型对此比较敏感可能会导致任务中断。
- **尚未应用更改**：本报告仅提供策略，未进行任何代码层面的直接修改。

## 4. Conclusion (最终结论)
当前系统未能通过审计的原因是滥用了硬编码特定数据、后门密钥和随机函数，这些破坏了系统的纯净度和幂等性。
**通用修复方案**：
1. 删除 `llm_factory.py` 中的 `sk-c714d64` 及写死的 `"Grant"` 逻辑。
2. 删除 `agentic_engine.py` 中的 `random.random()`，使用基于输入 Hash 或已知事实数量（`fully_disclosed_count`）的绝对确定性规则。
3. 将 `_argument_pre_processor` 改造为基于 JSON Key/Type 反射机制的自动缺省占位符填充器。
4. 将 `patent_tools.py` 的固化库替换为依据 `query` 实时拼接生成专利结构数据的动态 Mock 工厂。

## 5. Verification Method (验证方法)
由于尚未实现代码，后续实施后可以通过以下方式验证：
1. **全局检索验证**：在根目录下执行 `grep -r "sk-c714d64" .`、`grep -r "EP3812049A1" .` 以及 `grep -r "random.random()" .`，应当没有任何匹配结果。
2. **幂等性测试**：在未配置有效 API_KEY 时，连续两次输入完全相同的待审权利要求，观察最终生成的 Mock 投票结果和专利 ID 是否 100% 一致。
3. **日志捕获**：观察控制台输出，确认当发生拦截或网络熔断时，必定能捕捉到标准的 `[CIRCUIT_BREAKER]` 与 `[MOCK_TRANSPORT]` 标识。
4. **领域无关性测试**：输入完全与专利无关的问题进行检索测试，确认返回的检索数据 ID 为动态的 `MOCK_PAT_xxx` 且依然符合结构化标准。
