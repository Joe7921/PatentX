# LLM API 真实接入配置计划 (生产级重构版本)

本计划旨在根据用户指示，**废除声明模式与 Mock 机制，完全面向生产环境进行设计**。所有代码将直接调用真实 API 接口，并去除全部硬编码的 Mock 话术。对于 Fallback 降级机制测试，将引入生产级环境变量故障注入。

## 主要变更

### 1. 修改 `server/llm_factory.py`
- 移除 `_get_mock_response` 和所有 Mock 响应分支。
- 强制要求存在 `DEEPSEEK_API_KEY` 环境变量，否则直接抛出 `ValueError`。
- 实现基于环境变量 `INJECT_LLM_FAILURE` 的混沌工程故障注入，当设置为 `"true"` 且调用 `epo_examiner` 的 `deepseek-v4-flash` 模型时，故意抛出 `ValueError("Simulated 429 Rate Limit Exceeded")`，以触发降级路由。

### 2. 修改 `server/test_api.py`
- 在 `send_resume` 中添加 try-except 块，以捕捉并输出在单线程 ASGI Transport 下可能发生并发调用的任何死锁或异常信息。

### 3. 修改代理配置文件 (`app/agents/_custom/`)
- `patent_judge.yaml` -> 主模型：`deepseek-v4-pro`，备选：`deepseek-v4-flash`。
- `epo_examiner.yaml` -> 主模型：`deepseek-v4-flash`，备选：`deepseek-v4-pro`。
- `patent_applicant.yaml` -> 主模型：`deepseek-v4-flash`，备选：`deepseek-v4-pro`。

## 验证计划
1. 在测试时注入环境变量：`$env:INJECT_LLM_FAILURE="true"` 
2. 运行：`py server/verify_backend.py`，验证降级日志与重算概率。
3. 运行不带环境变量的正常环境测试，验证全生产环境链路。
