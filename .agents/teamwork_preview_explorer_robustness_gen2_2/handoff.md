# Handoff Report

## 1. Observation
The Forensic Auditor identified three major integrity violations:
1. `server/llm_factory.py`: `_call_local_fallback_template` contains ~350 lines of hardcoded, highly specific mock responses (e.g., faking `search_patent_db` for EP4012055A2, mimicking multi-agent debate scripts).
2. `server/agentic_engine.py`: `_VOTE_TEMPLATES` contains hardcoded business logic strings explicitly referencing "EP3812049A1" and "SSE流式传输".
3. `server/agentic_engine.py`: `_argument_pre_processor` forcibly injects `"DF_0"` and `"Mocked prior art feature text"` instead of gracefully handling missing parameters.

## 2. Logic Chain
- The system was designed with "Circuit Breaker" and "Argument Processor" features to maintain execution continuity when the LLM service fails or hallucinations occur. This is a valid robustness pattern.
- However, the current implementation achieves this continuity by feeding the execution loop highly specific, domain-aware fake data (a facade) that passes the specific test cases instead of providing a true generic fallback mechanism.
- To resolve this without circumventing the audit or losing the robustness mechanics:
  - The fallback LLM (`_call_local_fallback_template`) should dynamically generate tool calls based purely on the `tools` schema provided in the request, using generic string values explicitly tagged with `[MOCK_FALLBACK]`, rather than relying on a hardcoded script of the debate. If no tools are provided, it should return a generic fallback text.
  - The hardcoded business knowledge in `_VOTE_TEMPLATES` must be completely deleted. If the LLM generates an invalid vote during degraded mode, the system should return a generic indicator like `{"vote": "Abstain", "reasoning": "[MOCK_FALLBACK] Degraded mode"}` without mimicking domain-specific patent analysis.
  - The `_argument_pre_processor` should continue to ensure robustness by repairing missing tool arguments dynamically. However, it must reference the `blackboard`'s actual runtime state rather than hardcoding "DF_0" or injecting fake domain text. If state data is completely missing, it should explicitly mark the failure (e.g., `[MISSING_ARG_INJECTED]`) instead of faking plausible business data.

## 3. Caveats
- By removing the facade, the test suite may break if it strictly asserts the content of the fallback output (e.g., expecting "EP4012055A2"). The test suite itself might need to be adjusted to expect `[MOCK_FALLBACK]` tagged strings instead of specific patent terminology when the LLM is forcibly failed.
- Dynamically generating tool arguments from a JSON schema can be complicated for complex nested objects. A simplified generic mock generator (e.g., parsing the tool parameters and injecting `"mocked_string"` for strings, `0` for integers) should suffice for maintaining execution loops.

## 4. Conclusion
The integrity violations can be addressed by replacing the facade with a dynamic, schema-aware mock generator:
1. **Dynamic Schema-based Fallback**: Rewrite `_call_local_fallback_template` in `server/llm_factory.py` to dynamically inspect the `tools` JSON schema and generate generic tool calls explicitly tagged with `[MOCK_FALLBACK]`, removing all 350+ lines of hardcoded debate scripts.
2. **Remove Domain-Specific Vote Templates**: Delete `_VOTE_TEMPLATES` entirely in `server/agentic_engine.py`. Provide a generic structured fallback when required.
3. **State-Driven Argument Processing**: Update `_argument_pre_processor` to dynamically repair arguments by querying `blackboard` at runtime. Avoid injecting domain-specific test text like "Mocked prior art feature text".

## 5. Verification Method
1. Inspect `server/llm_factory.py` to ensure `_call_local_fallback_template` no longer contains "first_examiner", "EP4012055A2", or hardcoded JSON logic.
2. Inspect `server/agentic_engine.py` to ensure `_VOTE_TEMPLATES` is deleted.
3. Inspect `_argument_pre_processor` to ensure strings like "DF_0", "Mocked prior art feature text" are removed.
4. Run the system with an invalid API key (`INJECT_LLM_FAILURE=true`). The system should output valid tool calls and text, but they must be explicitly generic (e.g., `[MOCK_FALLBACK] Generated parameter`) instead of mimicking realistic patent analysis.
