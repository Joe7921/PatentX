# Handoff Report

## 1. Observation
- 在 `server/llm_factory.py` 的 `_call_local_fallback_template`（Mock Transport 降级模板）中，代码直接使用 if-elif 判断并硬编码了工具调用的严格顺序（例如按顺序压入 `search_patent_db`、`generate_feature_alignment_matrix`、`ask_epo_examiner`、`request_human_expert`），并且使用遍历属性拼接 `f"mock_{k}_string"` 等虚拟假数据的方式写入工具参数。
- 在 `server/llm_factory.py` 的 `_call_local_fallback_template` 第 415 行，针对第四阶段的裁决逻辑，硬编码直接返回通过结论：`vote_val = "Grant"`, `reasoning_val = "基于通用的Mock评估，当前特征满足条件。"`, `prob_val = 0.85`。
- 在 `tools/patent_tools.py` 的 `generate_feature_alignment_matrix` 工具（宣称为模拟 Layer-2 专家的特征比对评估）中，判断特征是否 `Fully_Disclosed` 的核心逻辑仅仅是一个简单的字符串切分匹配：`any(word and word in df_lower for word in focus_kw.split(" "))`。

## 2. Logic Chain
- “Mock Transport” 作为容灾特性的预期行为应当是提供基础且动态的占位/安全兜底，但当前的实现不仅伪造了参数，而且针对整体流程编写了一套自动应答器（Auto-responder script），自动按测试期望的剧本遍历并执行多智能体的每一步动作。这完全绕过了多智能体 ReAct 循环的核心自主决策目标（Shortcuts that bypass the intended task）。
- 在 Phase 4 硬编码 `vote="Grant"` 及 0.85 置信度，是极端恶劣的 Fabricated verification outputs（伪造验证输出）。它使得无论前期辩论或对齐矩阵的内容为何，在发生降级时系统都一定会直接授予专利并蒙混过关。
- `generate_feature_alignment_matrix` 作为关键的技术比对工具，用一行字符串截取伪装成 L2 代理的语义对比，属于典型的 Facade implementations that look correct but implement no real logic。
- 以上特征皆触犯了系统所定义的 Integrity Violations（完整性违规），属于通过作弊代码（Cheats）自证其对。

## 3. Caveats
- 观察到集成测试套件 `verify_backend.py` 能够在开启故障注入（`INJECT_LLM_FAILURE="true"`）的环境下全部 Pass，正是因为 `Mock Transport` 按照测试的 Assert 期望“定制化”输出了对应的参数和结论。没有进行进一步的业务数据隔离测试，但这并不影响对 Facade 作弊行为的定性。

## 4. Conclusion
- **VERDICT**: **REQUEST_CHANGES** (Critical - INTEGRITY VIOLATION)
- 系统所宣称的 Gen3 架构鲁棒性特性（特别是 Mock Transport 和部分 Agent-as-Tool 评估），本质上是绕过真实计算过程的硬编码剧本和 Facade 逻辑。其通过测试的分数完全建立在伪造的流程数据与固化的判定之上。必须彻底移除针对流程顺序的 Hardcode 轮询逻辑与硬编码投票判定，重构为真实动态、或至少非作弊性质的安全 Mock。

## 5. Verification Method
- **查看源码**：查阅 `server/llm_factory.py` 约第 310-420 行间的 `_call_local_fallback_template` 代码块，即可验证作弊分支。查阅 `tools/patent_tools.py` 约第 150 行。
- **重现现象**：在根目录下运行 `python server/run_test.py` 后，读取生成的 `server/test_output.txt`。尾部日志清晰显示，当激活 `INJECT_LLM_FAILURE` 时，多个不同角色的 Agent 给出了完全一致且机械的 Mock JSON 和最终 `Grant` 结论，证明其验证成功源于内置 Facade 剧本。
