# Fix Strategy for Integrity Violations

## 1. Observation
- `server/llm_factory.py`: The `_call_local_fallback_template` method (lines 292-646) acts as a facade, emitting 350+ lines of hardcoded agent conversation turns. These turns perfectly simulate a patent evaluation process using specific test data (e.g., `EP4012055A2`, `EP3812049A1`).
- `server/agentic_engine.py`: The `_VOTE_TEMPLATES` dictionary (lines 120-140) contains hardcoded paragraphs filled with specific business domain texts (e.g., "核心技术特征A（SSE流式传输）与EP3812049A1的状态流式传输特征高度重合").
- `server/agentic_engine.py`: The `_argument_pre_processor` (lines 54-113) forces tool execution to pass by silently injecting fabricated arguments (e.g., `"DF_0"`, `"Mocked prior art feature text"`) whenever the LLM fails to provide them.
- `tools/patent_tools.py`: Functions like `search_academic_db` (lines 100-106) return fake domain facts (e.g., "IEEE Transactions on AI, Vol. 12 (2025)") instead of standardized mock structures.

## 2. Logic Chain
- **Integrity Compliance**: The current implementation circumvents actual LLM reasoning and tool validation by hardcoding "perfect" fallback paths. To satisfy the auditor, the system must not fake successful domain logic when the actual logic fails.
- **Circuit Breaker (R1)**: A valid Circuit Breaker must gracefully halt operations or return an explicit generic error (e.g., "Service Unavailable") when the failure threshold is met, rather than substituting a 350-line pre-written script (`_call_local_fallback_template`) that deceptively completes the workflow.
- **Mock Transport (R2)**: A valid Mock Transport for testing should not be hardcoded into the production source files. Instead, it should dynamically read expected outputs from external test configurations (e.g., via `os.getenv("MOCK_RESPONSE_FILE")`) or return structured dummy payloads (`{"content": "MOCKED_RESPONSE", "tool_calls": []}`). For mock tools (`patent_tools.py`), they should use explicit structural mock tags instead of faking specific literature.
- **Argument Processor (R3)**: A valid Argument Processor must perform real validation (type checking, defaulting). If required arguments are missing, it must reject the call and return a clear error payload back to the LLM (e.g., `{"error": "Missing parameter: prior_art_feature"}`). This allows the ReAct loop to genuinely retry and self-correct, instead of silently mutating the arguments with mock strings to force the pipeline to succeed.

## 3. Caveats
- Removing these facades will likely break existing integration tests that currently rely on the hardcoded `EP4012055A2` text being emitted during offline testing. Test suites will need to be updated to either use a real LLM, or the new file-based Mock Transport.
- The UI or orchestration layer will need to handle explicit Circuit Breaker exceptions (e.g., `CircuitBreakerError`) since the system will no longer pretend to succeed when offline.

## 4. Conclusion
**Verdict**: The facades must be completely removed and replaced with standard architectural patterns. 

**Fix Strategy Actions**:
1. **Remove Hardcoded Domain Text**: Delete `_call_local_fallback_template` (`llm_factory.py`) and `_VOTE_TEMPLATES` (`agentic_engine.py`) entirely. Remove fake literature strings in `patent_tools.py`.
2. **Implement Authentic Circuit Breaker (R1)**: Update `llm_factory.py` so that when the breaker triggers, it raises a `CircuitBreakerError` or returns a generic system failure message, terminating the process authentically.
3. **Implement Authentic Mock Transport (R2)**: Create a proper `MockTransport` mode triggered by an environment variable. When active, it should route queries to a parser that reads from a test-specific JSON/YAML file, preventing test data from leaking into the source code.
4. **Implement Authentic Argument Processor (R3)**: Refactor `_argument_pre_processor` to validate required parameters. Replace the silent injection of "Mocked prior art feature text" with an explicit error return that prompts the LLM to retry.

## 5. Verification Method
1. Inspect `server/llm_factory.py` and `server/agentic_engine.py` to confirm `_call_local_fallback_template` and `_VOTE_TEMPLATES` no longer exist.
2. Disconnect the network or provide an invalid `DEEPSEEK_API_KEY`. Verify that the system halts with a `CircuitBreakerError` (or a generic system message) and DOES NOT generate patent-specific texts like "EP4012055A2".
3. Intentionally provide a malformed tool call to `generate_feature_alignment_matrix` and verify that the Argument Processor returns an error to the LLM rather than injecting `"DF_0"`.
