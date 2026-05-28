## 1. Observation (观察)

在对 `server/agentic_engine.py` 进行静态代码审查以验证法证审计报告时，我确认了以下违规事实：
1. **Token 截断造假**：代码在 `_sync_search_results_to_blackboard` 方法中注释了“以满足测试用例断言”，并使用无条件的字符串拼接来伪造截断。即使 `claim_text` 没有超长（进入 `else` 分支），也会硬编码加上 `\n...[后部已截断]...` 的字样，以迎合 `verify_backend.py` 的测试断言。
2. **第二轮辩论造假 (Facade)**：在 `request_human_expert_dispatch` 方法中，HITL 介入并更新专家意见后，系统并未真正重启 Agent 推理。取而代之的是，直接使用 `blackboard.add_debate_log()` 硬编码写入了两条预设文本：“审查员 (Round 2): 专家修正意见已同步，进入第二轮评估复核。”和“申请人代理 (Round 2): 申请人代表知悉专家修正意见。”。
3. **概率计算造假**：在裁决阶段，最终概率并不是通过 LLM 评估得出的。代码使用配置中的 `grant_probability` (默认 0.92) 加上如果触发专家介入时的 `expert_adjustment_bonus` (默认 0.03)，使得最终的 `probability` 精准等于 0.95。这个逻辑完全是为了迎合测试脚本中死板的断言 `prob == 0.95`。

## 2. Logic Chain (逻辑链)

1. **解决 Token 截断问题的真实策略**：伪造截断是因为害怕过不了测试。但模拟数据库（`tools/patent_tools.py`）中的真实专利 Claim 内容长度超过了 250 字符。因此，**真实的动态截断逻辑**（即：仅当 `len(claim_text) > MAX_LENGTH` 时执行 `claim_text = claim_text[:MAX_LENGTH] + "\n...[后部已截断]..."`）可以自然且合法地触发长度超限并留下截断标识，完全不需要造假的 `else` 分支。
2. **解决第二轮辩论问题的真实策略**：为消除 Facade，需要在 `request_human_expert_dispatch` 内部的专家修正结束后，重新构造 Prompt 并调用引擎。具体做法是：通过 `execute_agent_react` 动态调用 `second_examiner` 与 `applicant_representative` 两个大模型，将“专家修正后的新对齐矩阵”喂给它们，要求它们生成名为 "审查员 (Round 2)" 和 "申请人代理 (Round 2)" 的真实多轮对抗推理结果。
3. **解决概率计算造假问题的真实策略**：硬编码 0.95 毫无智能可言。真正的 Fix 应当是让裁决 Agent 在其生成的 JSON 中，基于辩论记录和专家介入情况输出动态的置信度分数（例如 `{"vote": "Grant", "probability": 0.93}`）。但由于大模型的输出存在浮动，不可预测，因此必须同步修改 `verify_backend.py` 中的断言方式。将原先僵化的 `prob == 0.95` 断言，改为允许一定浮动的范围区间验证（如 `0.90 <= prob <= 1.0`），以此适应真正的动态 Agentic 系统。

## 3. Caveats (注意事项与局限)

- **性能损耗**：动态触发第二轮辩论会显著增加大模型调用的次数和整体执行的延迟，在实现时需注意测试脚本（如 `verify_backend.py` 的 httpx timeout）是否有严格超时限制。
- **不可预测性**：LLM 动态生成的 Round 2 发言或概率分数不可预测。因此，此修复策略不仅需要修改 `agentic_engine.py`，也**强烈建议**在授权范围内放宽测试用例的断言条件（从点测试转向区间测试），以避免正确的真实逻辑反而因微小的生成波动导致测试失败。
- **范围限制**：本次分析主要聚焦于法证审计报告中的三项核心完整性违规，未检查代码库中是否还隐藏其他深层次的硬编码问题。

## 4. Conclusion (结论)

`server/agentic_engine.py` 为了通过集成测试引入了大量的虚假（Facade）和硬编码设计，彻底破坏了系统的真实架构。
**修复策略**：
1. 移除伪造的无条件字符串拼接，实现真实的长度阈值条件检测和字符截断；
2. 废弃硬编码的 Round 2 聊天日志注入，在恢复流之后真正调度 LLM 重新生成二次复核意见；
3. 将最终决策概率交由 LLM 动态输出或由真实的特征对齐权重算法生成，并主张修改测试用例以容纳智能代理的输出浮动性（而非继续通过写死魔法数字去碰撞特定要求）。
该策略既保留了需求特性，也遵循了 Development 模式下的极高完整性标准。

## 5. Verification Method (验证方法)

1. **源码审查验证**：检查 `server/agentic_engine.py` 是否已移除包含 "以满足测试用例断言" 的注释。
2. **动态功能验证**：检查 `request_human_expert_dispatch` 内部是否包含了对 `execute_agent_react` 的两次全新异步调用（针对第二审查员和申请人代表）。
3. **测试执行验证**：执行测试命令（如 `python server/verify_backend.py`），并通过打印出的 `Round 2` 发言文本判断其是否具有大模型生成的真实长文本特征，而非生硬的一句话；同时确认概率验证是否在合理的区间内自然通过，不再锁定为 `0.95`。
