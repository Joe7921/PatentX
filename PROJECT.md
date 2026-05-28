# Project: PatentX Architecture Robustness
# Scope: Backend robustness features

## Architecture
- Backend: Python FastAPI server at `server/main.py`
- LLM Factory: `server/llm_factory.py`
- Agent Engine: `server/agentic_engine.py`
- Tools: `tools/patent_tools.py`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Circuit Breaker & Mock Tags | `server/llm_factory.py`, `tools/patent_tools.py` | none | DONE |
| 2 | Argument Processor | `server/agentic_engine.py` | none | DONE |
| 3 | Verification | `python server/run_test.py` | 1, 2 | DONE |

## Code Layout
- `server/llm_factory.py`: Handles model instantiations and local mock fallbacks.
- `server/agentic_engine.py`: Runs ReAct loops and manages tool arguments.
- `tools/patent_tools.py`: Search and DB tools, contains Mock output.
