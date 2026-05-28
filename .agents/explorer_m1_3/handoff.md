# 架构健壮性优化 (Circuit Breaker, Argument Processor, Mocking) 实施方案

## 1. Observation
通过审查项目计划文档 `implementation_plan.md`，以及目标代码文件 `server/llm_factory.py`, `server/agentic_engine.py`, 和 `tools/patent_tools.py` 的结构与上下文环境，得出以下观察结果：
- **LLM 工厂层**：`server/llm_factory.py` 中的 `MockLLMClient._call_model` 和 `_call_model_chat` 负责与大模型 API 通信，当请求异常时会进入容灾机制；降级逻辑则在 `_call_local_fallback_template` 中。
- **引擎层**：`server/agentic_engine.py` 中的 `execute_agent_react` 负责执行 ReAct 循环，解析工具调用并进行传参。目前需要在工具执行前进行参数验证与自动补全。
- **工具层**：`tools/patent_tools.py` 包含了模拟专利检索及学术检索的方法，其中 `search_academic_db` 函数原本可能有其他的输出标记规范。

## 2. Logic Chain
为满足“提供带有显著标签的熔断、参数预处理及Mock降级”的核心需求，Worker 实施时应遵循以下逻辑链路：
1. **Circuit Breaker 熔断机制**：需要全局状态来记录各模型的连续失败次数和恢复时间点。在 HTTP 接口调用前，应当主动判定时间戳，若在熔断期内则直接中断请求抛出异常，进入下一层容灾，从而节约网络等待时间。并显式使用 `[CIRCUIT_BREAKER]` 日志。
2. **Mock Transport 显式标注**：在底层触发本地 Fallback 兜底生成时，需在日志控制台以及返回的响应内容中强制拼入 `[MOCK_TRANSPORT]` 标签，使用户能够清晰感知到当前非线上模型返回。
3. **Argument Processor 工具预处理器**：ReAct 在产生幻觉或传参缺失时，极容易导致下游工具执行崩溃。因此需在 `agentic_engine.py` 内抽离出 `_argument_pre_processor` 函数，通过 Blackboard 内缓存的状态（如国内特征列表、已检专利数据等）补齐如 `domestic_feature_id` 等缺失字段，并在发生修正时输出 `[ARGUMENT_PROCESSOR]` 标签。
4. **统一工具层输出**：将独立的 `search_academic_db` 工具里的旧版标签 `[MOCK NPL]` 更正为统一标准 `[MOCK_TRANSPORT]`，确保系统各层感知一致。

## 3. Caveats
- 熔断机制使用进程内的类属性（例如 `LLMFactory._failure_counts`）进行管理，这在多进程并发环境中（如 Uvicorn `workers > 1`）可能会产生状态不一致。本方案假设当前处于单实例测试/运行环境，若是多实例则建议后续采用 Redis 管理熔断状态。
- 参数处理器 `_argument_pre_processor` 强依赖于 `blackboard.claim_features` 等数据的完整性，如果上下文数据为空，该处理器依然只能生成 Mock 参数。

## 4. Conclusion
Worker 需要对以下三个文件进行精确定向修改以实现需求 R1-R3。

### Step-by-Step Implementation Strategy:

**Target 1: `server/llm_factory.py` (R1 & R2)**
1. **[R1] 增加熔断状态**：
   - 在 `LLMFactory` 类的顶层定义类属性：`_failure_counts = {}` 和 `_circuit_breaker_until = {}`。（大概在代码第26行左右）
2. **[R1] 执行熔断拦截**：
   - 在 `_call_model` 及 `_call_model_chat` 函数内，在组装 API url 前，增加熔断判定逻辑：获取当前时间戳并比对对应模型的 `_circuit_breaker_until`。
   - 处于熔断期则打印 `[CIRCUIT_BREAKER]` 标签日志并抛出 `ValueError`。
   - 若熔断结束，则清零计时器与失败计数。
   - 在 `except Exception as e:` 块中拦截异常，累加 `_failure_counts`，若达到3次则设置 30 秒后的恢复时间戳，并打印 `[CIRCUIT_BREAKER]` 熔断触发日志。
3. **[R2] 显式标注 Mock**：
   - 在 `_call_local_fallback_template` 开头，打印 `[MOCK_TRANSPORT] 检测到网络异常或熔断，当前请求已切换至本地 Mock 模板生成。`，并将其记录至 blackboard。
   - 在该函数返回值构建阶段，对生成的 `content_text` 添加 `[MOCK_TRANSPORT]` 前缀（包括调用工具的提示、以及完成流程的兜底提示）。

**Target 2: `server/agentic_engine.py` (R3)**
1. **[R3] 定义独立参数处理器**：
   - 在文件上方（例如第39行处，`_load_agent_config` 函数后）新增 `def _argument_pre_processor(tool_name: str, raw_args: Any, blackboard: Blackboard) -> Dict[str, Any]:`。
   - 针对 `generate_feature_alignment_matrix` 工具，检查并补全 `domestic_feature_id`, `domestic_feature`, `prior_art_id`, `prior_art_feature` 以及 `expert_annotations`。
   - 当参数发生更改时，通过 `print(f"[ARGUMENT_PROCESSOR] 拦截到不规范参数，已动态修正参数为: {tc_args}")` 输出。
2. **[R3] 接入预处理器**：
   - 定位 `execute_agent_react` 函数内处理 `tool_calls` 的逻辑（约 370 行附近）。
   - 将原有解析参数的代码替换或封装为 `tc_args = _argument_pre_processor(tc_name, tc_args_str, blackboard)`。

**Target 3: `tools/patent_tools.py` (R1/R2 alignment)**
1. **[R1/R2] 更新 Mock 标签**：
   - 定位 `search_academic_db` 函数。
   - 将原 `[MOCK NPL]` 替换为 `[MOCK_TRANSPORT]` 标签，使用如 `msg = f"[MOCK_TRANSPORT] 找到与 '{query}' 相关的学术引文..."` 进行返回和输出。

## 5. Verification Method
- **测试命令**：执行 `python server/run_test.py`。
- **验证项 1**：在测试用例使用假 Key（触发快速降级）或多次异常后，确保终端输出流或 `test_output.log` 中能够抓取到 `[CIRCUIT_BREAKER]` 和 `[MOCK_TRANSPORT]` 字样。
- **验证项 2**：在模型调用工具时故意留空必填字段，检查是否能够看到 `[ARGUMENT_PROCESSOR]` 标签的日志输出，证明参数补全成功且未发生调用崩溃。
