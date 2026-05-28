# Handoff Report: PatentX Robustness Update (Milestone 1)

## 1. Observation (观察结果)
1. **`server/llm_factory.py`**：已定义类属性 `_failure_counts` 和 `_circuit_breaker_until`。但在 `_call_model`（第110-120，170-178行）与 `_call_model_chat`（第228-238，276-284行）中，熔断器（Circuit Breaker）的核心逻辑存在代码重复。此外，本地回退模板中已经实现了 `[MOCK_TRANSPORT]` 的日志。
2. **`server/agentic_engine.py`**：已成功从 `execute_agent_react` 抽离出独立的 `_argument_pre_processor` 函数（第38行）。但在针对 `generate_feature_alignment_matrix` 进行参数补全时，将其参数 `prior_art_feature` 和 `expert_annotations` 强制转换为了 JSON 字符串（例如第119行 `tc_args["prior_art_feature"] = json.dumps(...)`）。
3. **`tools/patent_tools.py`**：`search_academic_db` 函数包含显式的 `[MOCK_TRANSPORT]` 返回标识，但 `search_patent_db` 和 `generate_feature_alignment_matrix` 缺乏统一的 Mock Transport 日志标识。更严重的是，`generate_feature_alignment_matrix` 函数内部直接按字典类型处理参数（如 `prior_art_feature['id']`），当接收到来自引擎层的 JSON 字符串格式参数时，会触发 `TypeError: string indices must be integers` 异常。

## 2. Logic Chain (逻辑链)
1. **Circuit Breaker 冗余**：`llm_factory.py` 中的重复代码不仅增加了维护成本，还不符合健壮性设计的 DRY 原则。应提取为公共内部函数。
2. **数据类型冲突（Argument Processor 与 Mock Transport）**：`agentic_engine.py` 中的参数预处理器将关键参数格式化为字符串，而 `patent_tools.py` 期望接收字典对象。这种类型错配会直接导致工具在执行时崩溃。
3. **Mock Transport 标准化不足**：根据架构要求，工具层应统一 Mock Transport 的行为。当前仅有 `search_academic_db` 实现了标准化，其他核心仿真工具遗漏了相关的日志或返回标识，不满足 Milestone 1 中 "Mock Transport standardization" 的要求。

## 3. Caveats (注意事项)
- 尚未排查 MCP 服务端包装工具的内部反序列化机制。如果 MCP 客户端对字符串参数具有自动 `json.loads` 反序列化处理，该类型错误可能在跨进程调用时被规避，但在进行直接代码层调用（如内部函数互调）时依然存在触发异常的风险。
- 当前的 `_argument_pre_processor` 仅对 `generate_feature_alignment_matrix` 进行了硬编码拦截，未采用注册表机制，后续扩展更多工具预处理时可能导致函数体过于臃肿。

## 4. Conclusion (结论与修复策略)
针对 Milestone 1 的 Robustness Features，提出以下修复策略：
1. **R1 (Circuit Breaker)**：重构 `server/llm_factory.py`，将熔断检查和失败计数的判断逻辑封装为独立的内部方法（如 `_check_circuit_breaker` 和 `_handle_llm_failure`），以消除代码冗余。
2. **R2 (Mock Transport)**：在 `tools/patent_tools.py` 中，对所有仿真函数（`search_patent_db`、`generate_feature_alignment_matrix`）增加显式的 `[MOCK_TRANSPORT]` 打印或日志输出。同时，作为健壮性补充，在 `generate_feature_alignment_matrix` 入口处增加参数兼容逻辑：若是字符串则使用 `json.loads` 解析，确保兼容字典和 JSON 字符串两种格式输入。
3. **R3 (Argument Processor)**：在 `server/agentic_engine.py` 中，调整 `_argument_pre_processor` 的补全逻辑，保证 `tc_args` 中设置的值与目标工具的预期数据类型（字典对象）保持一致，避免不必要的 `json.dumps`；或者在工具层统一做好反序列化防御。

## 5. Verification Method (验证方法)
1. 在项目根目录下运行测试命令（如 `pytest`），确认流程可跑通且无 `TypeError`。
2. 检查 `server/llm_factory.py` 确认重复的熔断代码已提取。
3. 查阅终端输出日志，验证执行 `search_patent_db` 或 `generate_feature_alignment_matrix` 时是否稳定打印了包含 `[MOCK_TRANSPORT]` 关键字的日志。
4. 构造包含 JSON 字符串和包含字典对象的双重单元测试用例，传入 `generate_feature_alignment_matrix`，确认均能正确输出而不再崩溃。
