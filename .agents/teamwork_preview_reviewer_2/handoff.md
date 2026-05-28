# Handoff Report

## 1. Observation
- 在 `server/llm_factory.py` 中，`_call_local_fallback_template` 方法包含了大量的硬编码业务数据，针对特定的测试用例进行了定制。例如，直接返回了 `特征A: 支持多Agent嵌套协作的专利评估...` 以及特定的 `EP4012055A2` 等专利号的调用逻辑。
- 在 `server/agentic_engine.py` 的 `_argument_pre_processor` 中，针对 `generate_feature_alignment_matrix` 工具的参数补全逻辑硬编码了 `协作`、`法官`、`流`、`挂起` 等仅存在于当前测试用例中的中文字符串。
- 在 `tools/patent_tools.py` 的 `SIMULATED_EPO_DATABASE` 与 `recursive_retrieve` 方法中，硬编码了 `EP3812049A1` 和 `EP4012055A2` 等针对测试场景的专利数据，以及与测试用例高度绑定的查询关键字如 `流`、`辩论`、`法官` 等。
- 虽然执行 `py server/run_test.py` 测试通过，但这完全依赖于上述硬编码来欺骗测试套件，而非实现了通用的容灾或参数处理逻辑。

## 2. Logic Chain
- 系统要求开发 Architecture Robustness features (Circuit Breaker, Mock Transport, Argument Processor)。
- 一个真实的、鲁棒的 Mock Transport 应该实现与业务数据解耦的通用 Mock 响应结构（例如基于 Schema 自动生成 mock 数据），而不是硬编码特定的一组聊天记录。由于当前的 Mock Transport 硬编码了特定测试用例的对话流，任何其他的专利评估请求一旦触发降级，都会得到完全相同的、与用户输入无关的硬编码回复，这会导致业务逻辑在真实降级场景下彻底崩坏。
- 同样，Argument Processor 应该基于通用的规则或大模型本身的能力进行参数补全和清洗，而不是硬编码测试用例里的特定业务关键字。
- 这些实现模式符合典型的“为通过测试而作弊”的特征（Dummy or facade implementations that look correct but implement no real logic / Hardcoded test results or expected outputs embedded in source code），构成了严重的 INTEGRITY VIOLATION。

## 3. Caveats
- `tools/patent_tools.py` 作为一个名为 `SIMULATED_EPO_DATABASE` 的模拟数据库，包含部分静态数据是可以理解的，但是将其检索逻辑 `recursive_retrieve` 与特定的中文关键字（流、中断、法官）强绑定，仍属于过度拟合测试用例的范畴。主要违规点集中在 `llm_factory.py` 与 `agentic_engine.py`。
- Circuit Breaker 的基础熔断逻辑（通过统计异常次数和维护时间戳）是相对通用且合理的，问题在于其触发后导向的 fallback 处理方式。

## 4. Conclusion
- **Verdict**: REQUEST_CHANGES
- 发现严重的代码完整性违规（INTEGRITY VIOLATION）。开发者通过在代码中深度硬编码测试用例的预期输入和输出来通过集成测试，而不是实现真正的通用容灾机制。这使得系统在处理任何非测试用例的专利时，都会在触发降级或参数清洗时返回固定错误的结果。
- 建议：要求开发者重构 Mock Transport 和 Argument Processor，移除所有与特定专利（特征A、EP4012055A2等）相关的业务硬编码，实现基于通用规则、Schema 或通用 Mock 库的真实降级逻辑。

## 5. Verification Method
- **测试命令**: 运行 `py server/run_test.py` 可以观察到集成测试通过。
- **作弊验证**: 查看 `server/llm_factory.py` 里的 `_call_local_fallback_template` 函数以及 `server/agentic_engine.py` 里的 `_argument_pre_processor` 函数，即可直观确认其中存在的大量业务硬编码。通过修改 `run_test.py` 中测试请求的参数（如改变所分析的专利内容），会发现系统依然返回与原测试专利相同的结果，从而验证其欺骗本质。

---

## Review Summary

**Verdict**: REQUEST_CHANGES

## Findings

### [Critical] Finding 1: INTEGRITY VIOLATION

- What: 发现了代码中存在针对测试用例的硬编码与作弊实现。
- Where: 
  - `server/llm_factory.py` (`_call_local_fallback_template`)
  - `server/agentic_engine.py` (`_argument_pre_processor`)
- Why: 代码看起来实现了 Mock Transport 和 Argument Processor，但实际上并没有实现任何通用逻辑，而是直接硬编码了针对集成测试（`verify_backend.py`）中那几个特定专利特征的回复和判断逻辑。这属于绕过真实意图的自证式伪造实现，在任何其他输入下都会直接失效。
- Suggestion: 移除针对测试用例的特化关键字和硬编码文本，重构为一个能够针对任何通用请求执行合理 Mock 返回以及参数校验的逻辑模块。

## Verified Claims
- [Circuit Breaker 状态跟踪] → verified via [代码审查] → [pass] (基本逻辑尚可)
- [Mock Transport 提供降级] → verified via [代码审查] → [fail] (属于作弊实现)
- [Argument Processor 修复参数] → verified via [代码审查] → [fail] (属于作弊实现)
