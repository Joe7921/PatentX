# 专利审查项目架构法医级审计修复策略报告

**工作产物**: `d:\Antigravity projects\PatentX\.agents\teamwork_preview_explorer_gen3_2\handoff.md`

## 1. 观察记录 (Observation)

通过直接查阅源代码，确认了 Iteration 2 审计报告中指出的全部问题，并追踪了其根源与依赖关系：

1. **`server/agentic_engine.py` 中的硬编码屏蔽了动态输入**：
   - 第 458-463 行，`run_workflow_logic` 内部直接忽略传入的 `claim`，硬编码了 `domestic_features`（如“特征A: 支持多Agent嵌套协作的专利评估...”）。
   - 第 491-499 行，Prompt 中存在强制要求 LLM 输出特定 ID（如 `DF_0` 等）的 `CRITICAL RULE`。
   - 第 51-114 行，`_argument_pre_processor` 会主动拦截 `generate_feature_alignment_matrix`，当参数缺失时，使用预设的 `DF_0`、`Mocked prior art feature text` 等覆盖参数。
   - 第 120-141 行，`_VOTE_TEMPLATES` 包含高度特异性的文本，如“核心技术特征A（SSE流式传输）与EP3812049A1...”。
2. **`server/llm_factory.py` 的测试专供“状态机”**：
   - 第 292-646 行，`MockLLMClient._call_local_fallback_template` 中写死了特定的 `if-else` 分支。如果当前角色是 `first_examiner` 且 `current_round == 1`，则强制输出针对 `multi-agent nested collaboration...` 的检索动作；如果 `current_round == 3`，则输出硬编码的三组对齐矩阵生成动作（包含 `EP4012055A2_F1` 等）。
3. **`server/verify_backend.py` 具有极度刻板的断言设计**：
   - 第 51-56 行，`verify_backend.py` 在执行恢复（resume）操作时，强行提交了硬编码的 `expert_details` 字典键值（如 `"DF_0_EP4012055A2_EP4012055A2_F1"`）。
   - 第 83 行，强断言 `prob == 0.95`，导致只要系统的动态逻辑稍有偏差或算出的概率略有不同就会挂掉。

## 2. 逻辑链条 (Logic Chain)

1. **为什么出现了 Facade (门面实现)？** 
   因为 `verify_backend.py` 中写死了复杂的 JSON 键值对进行断言和 POST 请求。为了让测试强行通过，前序开发者反向在 `agentic_engine.py` 和 `llm_factory.py` 中写死了各种规则，以确保最终输出的矩阵键值与测试脚本的预期分毫不差。
2. **解耦的第一步是使 `agentic_engine.py` 动态化**：
   必须移除硬编码的 `domestic_features`，改为根据传入的 `claim` 字符串动态分割生成（例如通过逗号/分号切分或正则表达式）。移除 Prompt 中所有的强制映射规则，使系统具备处理任意专利文本的底座能力。
3. **解耦的第二步是实现真正的通用 Mock Fallback**：
   `llm_factory.py` 中的 Fallback 逻辑不应知道当前测试的具体领域。它应当根据传入的 `messages` 历史记录及可用的 `tools` 列表进行通用响应：
   - 依赖 `current_round` 推进状态防止死循环。
   - 如果可用工具中包含 `search_patent_db`，则直接从 `messages` 中的 `claim` 文本提取前几个字作为关键词。
   - 如果需要构建对齐矩阵，则动态读取 `blackboard` 里的真实 `claim_features` 与 `retrieved_patents` 进行组合调用。
4. **解耦的第三步是使 `verify_backend.py` 具有自适应能力**：
   作为测试脚本，`verify_backend.py` 不能预设矩阵的 Key。它应当在捕获到 `hitl_interrupt` 事件时，动态调用一个 API（如 `/api/v1/evaluation/{id}/blackboard`）获取黑板上所有的对齐矩阵条目，遍历并提取真实的 ID 组合构建 `expert_details`，然后再发 POST 请求继续。同时，将最终的固定断言 `prob == 0.95` 放宽为范围断言（如 `prob >= 0.8`）。

## 3. 局限性与前提假设 (Caveats)

- `tools/patent_tools.py` 中的 `SIMULATED_EPO_DATABASE` 仍保留为 Mock 数据库。这符合测试环境中对于 Mock API Adapter 的允许范围（非生产环境无需连接真实 EPO 库），并不是完整性违规的范畴。我们的策略只需处理核心引擎流程的通用性。
- Mock Fallback 中的通用逻辑可能会因为只是基于规则生成特征拆分，导致与真实的 LLM 生成在逻辑严谨性上有所不同，但它能够真实走通 ReAct 循环。

## 4. 最终结论 (Conclusion)

当前的系统是为了迎合 `verify_backend.py` 苛刻且具体的断言要求而定制的测试专用脚本群，存在严重的完整性违规。
**核心修复策略**：
1. **重构 `agentic_engine.py`**：动态解析 `claim`，移除 `_argument_pre_processor` 和 `_VOTE_TEMPLATES` 中任何对“SSE”、“特征A”、“EP38”相关的硬编码词汇，改为依赖真实的 `blackboard` 状态对象进行安全补全和通用模板填充。
2. **重构 `llm_factory.py`**：将 `MockLLMClient` 改写为“状态感知但无领域偏见的”通用生成器。依靠获取到的 `blackboard` 和 `tools` 参数动态拼接工具调用（Tool Calls）。
3. **改造 `verify_backend.py` 测试脚本**：移除对硬编码特定字符串键值的依赖，通过在中断期间实时请求 Blackboard 状态接口获取最新的矩阵信息，动态组装出 `expert_details` 参数，并将过分严格的概率断言改为区间判断。

## 5. 验证方法 (Verification Method)

- 修改完成后，在 `main.py` 的 `/api/v1/analyze/stream` 接口中随意修改 `claim` 默认值为一个毫不相干的领域文本（如“一种基于量子纠缠的自动驾驶车载雷达系统”）。
- 执行测试 `python verify_backend.py`。
- 如果系统为真正的动态系统，则应该能够提取出量子领域的特征，检索出兜底的专利（或任意匹配结果），动态生成与量子特征相关的对齐矩阵，并在测试脚本的动态捕获下完成专家批注，最终无错通过。
- 执行全局搜索，确保 `server/` 目录下不再存在 "EP3812049A1", "EP4012055A2", "特征A", "SSE" 等硬编码字符串。
