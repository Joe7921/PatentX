# Handoff Report - Gen6 Iteration Failure Remediation Strategy

## 1. Observation
- `server/llm_factory.py` line 359: `val_type = v.get("type", "string")`. If `v` is `None` or not a dict, `AttributeError` is raised.
- `server/adapters/base_adapter.py` line 28: `desensitized_text.replace(kw, "[SENSITIVE_ENTITY]")`. If the input `text` is `None`, this causes an `AttributeError`.
- `server/llm_factory.py` in `_call_local_fallback_template`: The tool selection and argument generation rely entirely on `hashlib.md5(seed_str.encode())` to pseudo-randomly pick a tool and insert values like `mock_k_123`. The Auditor correctly identified this as a facade because it ignores the input semantics.
- `tools/patent_tools.py` in `recursive_retrieve`: Fake patents and claims are dynamically formatted (e.g. `pid = f"EP{...}"`) on the fly based on the input text length and hash seed, rather than retrieving from a data source. This is a generative facade rather than a mock retrieval.

## 2. Logic Chain
1. **Fixing AttributeErrors**: We must implement basic null-safety. In `llm_factory.py`, check `if isinstance(v, dict)` before extracting properties. In `base_adapter.py`, add `if not text: return ""` to prevent `.replace()` from acting on `NoneType`.
2. **Remediating `_call_local_fallback_template` (Facade removal)**: The requirement for a "Mock fallback" allows returning deterministic offline data, but the logic choosing that data must be genuine. We must replace the MD5 random selection with a keyword-based intent router. The router should scan `last_user_msg` for tool names or parameter descriptions to decide which tool to call, and extract substrings directly from the prompt as arguments.
3. **Remediating `recursive_retrieve` (Facade removal)**: To transform this from a generative facade to a real mock retriever, we must define a small, static in-memory list of mock patents within the function (or module). The function should then iterate over this static list, calculate an overlap score between `claim_text` and the patent texts (e.g., using set intersection), and return the highest-scoring static records. This satisfies the "real logic" requirement.

## 3. Caveats
- The new fallback and retrieval logic will be primitive (keyword overlap) and cannot match an LLM's semantic depth, but it is deterministic, verifiable logic rather than random spoofing.
- The size of the static mock patent list should be kept small to avoid bloating `patent_tools.py` but large enough to demonstrate retrieval filtering.

## 4. Conclusion
The remediation strategy is as follows:
- **Step 1**: In `server/llm_factory.py`, update the `props.items()` loop: `val_type = v.get("type", "string") if isinstance(v, dict) else "string"`.
- **Step 2**: In `server/adapters/base_adapter.py`, update `filter_pii`: `if not text: return str(text)`.
- **Step 3**: In `server/llm_factory.py`, rewrite `_call_local_fallback_template` to use simple keyword matching (e.g., checking if tool names exist in `last_user_msg`) instead of MD5 hashes.
- **Step 4**: In `tools/patent_tools.py`, rewrite `recursive_retrieve` to define a static array of mock patents and implement a genuine loop to score and sort these mock patents against the input `claim_text`.

## 5. Verification Method
- Execute the backend test suite (e.g. `python server/run_test.py` or project test script) to ensure the AttributeErrors are resolved.
- Invoke `recursive_retrieve` with distinct queries to verify it returns records from the static subset based on genuine string overlap rather than randomly generated `EP` strings.
- Pass a `None` query to `filter_pii` and confirm it gracefully returns `None` or `""`.
