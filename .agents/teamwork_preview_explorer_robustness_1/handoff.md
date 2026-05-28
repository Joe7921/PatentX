# Handoff Report: Robustness Features (Milestone 1)

## 1. Observation
- **Circuit Breaker (`server/llm_factory.py`)**: `LLMFactory` implements `_failure_counts` and `_circuit_breaker_until` at the class level. In `_call_model` and `_call_model_chat`, consecutive failures increment the count. Upon 3 failures, it triggers a 30s circuit breaker timeout (lines 173, 280) and raises a ValueError to trigger the fallback model or local template.
- **Mock Transport (`server/llm_factory.py`, `tools/patent_tools.py`)**: 
  - `llm_factory.py`: The `_call_local_fallback_template` prints a `[MOCK_TRANSPORT]` log (line 289), but the actual `content` strings in the returned dictionaries (e.g., lines 309, 323, etc.) do not contain an explicit `[MOCK_TRANSPORT]` prefix.
  - `patent_tools.py`: `search_academic_db` explicitly returns a string prefixed with `[MOCK_TRANSPORT]` (line 104), but `search_patent_db` and the simulated DB responses do not.
- **Argument Processor (`server/agentic_engine.py`, `tools/patent_tools.py`)**:
  - `agentic_engine.py`: A centralized `_argument_pre_processor` is implemented (lines 38-135) to handle JSON parsing, default value completion, and ID normalization for `generate_feature_alignment_matrix` before tool execution.
  - `patent_tools.py`: The tool `generate_feature_alignment_matrix` (lines 116-140) still contains redundant hardcoded normalization logic for `domestic_feature_id` and `prior_art_id` that overlaps entirely with the `_argument_pre_processor`.

## 2. Logic Chain
- **Circuit Breaker (R1)**: The logic correctly traps HTTP exceptions, increments failure counts, triggers a 30-second cooldown, and cascades the exception to trigger the primary -> fallback -> mock LLM chain. The implementation is mostly sound for an asyncio context (GIL protects dictionary state updates).
- **Mock Transport explicitly (R2)**: The prompt and project plan require "Mock Transport explicitly". Currently, the explicit tagging is inconsistent. While console logs show the mock routing, the end user or downstream UI won't see the explicit `[MOCK_TRANSPORT]` tag in the LLM's `content` payload. Prepending `[MOCK_TRANSPORT]` to the fallback template responses will fix this.
- **Argument Processor (R3)**: The goal of an argument processor is to decouple argument sanitization from the tool execution itself. The presence of redundant normalization code in `patent_tools.py` violates the single responsibility principle and makes the code harder to maintain. The tool should assume inputs are already sanitized by the engine's pre-processor.

## 3. Caveats
- I did not review the tests, so I am assuming the fallback template's exact string matches are not rigidly asserted without `[MOCK_TRANSPORT]`. If they are, tests will need to be updated.
- Removing normalization from `patent_tools.py` assumes that `generate_feature_alignment_matrix` is exclusively called via `_argument_pre_processor`. If other parts of the code call it directly with dirty inputs, it might fail.

## 4. Conclusion
**Proposed Fix Strategy for Milestone 1:**
1. **R1 (Circuit Breaker)**: The core implementation is correct. No structural changes needed. Ensure `LLMFactory._circuit_breaker_until` and `LLMFactory._failure_counts` remain class variables.
2. **R2 (Mock Transport explicitly)**: 
   - Modify `_call_local_fallback_template` in `server/llm_factory.py` to prepend `[MOCK_TRANSPORT] ` to all generated `"content"` strings.
   - Optionally add `[MOCK_TRANSPORT]` explicit text to `search_patent_db` outputs in `tools/patent_tools.py` for consistency.
3. **R3 (Argument Processor)**: 
   - Remove the redundant normalization logic (lines 116-140) from `generate_feature_alignment_matrix` in `tools/patent_tools.py`.
   - Rely solely on the `_argument_pre_processor` in `server/agentic_engine.py` to sanitize and inject proper `domestic_feature_id`, `prior_art_id`, etc.

## 5. Verification Method
- **Static Check**: Inspect `tools/patent_tools.py` to ensure lines 116-140 are removed. Inspect `server/llm_factory.py` to ensure `"content": "[MOCK_TRANSPORT] ..."` is used.
- **Dynamic Test**: Run the project test suite or trigger a mock response. The output should explicitly display `[MOCK_TRANSPORT]` and the system should not crash when passing raw LLM tool arguments to `generate_feature_alignment_matrix`.
