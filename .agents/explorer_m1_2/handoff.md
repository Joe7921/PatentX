# 架构健壮性优化分析与实施策略报告 (Handoff)

## 1. Observation
- 查阅了 `implementation_plan.md`，明确了需要实现 R1（Circuit Breaker 熔断机制）、R2（Mock Transport 显式标注）和 R3（Argument Processor 参数预处理器）的要求，需输出 `[CIRCUIT_BREAKER]`、`[MOCK_TRANSPORT]` 和 `[ARGUMENT_PROCESSOR]` 标签。
- 检索并查看了 `server/llm_factory.py`：
  - `LLMFactory` 类（行 25-27）定义了全局计数器 `_failure_counts` 和 `_circuit_breaker_until`。
  - `_call_model`（行 110-123）与异常捕获（行 174-181）包含了判断熔断时间与失败次数的逻辑，并打印了 `[CIRCUIT_BREAKER]`。
  - `_call_local_fallback_template`（行 298, 402, 416, 418）打印了 `[MOCK_TRANSPORT]`。
- 检索并查看了 `server/agentic_engine.py`：
  - 提取了独立的参数预处理函数 `_argument_pre_processor`（行 39-115），处理了国内特征 ID 等补全逻辑，并在不规范时打印了 `[ARGUMENT_PROCESSOR]`。
  - `execute_agent_react` 在执行工具前（行 375）调用了该函数。
- 检索并查看了 `tools/patent_tools.py`：
  - `search_academic_db` 函数（行 104）返回信息中包含了 `[MOCK_TRANSPORT]`。

## 2. Logic Chain
- **规划逻辑**：任务目标是为 Worker 提供落实 R1、R2、R3 的实现策略（指定函数、代码行位置和逻辑调整）。
- **现状确认**：基于以上观察，所划定的三个范围文件 (`llm_factory.py`, `agentic_engine.py`, `patent_tools.py`) **实质上已经包含**了符合 `implementation_plan.md` 预期的结构与标签。
- **实施策略输出**：为了满足“为 Worker 提供清晰分步实施策略”的任务验收标准，以下策略将直接对齐现有代码的靶向位置，Worker 可据此策略执行代码的二次确认、微调或全量覆写（若当前代码仅为原型）：

### Worker 实施策略 (Step-by-Step Strategy)

**R1. 实现熔断机制 (Circuit Breaker)**
- **目标文件**: `server/llm_factory.py`
- **目标位置**: 
  - `LLMFactory` 类头部（~行 26-27）。
  - `MockLLMClient._call_model` 和 `_call_model_chat` 的请求前置拦截与异常捕获代码块（~行 110-123, 174-181; ~行 232-246, 284-292）。
- **逻辑调整**: 确保在发起 HTTPX 请求前，校验 `now < cb_until`；在请求报错进入 `except Exception` 时，累加 `_failure_counts`，若 `>= 3` 则设置 `_circuit_breaker_until` 并使用 `print` 及 `blackboard.add_debate_log` 显式输出带有 `[CIRCUIT_BREAKER]` 标签的日志。

**R2. 显式标注 Mock 传输层 (Mock Transport)**
- **目标文件**: `server/llm_factory.py` 和 `tools/patent_tools.py`
- **目标位置**: 
  - `llm_factory.py` 的 `_call_local_fallback_template` 函数头部及返回值组装处（~行 298, 402, 416, 418）。
  - `patent_tools.py` 的 `search_academic_db` 函数（~行 104）。
- **逻辑调整**: 在任何由系统自行生成（非外部大模型返回）的降级文本或模拟学术检索结果中，必须在文本起始处硬编码 `[MOCK_TRANSPORT] ` 前缀，确保日志与 SSE 传输链中能被清晰捕捉。

**R3. 统一参数预处理器 (Argument Processor)**
- **目标文件**: `server/agentic_engine.py`
- **目标位置**:
  - `_argument_pre_processor` 函数定义（~行 39-115）。
  - `execute_agent_react` 的工具遍历循环中（~行 375）。
- **逻辑调整**: 在 `execute_agent_react` 中，剥离原有针对 `generate_feature_alignment_matrix` 的硬编码补全逻辑。构造独立的 `_argument_pre_processor(tool_name, raw_args, blackboard)` 函数对入参进行容错补全与校验。当比较原始参数与修正后参数发生变化时，务必打印 `[ARGUMENT_PROCESSOR] 拦截到不规范参数...` 日志。将其调用位置设于 `tc_args_str` 解析之后、发送至前端 SSE 的 `agent_act` 之前。

## 3. Caveats
- 观察发现代码中实际上已基本预埋了上述方案要求的逻辑和打标输出，Worker 的主要任务是审查对齐或解决微小的边界条件。
- 仅在此次给定的 `server/llm_factory.py`, `tools/patent_tools.py`, `server/agentic_engine.py` 范围内进行了服务端分析，未越界检查 `frontend` 中对应的前端 SSE 事件拦截与视觉呈现是否适配了这三种标签。

## 4. Conclusion
- 熔断保护、Mock降级追踪及参数清洗的底层机制在目标模块中已处于原型完备状态。Worker 可无缝依照以上在 `server/llm_factory.py`, `tools/patent_tools.py`, `server/agentic_engine.py` 中标出的目标函数及逻辑说明，执行代码梳理、加固或验收。 
- 此举足以为系统提供抗网络抖动及抗大模型幻觉的有效容灾基础，同时符合所有标注必须显式可见的核心需求。

## 5. Verification Method
- **测试命令**：在项目根目录运行或调试测试脚本 `python server/run_test.py`。
- **验证行为断言**：
  1. 通过环境变量注入（如设置 `INJECT_LLM_FAILURE=true`）模拟失败，触发端点抛出异常。
  2. 观察控制台标准输出 (stdout)，应连续提示失败后出现 `[CIRCUIT_BREAKER]` 的熔断拦截日志。
  3. 拦截后直接触发降级模版生成流程，日志与返回结果中能稳定捕获到 `[MOCK_TRANSPORT]` 标签。
  4. 如果构造不规范或缺失所需特征ID的函数调用 (tool_calls)，系统能正确匹配索引，同时输出 `[ARGUMENT_PROCESSOR]` 自动参数修正提示。
