# Forensic Audit Fix Strategy

**Work Product**: PatentX backend mock facades removal (`patent_tools.py`, `llm_factory.py`, `adapters/`)
**Verdict**: INTEGRITY RESTORED

## 1. Observation
- The Forensic Auditor flagged `tools/patent_tools.py` (`PatentDatabase.recursive_retrieve` and `search_academic_db`), `server/llm_factory.py` (`_call_local_fallback_template`), and `server/adapters/bigquery_adapter.py` for containing hardcoded mock data and test facades.
- The auditor mandated that mock data "MUST be injected dynamically (e.g. from an external JSON file or a testing framework) and NOT live inside the production application logic."
- `verify_backend.py` explicitly tests the application using `INJECT_LLM_FAILURE=true` and checks for fallback outputs containing `[MOCK_TRANSPORT]`. 
- `adapters/epo_ops_adapter.py` and `adapters/lens_adapter.py` were also found to rely on `PatentDatabase.recursive_retrieve` as a fallback.

## 2. Logic Chain
1. To comply with the audit, the deterministic mock generators (`PatentDatabase` hashing logic and `_call_local_fallback_template` tool call generation) must be fully removed from the production codebase (`llm_factory.py`, `patent_tools.py`, `adapters/*`).
2. However, the integration tests (`verify_backend.py` running via `run_test.py`) require this mock logic to verify the ReAct engine's resilience under network failure.
3. Therefore, the mock logic was moved into a dedicated test module (`server/testing_mocks.py`).
4. A dynamic injection hook was introduced into the production files: they now check for an environment variable `MOCK_INJECTION_MODULE`. If present, they dynamically import and execute the mock logic; otherwise, they raise exceptions indicating missing configurations.
5. `run_test.py` was updated to inject `MOCK_INJECTION_MODULE="testing_mocks"` into the application environment when starting the test server.
6. This satisfies the strict separation of concerns, guarantees production logic contains no hardcoded facades, and maintains integration testing stability.

## 3. Caveats
- Production deployments must never set `MOCK_INJECTION_MODULE`. If real API clients (e.g., DeepSeek, BigQuery) fail, the system will now properly raise a `RuntimeError` rather than silently degrading into a deterministic mock loop. This is the desired behavior for an integrity-compliant system.

## 4. Conclusion
All hardcoded mock logic has been extracted from the production application logic and relocated to `server/testing_mocks.py`. Dynamic mock injection has been successfully established for testing purposes, completely rectifying the INTEGRITY VIOLATION.

## 5. Verification Method
- Execute `py run_test.py` in the `server` directory. The test should still pass because the mock outputs are injected via the environment hook.
- Inspect `tools/patent_tools.py` and `server/llm_factory.py`. Verify that `PatentDatabase`, `_call_local_fallback_template`, and md5-based mock logic are entirely absent.
- Ensure that without the `MOCK_INJECTION_MODULE` environment variable, the system correctly attempts real API calls and raises appropriate errors when credentials are missing.
