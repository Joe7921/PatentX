# Project: PatentX
# Scope: Robustness Features

## Architecture
- `llm_factory.py`: 大模型调用中心。添加熔断机制以及Mock标签。
- `agentic_engine.py`: 代理执行引擎。抽取独立的参数处理层。
- `patent_tools.py`: 工具函数库。统一Mock标签。

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1 | Implement Circuit Breaker & Mocking Explicit Tags (R1, R2) | none | DONE |
| 2 | M2 | Centralize Argument Processor (R3) | none | DONE |

## Interface Contracts
### `agentic_engine.py` 内部
- `_argument_pre_processor(tool_name, raw_args, blackboard)` -> `cleaned_args`
