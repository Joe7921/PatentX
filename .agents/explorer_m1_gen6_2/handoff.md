# Handoff Report

## 1. Observation
- In `server/adapters/bigquery_adapter.py`, lines 63-66 hardcode `focus_keywords` to intercept `["流", "stream", "中断", "pause", "恢复", "resume"]`.
- In `server/adapters/bigquery_adapter.py`, lines 138-147 contain a hardcoded `if "stream" in claim_lower ...` block that injects fake `features` such as `"SSE流式传输"`, `"HITL中断与挂起"`, and `"法官协调代理"`.
- In `server/llm_factory.py`, line 354 is: `props = tool_schema.get("function", {}).get("parameters", {}).get("properties")`. If the `parameters` key is explicitly `null` (None in Python), `.get("parameters", {})` returns `None`. Calling `.get("properties")` on `None` raises an `AttributeError`. The `props.items()` loop on line 358 ultimately triggers the dictionary extraction error.

## 2. Logic Chain
- The `bigquery_adapter.py` is violating its role by mocking domain-specific agent behaviors and intercepting stream requests with hardcoded text. By replacing the hardcoded keyword extraction with generic regex tokenization from the user query, and by replacing the mocked features with a generic sentence-extractor from `claim_text`, the adapter becomes domain-agnostic and returns real data.
- The `llm_factory.py` crash is caused by assuming that missing keys return `{}` via `.get(key, {})`, but ignoring that explicitly `null` JSON values evaluate to `None`, which `.get()` will return as-is. We must use `or {}` to ensure that `None` evaluations correctly fallback to an empty dictionary before accessing further keys or calling `.items()`.

## 3. Caveats
- Extracting features via regex sentence splitting from `claim_text` in the BigQuery adapter is basic. If the `claim_text` lacks punctuation, the entire text might be returned as a single feature. This is still better than hardcoded mock features, but might affect downstream tasks that expect highly granular points.
- The fix in `llm_factory.py` assumes that if `parameters` or `properties` are `null`, the tool takes no arguments.

## 4. Conclusion
**Fix Strategy for `server/adapters/bigquery_adapter.py`:**
1. Replace `focus_keywords` generation (lines 63-66) with a regex that extracts generic words from `query.lower()` (e.g., `re.findall(r'\b[A-Za-z0-9]{4,}\b', query.lower())`).
2. Remove the fallback regex `agent|stream|pause|resume` on line 97 and use generic tech words like `patent|system|method`.
3. Replace the `if "stream" in claim_lower...` block (lines 137-147) with a generic feature extractor that splits `claim_text` by sentence delimiters (`.` or `;`) and assigns the first few sentences as the `features` list.

**Fix Strategy for `server/llm_factory.py`:**
1. Rewrite lines 354-356 to safely fallback explicitly `None` values using Python's `or` operator:
   ```python
   func_obj = tool_schema.get("function") or {}
   params_obj = func_obj.get("parameters") or {}
   props = params_obj.get("properties") or {}
   ```
2. Remove the previous `if props is None:` block as `props = ... or {}` inherently handles the `None` check, ensuring `props.items()` safely executes.

## 5. Verification Method
- For `bigquery_adapter.py`: Run `server/run_test.py` or equivalent test querying BigQuery, and print the retrieved features. Ensure no "SSE流式传输" appears and verify sentences from the text are used instead.
- For `llm_factory.py`: Create a dummy test file that passes `{"function": {"name": "test", "parameters": null}}` as a tool schema to the fallback template and assert that it doesn't crash with `AttributeError`.
