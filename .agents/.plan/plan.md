# 健壮性优化实施计划

## 目标
实现架构健壮性优化，主要包括：
1. 熔断机制 (Circuit Breaker)
2. Mock传输层显式标注 (Mock Transport)
3. 工具参数预处理器 (Argument Processor)

## 细节
- **llm_factory.py**: 增加失败计数器和熔断逻辑。在降级和熔断时分别输出 `[CIRCUIT_BREAKER]` 和 `[MOCK_TRANSPORT]`。
- **agentic_engine.py**: 抽取独立的 `_argument_pre_processor` 函数，并在修改参数时输出 `[ARGUMENT_PROCESSOR]`。
- **patent_tools.py**: 统一使用 `[MOCK_TRANSPORT]` 替换之前的 `[MOCK NPL]` 标记。

## 约束
- `python server/run_test.py` 集成测试必须100%通过。
- 遵循所有文件编辑安全规则（禁止使用PS命令修改，必须使用MCP工具，全中文交互等）。
