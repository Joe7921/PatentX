# Robustness Features Investigation Handoff Report

## 1. Observation
I have investigated the specified files. Here are the direct observations:

1. **Circuit Breaker** (`server/llm_factory.py`):
   - In `_call_model` (lines 117-119) and `_call_model_chat` (lines 236-238), when the circuit breaker timeout expires (`now >= cb_until`), the code explicitly resets both `_circuit_breaker_until` and `_failure_counts` to `0` before making the request. 
   - If a request succeeds, it resets the count to `0` (lines 158 and 266).
   - If it fails, it increments the count and triggers the breaker if `>= 3` (lines 170-173 and 277-280).

2. **Mock Transport explicitly** (`server/llm_factory.py`):
   - The method `_call_local_fallback_template` spans over 340 lines (lines 288-628) inside the generic LLM factory.
   - It contains highly coupled PatentX business logic, checking hardcoded `agent_role` strings (e.g., `"first_examiner"`, `"chairman"`) and returning hardcoded JSON responses with specific tool calls and arguments.

3. **Argument Processor** (`server/agentic_engine.py` & `tools/patent_tools.py`):
   - In `server/agentic_engine.py`, the `_argument_pre_processor` function (lines 38-135) contains monolithic, tool-specific patching logic for `generate_feature_alignment_matrix`. It uses hardcoded Chinese keyword string matching to resolve arguments like `domestic_feature_id` to `"DF_0"`, `"DF_1"`, etc.
   - In `tools/patent_tools.py`, the `generate_feature_alignment_matrix` function (lines 106-177) duplicates similar normalization logic (lines 116-134).

## 2. Logic Chain
1. **Circuit Breaker**: Because the failure count is reset to 0 immediately upon timer expiration, the system loses its "Half-Open" state memory. A struggling API will require 3 subsequent failures to trip the breaker again, exacerbating load. By simply removing the premature reset before the request, the first failure after a timeout will increment the count to `4` (which is `>= 3`), instantly tripping the breaker again. A success will still properly reset the count to `0`.
2. **Mock Transport**: The LLM Factory should be an infrastructural component agnostic to business logic. The massive `_call_local_fallback_template` violates separation of concerns. It should be extracted into an explicit `MockTransport` component (e.g., `mock_transport.py`) that the LLM Factory delegates to.
3. **Argument Processor**: The engine layer (`agentic_engine.py`) should not be coupled with specific tool implementation details or Chinese keywords. The patching logic must be decoupled by either creating a generic `ArgumentProcessor` registry where tools can register their own pre-processors, or by moving the specific parameter-fixing logic directly into the domain layer (`patent_tools.py`).

## 3. Caveats
- No caveats. The observations are based on direct static analysis of the source code.

## 4. Conclusion
**Proposed Fix Strategy for Milestone 1:**
- **R1 - Circuit Breaker**: Delete lines 118-119 and 236-237 in `server/llm_factory.py` to allow the natural `>= 3` logic to provide a Half-Open state.
- **R2 - Mock Transport**: Move the `_call_local_fallback_template` logic out of `server/llm_factory.py` into a separate `server/mock_transport.py` module. Have `llm_factory.py` explicitly invoke this new mock layer.
- **R3 - Argument Processor**: Remove `_argument_pre_processor`'s tool-specific hardcoded logic from `server/agentic_engine.py`. Delegate argument normalization to a generic `ArgumentProcessor` class that invokes tool-specific validators defined in `tools/patent_tools.py`.

## 5. Verification Method
- **Circuit Breaker**: Set `INJECT_LLM_FAILURE=true` in `.env` and verify via logs that after a 30s timeout, a single failure immediately trips the breaker again without requiring 3 attempts.
- **Mock Transport**: Verify `server/llm_factory.py` no longer contains patent-specific strings (`"first_examiner"`, `"DF_0"`, etc.) and instead imports/uses a Mock component.
- **Argument Processor**: Check `server/agentic_engine.py` to ensure `_argument_pre_processor` acts only as a generic dispatcher and contains no patent-specific keyword matching. Run the main workflow to ensure fallback tool calls still execute correctly.
