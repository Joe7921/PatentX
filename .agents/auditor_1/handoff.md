## Forensic Audit Report

**Work Product**: `tools/patent_tools.py`, `server/llm_factory.py`, and `server/agentic_engine.py`
**Profile**: General Project
**Verdict**: CLEAN

### Phase Results
- [Hardcoded Output Detection]: PASS — Grep searches for "EP3812049A1", "流", and "stream" across the target files returned no results. The mock patent generator dynamically constructs PIDs (`f"EP{random.randint(1000000, 9999999)}A1"`) and extracts words from the claim dynamically using regex `\b\w+\b`.
- [Facade Implementation Detection]: PASS — The feature alignment in `patent_tools.py` uses a real intersection-over-union (IoU) Jaccard calculation logic with a 0.3 similarity threshold to natively determine `Fully_Disclosed`.
- [Fallback Robustness]: PASS — The mock LLM fallback in `llm_factory.py` dynamically infers parameter types from any tool's JSON schema and dynamically generates random integers, booleans, and string values (e.g., `mock_args[k] = f"mock_{k}_{random.randint(100, 999)}"`), successfully avoiding brittle hardcoded parameter sets.
- [Dynamic Parsing]: PASS — `agentic_engine.py` dynamically extracts domestic features by splitting the claim text using common punctuation `re.split(r'[,;，；。且及与]+', claim)`.

### Evidence
- `patent_tools.py`: `words = re.findall(r'\b\w+\b', claim_text)` (Line 19)
- `llm_factory.py`: `mock_args[k] = f"mock_{k}_{random.randint(100, 999)}"` (Line 349)
- `agentic_engine.py`: `raw_features = re.split(r'[,;，；。且及与]+', claim)` (Line 404)

---

1. **Observation** — 
   - I searched the codebase using `grep` for the flagged substrings ("EP3812049A1", "流", "stream"). No test-specific artifacts were found in the codebase.
   - Code review of `tools/patent_tools.py`, `server/llm_factory.py`, and `server/agentic_engine.py` confirms that the backend utilizes generic Python tools (regex processing, token overlap calculations) to simulate the database and fallback logic.

2. **Logic Chain** — 
   - Because the system uses regex string splitting for the claims rather than matching specific test inputs, it can process any incoming data seamlessly.
   - Because `LLMFactory` dynamically iterates over tool schemas to construct its offline `mock_args`, it avoids being tied to a specific tool's signature.
   - Therefore, the implementation meets the requirements for Demo Mode without relying on facades.

3. **Caveats** — 
   - The system is still heavily dependent on pseudo-random generation for fallback responses, which ensures execution completeness but does not test the actual quality of LLM outputs.

4. **Conclusion** — 
   - The developer successfully removed the hardcoded test facades and replaced them with robust, generalized logic capable of passing the integrity checks. The verdict is CLEAN.

5. **Verification Method** — 
   - Execute `grep -rE "(EP3812049|stream|流)" tools/ server/` to independently verify the absence of hardcoded values. Review `server/llm_factory.py` offline fallback mechanism.
