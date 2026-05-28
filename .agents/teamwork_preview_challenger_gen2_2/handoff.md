# 鲁棒性特性实证挑战移交报告 (Robustness Features Handoff Report)

## 1. Observation (观察结果)

我在本地环境编写了 `test_robustness.py` 隔离测试脚本，对当前的鲁棒性机制进行了黑盒与白盒结合的实证测试，具体观察如下：

1. **Circuit Breaker (熔断器)** (`server/llm_factory.py`)：
   - 当人为设置 `_failure_counts = 3` 且熔断时间结束（`now >= cb_until`）时发起请求，系统因使用无效的 API Key 而请求失败（返回 401 错误）。
   - **观察输出**：请求失败后，`_failure_counts` 被记录为 `1`。这表明系统在发起半开请求前，主动执行了 `LLMFactory._failure_counts[mapped_model] = 0`，抹除了所有的历史失败记忆。
   
2. **Mock Transport (模拟传输层)** (`server/llm_factory.py`)：
   - 在测试中，我将代理角色设置为 `"first_examiner"`，并向 fallback 系统输入了一个完全与专利无关的提示词 (`"How do I bake a cake?"`)。
   - **观察输出**：Fallback 返回了高度硬编码的 PatentX 业务内容：`"[MOCK_TRANSPORT] 正在执行检索，尝试从 EPO 数据库中搜索与协作、法官和流式传输相关的专利文献。"` 并且自动附带了调用 `search_patent_db` 的动作。

3. **Argument Processor (参数处理器)** (`server/agentic_engine.py`)：
   - 构造了一个空的 Blackboard 环境并调用 `_argument_pre_processor` 处理 `"generate_feature_alignment_matrix"` 工具，输入参数为空字典 `{}`。
   - **观察输出**：处理器打印出 `"拦截到不规范参数，已修正参数为..."`，并主动在参数内“无中生有”地塞入了：`'domestic_feature_id': 'DF_0'`、`'prior_art_id': 'UnknownID'` 以及硬编码的 Mock 结构 `'prior_art_feature': '{"id": "UnknownID_F1", "text": "Mocked prior art feature text", "focus": "Mocked focus"}'`。

## 2. Logic Chain (逻辑链条)

1. **Circuit Breaker**：熔断器设计的核心之一是“半开 (Half-Open)”状态，即在熔断冷却期结束后放行**部分**流量试探服务是否恢复。如果试探请求依然失败，理应立刻重新熔断。但当前 `llm_factory.py` 在冷却期刚过时直接把错误计数清零的逻辑，破坏了半开状态：试探失败会让错误计数变成 1，系统必须再忍受 2 次连续失败才会重新熔断。这将严重放大下游 API 故障时的重试风暴（Retry Storm）。
2. **Mock Transport**：`LLMFactory` 本应是底层基础设施组件，负责调度并处理模型接口。然而它内置的 `_call_local_fallback_template` 方法包含了大量硬编码的条件判断（如 `if agent_role in ("first_examiner", "epo_examiner"):`）和 PatentX 具体的强业务耦合内容。这意味着底层模块越权处理了上层领域逻辑，违背了“关注点分离（Separation of Concerns）”的设计原则。
3. **Argument Processor**：核心调度引擎 (`agentic_engine.py`) 应当仅负责工具调度的编排（ReAct Loop）。目前的 `_argument_pre_processor` 直接侵入了某一个特定工具的具体参数细节，并通过大量生硬的 if-else 注入“幻觉”数据。这种做法不仅掩盖了大模型真正输出异常的原因，还导致引擎层臃肿不堪。工具的参数校验与回退兜底应当在特定工具的实现模块（如 `patent_tools.py`）中完成。

## 3. Caveats (注意事项)

- 隔离脚本没有对 `httpx` 库做深度网络拦截（Mock），而是利用配置无效 API Key（例如 `sk-real-key` 或 `sk-c714d64`）的方式，让实际网络请求快速报 401 Authentication Fails 错误。通过这种方式成功从侧面精准验证了重试与重置计数器的逻辑状态，不影响最终结论。
- 此次实证并未覆盖大流量并发下共享的全局字典 `_circuit_breaker_until` 可能出现的线程/协程安全问题，但其逻辑层面的缺陷已足够严重。

## 4. Conclusion (结论)

先前的审计结论完全成立。当前的系统虽然具备了所谓的“容灾机制”，但这些鲁棒性功能（Circuit Breaker、Mock Transport、Argument Processor）的工程实现都不符合规范。

**明确的行动结论**：
1. **重构 Circuit Breaker**：必须删除 `server/llm_factory.py` 中 `now >= cb_until` 时的计零重置代码，修改为只有当请求明确成功（返回 200 HTTP 状态码）时，才重置 `_failure_counts`，真正落实半开状态（Half-Open State）。
2. **解耦 Mock Transport**：应当将庞大的业务 Mock 模板从 `server/llm_factory.py` 彻底移出，最好使用插件化架构，将 Mock 数据提取至单独的文件（如 `mock_transport.py`）。
3. **转移 Argument Processor 逻辑**：应彻底移除 `server/agentic_engine.py` 中的 `_argument_pre_processor` 特定业务打补丁逻辑，转由具体工具（如 `patent_tools.py` 中的目标函数）进行自己的参数清洗或在执行时直接抛出校验失败。

## 5. Verification Method (验证方法)

我已经在工作区生成了包含验证逻辑的脚本。可以通过以下指令直接复现与独立验证：
```powershell
uv run "d:\Antigravity projects\PatentX\.agents\teamwork_preview_challenger_gen2_2\test_robustness.py"
```
修复完成后再次运行该脚本，应看到以下状态：
1. **Circuit Breaker**：输出信息应提示在 1 次失败后，由于处于半开验证态，`_failure_counts` >= 3，立刻重新激活了熔断器。
2. **Mock Transport**：当接收到与专利无关的提示时，不再返回硬编码的 `search_patent_db` 工具调用和 EPO 业务话术。
3. **Argument Processor**：不再出现 `"拦截到不规范参数，已修正参数为..."`，而是能保持传入的空字典状态原样传递，或者由下层工具自行处理。
