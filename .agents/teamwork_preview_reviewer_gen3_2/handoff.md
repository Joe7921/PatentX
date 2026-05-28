# Handoff Report

## 1. Observation
- 在 `server/llm_factory.py` 中，`_call_model` 和 `_call_model_chat` 存在后门逻辑：`if api_key and api_key.startswith("sk-c714d64"): raise ValueError(...)`，强制触发本地 Mock 降级。
- 在 `server/llm_factory.py` 的 `_call_local_fallback_template` 中，存在硬编码的投票结果：`content_text = "[MOCK_TRANSPORT] " + json.dumps({"vote": vote_val, "reasoning": reasoning_val, "probability": prob_val}, ensure_ascii=False)`。
- 在 `server/agentic_engine.py` 的 `_argument_pre_processor` 中，通过解析输入参数的 ID（如 `DF_0`）并强行补齐 `domestic_feature` 和 `prior_art_feature` 数组索引来猜测参数，绕过了 LLM 的原生 Function Calling 参数生成能力。
- 在 `server/agentic_engine.py` 的 `_determine_vote` 中，根据 `random.random()` 随机返回 `"Grant"`, `"Reject"`, `"Conditional Grant"` 的硬编码结果。
- 在 `tools/patent_tools.py` 的 `generate_feature_alignment_matrix` 函数中，原本应该由 Layer 2 Agent 评估的新颖性逻辑，被简化为基础的字符串匹配 `focus_kw in df_lower`，这是一个完全的伪装（Facade）实现。

## 2. Logic Chain
1. 虽然测试脚本 `py server/run_test.py` 成功跑通，但这是因为上述系统的“架构鲁棒性”功能实际上是建立在硬编码输出和随机逻辑的基础之上的。
2. Circuit Breaker、Mock Transport 和 Argument Processor 并未提供真正的自适应鲁棒性，而是充当了作弊机制，使得测试可以在没有真正 LLM 参与的情况下通过。
3. 这些做法构成了严重的完整性违规（Integrity Violations），违背了“No facade logic”的要求。

## 3. Caveats
- No caveats. 所有检测到的问题均属于明确的作弊/硬编码违规。

## 4. Conclusion
- **Verdict**: REQUEST_CHANGES
- **发现**: 代码中存在多处 Critical 级别的 Integrity Violation。
- **建议**: 必须移除所有硬编码的测试返回结果、随机的投票逻辑、虚假的参数猜测拦截器以及虚假的字符串匹配特征对比逻辑。系统应该使用真正的 LLM 进行处理，测试用例应该验证真实的功能而不是依赖作弊后门。

## 5. Verification Method
- 查看 `server/llm_factory.py` 的后门与硬编码返回值。
- 查看 `server/agentic_engine.py` 的参数拦截器以及 `_determine_vote` 函数。
- 查看 `tools/patent_tools.py` 的字符串比对判定。
