# Handoff Report: Gen6 Iteration Remediation Strategy

## 1. Observation
- **`llm_factory.py`**: In `server/llm_factory.py:359`, the code `val_type = v.get("type", "string")` throws an `AttributeError` if `v` is `None`. This occurs when a parameter definition in the tool schema lacks properties or evaluates to `None`.
- **`base_adapter.py`**: In `server/adapters/base_adapter.py:20`, `filter_pii(self, text: str)` calls `text.replace` (implicitly via `desensitized_text.replace`). If the `text` (or `query`) is passed as `None`, an `AttributeError: 'NoneType' object has no attribute 'replace'` is raised.
- **Integrity Violation**: In `server/llm_factory.py:327-390` (`_call_local_fallback_template`) and `tools/patent_tools.py:23-64` (`recursive_retrieve`), the code utilizes `hashlib.md5` to dynamically generate randomized strings (`mock_...` and procedural gibberish like `Dynamic system for...`). The Forensic Auditor correctly identified this as a "dummy/facade" because it lacks genuine programmatic logic or realistic fallback data.

## 2. Logic Chain
1. **AttributeError in `llm_factory.py`**: A schema dictionary `v` might be `None` or not a dictionary. Defensively checking its type will prevent `v.get()` from faulting.
2. **AttributeError in `base_adapter.py`**: Defensive programming requires `filter_pii` to handle a `None` input cleanly by returning an empty string or `None` immediately.
3. **Facade Violation**: The definition of a "Mock fallback" for this milestone implies a functional simulation rather than purely random data generation. 
   - For `patent_tools.py`, instead of hashing the query to build random words, the system should hold a local static dictionary of 5-10 realistic pre-authored patent fixtures (JSON/Dictionary). It can then perform a genuine, albeit simple, keyword matching (e.g., set intersection) against the query to return relevant static fixtures.
   - For `llm_factory.py`, instead of generating parameters using MD5 seeding, the local fallback should apply a genuine heuristic (e.g., regex extraction of quoted strings or simple NLP keyword extraction from the prompt) to populate tool arguments. If it cannot reliably extract, it should return a predictable, deterministic default rather than a randomized `mock_` hash.

## 3. Caveats
- Implementing a realistic mock dataset will slightly increase the file size of `patent_tools.py` due to the embedded fixtures.
- The regex/heuristic parsing in `llm_factory.py` will not perfectly replicate an LLM's comprehension but it will serve as a mathematically legitimate deterministic parser, satisfying the "no facade" constraint.

## 4. Conclusion
We must implement a **Deterministic Heuristic & Fixture-based Strategy**:
1. **Fix `llm_factory.py` AttributeError**: Update line 359 to `val_type = v.get("type", "string") if isinstance(v, dict) else "string"`.
2. **Fix `base_adapter.py` AttributeError**: Add `if not text: return ""` at the beginning of `filter_pii`.
3. **Resolve `patent_tools.py` Facade**: Replace the `hashlib.md5` generation in `recursive_retrieve` with a hardcoded list of ~3 realistic mock patent dictionaries. Implement a simple loop to return those fixtures based on whether the input `claim_text` shares words with the fixture.
4. **Resolve `llm_factory.py` Facade**: Remove `hashlib.md5` parameter generation in `_call_local_fallback_template`. Instead, use basic python string methods (e.g., extracting the longest word for `query`, returning a deterministic structured JSON template based on the available `tools` schema).

## 5. Verification Method
- **AttributeError Tests**: Manually invoke `filter_pii(None)` and `_call_local_fallback_template` with a mock schema where a property is `None`. They should no longer throw errors.
- **Integrity Validation**: Run the exact test suite or Forensic Auditor script that flagged the integrity violation. It should pass, as the codebase will no longer contain `hashlib.md5` random number generation disguised as logic.
