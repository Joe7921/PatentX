# Handoff Report

## 1. Observation
- In `server/llm_factory.py`, the `_call_local_fallback_template` method contains a 350-line `if/elif` block that hardcodes specific tool calls, JSON arguments, and narrative responses for `first_examiner`, `second_examiner`, and `chairman` based on the exact round of interaction. This includes domain-specific data such as `"EP4012055A2"`, `"search_patent_db"`, and `"generate_feature_alignment_matrix"`.
- In `server/agentic_engine.py`, the `_VOTE_TEMPLATES` dictionary contains explicitly hardcoded domain strings such as `"核心技术特征A（SSE流式传输）与EP3812049A1的状态流式传输特征高度重合..."` and `"EP4012055A2的分层辩论系统"`.
- In `server/agentic_engine.py`, the `_argument_pre_processor` forcibly patches missing arguments with specific hardcoded test data, such as `"DF_0"` and `"Mocked prior art feature text"`.

## 2. Logic Chain
- The Forensic Auditor correctly identified these elements as an Integrity Violation. The system acts as a fraudulent Facade during fallback mode by replaying a perfectly scripted evaluation for a specific patent, bypassing genuine workflow logic.
- To eliminate the violation while preserving the required robust features (Circuit Breaker, Argument Processor, and explicit `[MOCK_TRANSPORT]` tags):
  1. **Schema-Driven Dynamic Mocking**: Replace the 350-line hardcoded block in `_call_local_fallback_template` with a dynamic generic mock generator. When the Circuit Breaker routes to the fallback, the system should parse the provided `tools` JSON schema from the request and dynamically generate generic mock arguments (e.g., `{"query": "mock_query_string"}`) and generic conversational text, rather than hardcoded domain responses.
  2. **Generic Template Generation**: Completely remove `_VOTE_TEMPLATES`'s domain-specific strings (like `EP3812049A1`). Replace them with dynamic templates that interpolate actual data from the `Blackboard` (e.g., `"Based on the {count} retrieved prior arts, the feature alignment matrix shows..."`).
  3. **Type-Safe Argument Processor**: Refactor `_argument_pre_processor`. Instead of forcefully injecting `"DF_0"`, the processor should use safe generic type defaults for missing keys (e.g., empty strings or `"unknown_feature_id"`) or dynamically retrieve the closest match from the Blackboard without hardcoding indices or test data strings.

## 3. Caveats
- Since the Mock Fallback will now return generic text and dynamically generated dummy arguments rather than a perfectly coherent logical chain, tests that rely on the Mock system to output a flawless, domain-specific patent analysis will fail. The testing suite must be updated to expect generic responses when evaluating the Circuit Breaker's fallback mode.

## 4. Conclusion
- **INTEGRITY FIX STRATEGY**: The project must completely strip all domain-specific hardcoded strings (patent IDs, feature descriptions, and scripted round-by-round dialogue) from `llm_factory.py` and `agentic_engine.py`. By shifting to a **Schema-Driven Dynamic Mock Generator** and a **Type-Safe Parameter Defaulting mechanism**, the project will maintain its robustness (handling missing parameters and API outages) without violating structural integrity or acting as a deceptive Facade.

## 5. Verification Method
1. **Source Code Check**: Run `grep -r "EP3812049A1" server/` and `grep -r "DF_0" server/`. The output should be completely empty, confirming the removal of all hardcoded domain data.
2. **Behavioral Test (Offline Mode)**: Set a fake API key (`DEEPSEEK_API_KEY=sk-c714d64...`) or trigger the Circuit Breaker, then execute the workflow. Ensure that the generated output contains generic fallback texts (e.g., `"[MOCK_TRANSPORT] Fallback response generated"`) and that any tool calls use dynamically generated generic parameters rather than the previously scripted patent analysis.
