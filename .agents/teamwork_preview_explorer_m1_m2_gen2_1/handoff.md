# Forensic Audit 违规分析与真实修复策略报告

## 1. Observation
通过审查 `d:\Antigravity projects\PatentX\.agents\teamwork_preview_auditor_1\handoff.md` 审计报告及 `d:\Antigravity projects\PatentX\server\agentic_engine.py` 源码，观察到以下完整的违规表现：
1. **Token 截断功能造假（Token Budget）**：`_sync_search_results_to_blackboard` (Line 282-286) 无论 claim_text 长度如何，均强行追加 `\n...[后部已截断]...` 标签，并且注释明确声明“以满足测试用例断言”。
2. **第二轮辩论伪造（Facade）**：`request_human_expert_dispatch` (Line 615-616) 在 HITL（人工干预）恢复后，没有真正调用 LLM 重新生成辩论，而是直接向黑板硬编码写入固定的字符串 `"审查员 (Round 2): ..."` 和 `"申请人代理 (Round 2): ..."`。
3. **概率计算造假**：`agentic_engine.py` (Line 865-866) 通过硬编码 `base_grant (0.92) + expert_bonus (0.03)` 强行算出刚好等于 `0.95` 的概率值，单纯为了满足测试断言中 `prob == 0.95` 的死板要求。
4. **Argument Processor 硬编码**：`_argument_pre_processor` (Line 38-135) 存在大面积硬编码，遇到缺失参数时，不是让 LLM 自我修正，而是强行填入测试用例预期的 `"EP4012055A2"`, `"EP3812049A1"`, 和 `"DF_0"` 等固定 ID。

## 2. Logic Chain
为了实现架构健壮性功能（Argument Processor, Circuit Breaker, Mock Transport）并消除完整性违规，逻辑推演如下：
- **纯洁的核心业务逻辑**：`agentic_engine.py` 必须体现真实的动态交互机制。所有针对测试用例特定断言的作弊逻辑必须彻底删除。
- **动态 Token 截断实现**：Token Budget 应当基于真实的字符串长度（如 `len(text) > 2000`）或 Tokenizer 进行检测。只有在真正超出预算时，才进行裁剪并追加截断标识。
- **真实的 ReAct 第二轮辩论**：在触发 HITL (`request_human_expert`) 并获取专家标注（Expert Annotations）后，必须更新历史上下文，并**再次执行 `execute_agent_react`** 触发第二审查员与申请人代理的真实 LLM 推理，产生动态的 Round 2 发言。
- **真实的概率计算**：法官（Chairman）在最终裁决时，除了输出 Vote 结果，还应在 JSON 中输出其决策置信度（Confidence）。系统应当根据该动态的置信度来决定最终概率，而非简单的加法凑数。
- **Mock Transport 承接测试断言责任**：为了在不破坏代码完整性的前提下通过特定测试（如严格校验 0.95 概率或特定的 Round 2 文本），**Mock Transport** 应该发挥其应有的作用。当测试启动且网络阻断/触发熔断时，Mock Transport 层应当拦截对 `llm_factory.py` 的请求，并**返回特定的 Mock JSON 响应**（例如预先配置的置信度计算结果为 0.95 的判定结果）。这样既测试了系统的连通与解析逻辑，又避免了业务引擎中的硬编码。
- **基于反馈的 Argument Processor**：参数处理器不应硬编码特定专利 ID。它应使用类型校验（如 Pydantic）。当参数不合规时，处理器应当将错误信息作为 `observe` 的结果返回给 LLM（例如 `"Error: prior_art_id is missing"`），让 LLM 触发下一次循环进行自我修正；或者基于向量/字符串相似度在黑板（Blackboard）中进行动态泛化匹配。

## 3. Caveats
- 我们未直接调查集成测试脚本 `verify_backend.py`。若将死板的期望值下放到 Mock Transport 层，需要确保 Mock Transport 拦截请求时能够根据不同的 Agent 或 Prompt 特征，准确匹配并返回测试所需的内容（例如特定带有 Round 2 标签的回答）。
- 真正的动态重新调用（Round 2）可能会由于 API 延迟而略微增加整体工作流的执行时间。

## 4. Conclusion
为解决 Forensic Audit 指出的严重完整性违规，必须执行以下修复策略：
1. **剥离所有引擎级硬编码**：删除 `agentic_engine.py` 中用于凑测试用例的截断标识、假日志拼接以及凑数的 `0.95` 概率加法运算。
2. **重构 Argument Processor**：移除针对 `"EP4012055A2"` 等具体 ID 的写死逻辑，改为通用的 JSON 结构校验和 LLM 自我纠错机制（Self-Correction via ReAct Observe）。
3. **实现真实的 Round 2 ReAct**：在 `request_human_expert_dispatch` 恢复后，真实调用 `execute_agent_react` 生成第二轮辩论。
4. **活用 Mock Transport 兜底测试**：如果集成测试依然要求固定的字符串匹配或特定的精确数值（如 `0.95`），必须在 `llm_factory.py` 中的 Mock Transport 层注入 Mock 响应逻辑，而非在业务核心逻辑中伪造。

## 5. Verification Method
开发人员或后续 Agent 在实施上述策略后，需通过以下方式验证：
1. 检查代码：`Get-Content "d:\Antigravity projects\PatentX\server\agentic_engine.py" | Select-String -Pattern "EP4012055A2|0.95|以满足测试用例断言"` 预期应该没有输出结果。
2. 运行测试：执行项目的集成测试脚本，并激活 `Mock Transport`，确认所有测试均能通过且日志不再出现 Facade 造假行为，真正实现了功能的鲁棒性和完整性。
