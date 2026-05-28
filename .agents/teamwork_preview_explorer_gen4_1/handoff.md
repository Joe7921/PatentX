# Handoff Report

## 1. Observation
- 在 `server/llm_factory.py` 的 `_call_local_fallback_template` 中观察到，代码通过 if-elif 语句硬编码了工具调用的严格顺序（例如 `search_patent_db`、`generate_feature_alignment_matrix`、`ask_epo_examiner` 等），并在 Phase 4 的判定中直接硬编码返回 `{"vote": "Grant", "reasoning": "...", "probability": 0.85}`。
- 在 `tools/patent_tools.py` 的 `generate_feature_alignment_matrix` 工具中，观察到特征对齐的核心评估逻辑仅使用了基础的字符串包含判断：`focus_kw in df_lower or any(word and word in df_lower for word in focus_kw.split(" "))`。
- 在 `server/agentic_engine.py` 的 `_argument_pre_processor` 中，针对 `generate_feature_alignment_matrix` 工具，观察到代码使用正则 `re.search(r'\d+', df_id)` 从参数中强行提取索引，并直接从 `blackboard` 的数组中按索引提取数据覆盖原始参数，取代了真正的 LLM 参数生成。

## 2. Logic Chain
- 审阅门禁（Reviewer Gate）驳回的原因是系统使用了作弊性质的硬编码剧本和门面（Facade）逻辑，绕过了真实的 Agent 动态决策与评估。要修复此问题，必须彻底移除所有为了通过测试而固化的“捷径”。
- **针对 Mock Transport (`llm_factory.py`) 的修复策略**：彻底移除针对具体工具名称的 if-elif 硬编码。实现一个真正的泛化生成降级方案：动态解析传入的 `tools` JSON Schema，随机挑选一个可用工具，并根据其 `properties` 的类型（string, integer, array 等）动态生成对应类型的随机合法 Mock 数据。对于 Phase 4 的投票，不应固定返回 "Grant"，而是随机从 `["Grant", "Reject", "Conditional Grant"]` 中抽取，并赋予随机的 probability。
- **针对特征对齐 (`patent_tools.py`) 的修复策略**：将单纯的字符串包含替换为轻量级的本地 NLP 规则引擎。引入 Jaccard 相似度算法，对 `domestic_feature` 和 `prior_art_feature` 进行分词并剔除常见停用词，计算词汇重合度（Token Overlap Ratio）。如果相似度大于设定阈值（如0.3）则判定为 `Fully_Disclosed`。这种基于算法的评估能够提供真实的计算过程，而非简单的字符串门面匹配。
- **针对参数预处理器 (`agentic_engine.py`) 的修复策略**：移除通过数组索引猜参数并强制覆盖的逻辑。预处理器应当尊重 LLM 或 Mock 引擎真实生成的参数，仅做基础的类型安全检查和 JSON 解析。若缺少字段，可回退为简单的类型默认值，而不是利用作弊手段从全局状态中按顺序偷取数据补全。

## 3. Caveats
- 引入的轻量级 NLP 规则（如 Jaccard 相似度）虽然比字符串包含更真实，但依然是基于词法规则的本地评估，无法完全媲美真实 LLM 的语义理解能力。但这符合在脱机环境或 Mock 降级时“提供真实计算而非脚本化门面”的整改要求。
- 移除参数预处理器的强行补全机制后，如果 LLM 生成的参数不规范，系统可能会产生更多的工具调用错误，但这恰恰是系统鲁棒性测试所需面对的真实场景。

## 4. Conclusion
- **VERDICT**: **APPROVE WITH FIX STRATEGY**
- 系统的 Facade 逻辑已被准确定位。必须执行以下重构：
  1. 重写 `llm_factory.py` 的 Mock 生成器，基于传入 Schema 实现随机且合法的工具调用生成，移除顺序硬编码。
  2. 在 `patent_tools.py` 中实现基于分词与 Jaccard 相似度的轻量级 NLP 对齐算法。
  3. 清理 `agentic_engine.py` 中基于索引作弊的参数强行注入代码。
  执行上述策略即可完全移除 scripted test sequence，满足 Reviewer 的严格要求。

## 5. Verification Method
- **源码审查**：修改完成后，检查上述三个文件，确保找不到 `search_patent_db` 等工具名称的硬编码轮询逻辑，找不到 `0.85` 与 `Grant` 的强制返回，以及找不到 `re.search(r'\d+', df_id)`。
- **行为验证**：在开启 `INJECT_LLM_FAILURE="true"` 的环境下运行 `python server/run_test.py`。通过观察 `server/test_output.txt` 日志，应发现 Mock 模式下选用的工具不再是固定的剧本顺序，参数值呈现随机生成的特征；投票结论在多次运行中应随机出现 Grant/Reject，概率值也应为随机浮点数。
