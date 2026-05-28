# Handoff Report

## 1. Observation
- 在 `server/llm_factory.py` 的 `_call_local_fallback_template` 方法中，针对 `current_round <= 3` 的情况，代码使用了一系列硬编码的 `if-elif` 逻辑，强制按照 `search_patent_db` -> `generate_feature_alignment_matrix` -> `ask_epo_examiner` 等顺序生成工具调用参数。针对 Phase 4（`current_phase == 4`），代码硬编码返回了固定的投票结果：`{"vote": "Grant", "reasoning": "基于通用的Mock评估，当前特征满足条件。", "probability": 0.85}`。
- 在 `tools/patent_tools.py` 的 `generate_feature_alignment_matrix` 工具中，对于特征是否属于 `Fully_Disclosed`（完全公开）的评估，仅使用简单的字符串拆分和包含判定：`focus_kw in df_lower or any(word and word in df_lower for word in focus_kw.split(" "))`，这是一种虚假的评估门面（Facade）。
- 在 `server/agentic_engine.py` 的 `_argument_pre_processor` 中，针对 `generate_feature_alignment_matrix` 工具，使用了基于正则匹配提取数字索引的方式（`re.search(r'\d+', df_id)`），并从黑板的数组（`blackboard.claim_features` 和 `blackboard.retrieved_patents`）中自动提取相应下标的元素来填充缺失的参数，从而掩盖了大语言模型在工具调用时未正确生成参数的错误。

## 2. Logic Chain
- 当前的 **Mock Transport 降级模板** 彻底绕过了大语言模型应当具备的随机生成与自主决策能力，演变成了一个“剧本式”的自动应答器。特别是 Phase 4 直接返回“Grant”，这种伪造验证结论的行为属于严重的完整性违规（Integrity Violation）。
- **`generate_feature_alignment_matrix`** 的底层逻辑使用单纯的字符包含，虽然包装成 L2 Agent 的形式，但无法真正反映语义上的近似程度，使得功能流于形式。
- **`_argument_pre_processor`** 使用数组下标去猜测并强行填补缺失参数，阻止了系统正确暴露和处理大语言模型输出不规范的问题。在真实的函数调用（Function Calling）流程中，如果缺少必要参数，应当将校验错误反馈给大语言模型促使其自行修正，而非在底层悄悄替换数据。

## 3. Caveats
- 采用通用且随机生成的 Mock 机制以及移除硬编码的参数补偿逻辑后，目前的集成测试 `verify_backend.py` 可能会因为无法获得预设的参数和流程而失败。测试套件需要同步进行重构，以适应动态生成的降级结果。
- 对于 `generate_feature_alignment_matrix`，引入轻量级的自然语言处理规则（例如 Jaccard 相似度）虽然比字符包含更科学，但由于不经过真实大语言模型的语义理解，其在测试环境的判定结果仍然具有局限性，仅适用于兜底降级。

## 4. Conclusion
为彻底修复 Reviewer 指出的 Facade 作弊逻辑，建议按照以下策略重构：
1. **重构 Mock Transport（`llm_factory.py`）**：废除硬编码的工具调用顺序。在触发降级时，动态读取 `tools` 列表，随机挑选一个未调用的工具，并根据该工具的 JSON Schema（包含参数的 type 字段）随机生成合理的 mock 占位数据。在 Phase 4 的投票中，从 `["Grant", "Reject", "Conditional Grant"]` 选项中随机抽取投票结果。
2. **重构特征对齐评估（`patent_tools.py`）**：废除简单的 `in` 字符包含匹配，改用轻量级 NLP 规则。例如，对英文/中文进行分词处理，计算 `domestic_feature` 和 `prior_art_feature` 的词袋集合，然后利用 Jaccard 相似度（交集/并集）与预设阈值（如 > 0.3）来判断是否属于 `Fully_Disclosed`。
3. **重构 Argument Processor（`agentic_engine.py`）**：移除根据 ID 提取下标并自动查数组填充的逻辑。如果识别到缺少关键参数，不应“智能填空”，而是应该构造一个明显的错误占位符，或者向 LLM 抛出明确要求修正的 Tool Error，强制依赖 LLM 遵循 Schema。

## 5. Verification Method
- **查看源码**：重构完成后，查阅 `server/llm_factory.py`，确认 `_call_local_fallback_template` 中不再存在任何具体工具名（如 `search_patent_db`）的 hardcode 字符串；查阅 `tools/patent_tools.py` 确认使用了类似集合交并比的 NLP 函数；查阅 `server/agentic_engine.py` 确认移除了 `re.search(r'\d+', df_id)`。
- **运行并监控**：设置 `INJECT_LLM_FAILURE="true"`，运行 `python server/run_test.py`。检查测试输出中生成的工具参数是否体现出随机性，确保投票结果会在多次运行中表现出变化，并且不再是机械不变的 "Grant"。
