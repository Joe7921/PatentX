# 架构健壮性优化分析与实施策略

## 1. Observation
- 根据计划 `implementation_plan.md`，目标是为 PatentX 后端引入架构健壮性特性：Circuit Breaker（熔断机制）、Mock 显式标注（Mock Transport）以及工具参数预处理器（Argument Processor）。
- 在干净的工作区状态下（`git diff` 为空）：
  - `server/llm_factory.py` 的 `LLMFactory` 缺少全局故障计数器 `_failure_counts` 和熔断期 `_circuit_breaker_until`。在 API 失败时，它直接向上抛出异常，并未执行带有明确 `[MOCK_TRANSPORT]` 标签的本地降级模板。
  - `server/agentic_engine.py` 内部缺乏统一的 `_argument_pre_processor` 函数，工具调用是直接传参，未进行参数自动补全和纠错。
  - `tools/patent_tools.py` 的 `search_academic_db` 函数目前返回 `[MOCK NPL]` 标签（位于第 104 行），不符合统一标签规范。
- 额外观察：在主库 `d:\Antigravity projects\PatentX` 中存在大量未提交的修改（Uncommitted Changes），这些修改**实际上已经包含了上述特性的完整实现**（包括 `execute_agent_react` 的重构以及相关标签的打印）。

## 2. Logic Chain
- **Circuit Breaker**: 为了避免无效的网络等待并明确系统状态，必须在 `LLMFactory` 维护模型级别的失败次数。当 `_call_model` 捕获异常时，增加计数；若连续失败达 3 次，则设置熔断时间戳，并打印 `[CIRCUIT_BREAKER]` 标签。后续请求若处于熔断期内，直接抛出异常或进入本地 Fallback。
- **Mock Transport**: 当大模型 API 故障且无备用模型时，需要提供降级兜底逻辑（如 `_call_local_fallback_template`），并在生成的兜底响应及日志中显式加入 `[MOCK_TRANSPORT]`，确保测试时前端和后台均能明确当前为 Mock 状态。同时，`tools/patent_tools.py` 中的 `[MOCK NPL]` 需统一替换为 `[MOCK_TRANSPORT]`。
- **Argument Processor**: 为了防止大模型输出的 JSON 参数不完整（特别是针对 `generate_feature_alignment_matrix` 工具缺失 `domestic_feature_id` 等字段的情况），需要实现 `_argument_pre_processor(tool_name, raw_args, blackboard)`。在真正调用工具前，将 `raw_args` 传入该处理器进行清洗与补全；若发生修正，则在日志中显式打印 `[ARGUMENT_PROCESSOR]` 标签。

## 3. Caveats
- **重大代码冲突预警**：主仓库 `d:\Antigravity projects\PatentX` 目前存在未提交的大型重构（涉及 ReAct 循环引擎 `execute_agent_react` 的引入及已完成的熔断逻辑）。Worker 在执行具体实现时，需要与 Orchestrator 或 User 确认是基于这些未提交的修改继续（直接 commit 或复用），还是要在纯净的工作区从零重写。
- 如果工作区仍使用旧版 `run_agentic_workflow`（硬编码工具调用），提取 `_argument_pre_processor` 的集成位置将与新版 `execute_agent_react` 有所不同。

## 4. Conclusion
为满足要求，Worker 的实施策略如下：
1. **修改 `server/llm_factory.py`**：
   - 为 `LLMFactory` 类添加 `_failure_counts` 和 `_circuit_breaker_until` 字典。
   - 在 `_call_model` 请求 API 前检查 `_circuit_breaker_until`，生效中则记录 `[CIRCUIT_BREAKER]` 并抛异常。
   - 捕获 API 异常后，累加计数，若 >= 3 则触发熔断并记录 `[CIRCUIT_BREAKER]`。
   - 实现或补全 `_call_local_fallback_template` 降级函数，包含 `[MOCK_TRANSPORT]` 提示信息。
2. **修改 `server/agentic_engine.py`**：
   - 编写 `_argument_pre_processor(tool_name, raw_args, blackboard)` 独立函数，专门处理 `generate_feature_alignment_matrix` 的参数缺失问题（如动态匹配 `domestic_feature` 和 `prior_art_feature`）。
   - 补全参数后，若发现参数被修改，则 `print("[ARGUMENT_PROCESSOR] 拦截到不规范参数，已动态修正...")`。
   - 在引擎执行工具前，插入对此函数的调用。
3. **修改 `tools/patent_tools.py`**：
   - 将第 104 行的 `f"[MOCK NPL] 找到与..."` 修改为 `f"[MOCK_TRANSPORT] 找到与..."`。

## 5. Verification Method
1. 执行 `npm run dev` 和 `uvicorn main:app`。
2. 在环境变量或 `.env` 中设置 `INJECT_LLM_FAILURE=true`（或填入无效 API Key）。
3. 运行端到端测试或提交一次专利审查请求，观察后端控制台和前端 SSE 日志输出。
4. 验证条件：
   - 是否连续抛出异常后打印 `[CIRCUIT_BREAKER] 模型 ... 连续失败超过3次，触发熔断`。
   - 是否在降级生成中看到 `[MOCK_TRANSPORT]` 标签。
   - （如遇到参数残缺）是否在日志看到 `[ARGUMENT_PROCESSOR]` 的自动修正提示。
   - `tools/patent_tools.py` 的模拟 NPL 检索结果是否成功带有 `[MOCK_TRANSPORT]` 前缀。
