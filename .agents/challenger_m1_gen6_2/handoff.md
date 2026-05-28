# 5-Component Handoff Report

## 1. Observation
I created a stress-test harness script `stress_test_edge.py` to test the new generic Mock fallback mechanism in `llm_factory.py` and the `retrieve` logic in `bigquery_adapter.py` (which uses `adapters/base_adapter.py`).

1. When calling `BigQueryAdapter.retrieve(query=None)` or `retrieve(query={"some": "object"})`, the execution crashes in the `filter_pii` method of the base adapter with:
```
BigQueryAdapter failed on None query: 'NoneType' object has no attribute 'replace'
BigQueryAdapter failed on dict query: 'dict' object has no attribute 'replace'
```
This is because `filter_pii(text: str)` immediately calls `text.replace(kw, "[SENSITIVE_ENTITY]")` without checking if `text` is indeed a string.

2. When triggering the LLM Generic Mock Fallback mechanism (by simulating API failure) and passing a tool schema containing an explicitly `null` property (e.g. `{"null_prop": null}` instead of a dictionary definition), the execution crashes with:
```
Traceback (most recent call last):
  File "D:\Antigravity projects\PatentX\server\stress_test_edge_llm.py", line 39, in test_llm_factory_edge_cases
    res = await client.chat(messages, tools=tools)
  File "D:\Antigravity projects\PatentX\server\llm_factory.py", line 201, in chat
    return await self._call_local_fallback_template(messages, tools)
  File "D:\Antigravity projects\PatentX\server\llm_factory.py", line 360, in _call_local_fallback_template
    val_type = v.get("type", "string")
AttributeError: 'NoneType' object has no attribute 'get'
```
This happens because `_call_local_fallback_template` assumes `v` is always a `dict` inside `for k, v in props.items():`.

## 2. Logic Chain
- The fixes in `bigquery_adapter.py` rely on `filter_pii` and `truncate_by_budget`, both assuming the `query` input is strictly a valid string. If an adversarial input (e.g., `None` or a dictionary from a malformed tool call or explicit JSON null) is passed, the adapter's `retrieve` method will throw an unhandled exception before reaching the safe fallback mechanism.
- The new `llm_factory.py` generic Mock fallback randomly picks tools and generates mock arguments by parsing the `properties` dict. It loops through `props.items()` as `(k, v)`. In Python, an explicitly null property in JSON becomes `None`. Attempting `v.get("type", ...)` directly on `None` causes an `AttributeError`, killing the entire Mock fallback process and breaking the intended容灾降级 (disaster recovery) mechanism.

## 3. Caveats
- I did not test all permutations of missing schema fields (e.g. missing `properties` entirely, which is handled fine due to `.get("properties") or {}`). The critical failure is specifically when a property key is present but its value is `None`/`null`.
- The `bigquery_adapter.py` test triggered the error in `base_adapter.py`, which is shared by other adapters. This means the vulnerability also impacts `epo_ops_adapter.py` and `lens_adapter.py` if they call `filter_pii`.

## 4. Conclusion
The current implementations of the Mock Fallback and Adapter systems are brittle when handling edge-case inputs (`None`, explicit `null` schema parameters, or non-string queries). 
- **Critical Risk:** A malformed tool call or a schema containing `null` properties will completely break the Mock fallback in `llm_factory.py` with an `AttributeError`.
- **High Risk:** Providing `None` or a dictionary to the database adapters' `retrieve` method crashes the system inside `filter_pii` instead of being handled gracefully.

## 5. Verification Method
To independently verify:
1. Run `py "D:\Antigravity projects\PatentX\server\stress_test_edge_llm.py"` from my workspace folder. You will observe the `AttributeError: 'NoneType' object has no attribute 'get'` stack trace.
2. The script can be found in `D:\Antigravity projects\PatentX\server\stress_test_edge_llm.py` and `stress_test_edge.py`.
3. Inspect `D:\Antigravity projects\PatentX\server\llm_factory.py` line 360 and `D:\Antigravity projects\PatentX\server\adapters\base_adapter.py` line 26.
