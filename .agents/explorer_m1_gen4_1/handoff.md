# Handoff Report: Generic Mock Strategy & Architecture Robustness

## 1. Observation
- **`server/agentic_engine.py` (Argument Processor)**: The function `_argument_pre_processor` (lines 39-59) contains hardcoded, scripted logic specific to `generate_feature_alignment_matrix` to inject `expert_annotations` from the blackboard.
- **`server/llm_factory.py` (LLM Fallback)**: `_call_local_fallback_template` (lines 296-402) dynamically generates mock tool arguments, but explicitly hardcodes `generate_feature_alignment_matrix` for blackboard data injection. Furthermore, the voting phase (Phase 4) fallback is entirely scripted with a hardcoded enum: `["Grant", "Reject", "Conditional Grant"]`.
- **`tools/patent_tools.py` (Mock Transport)**: `SIMULATED_EPO_DATABASE` is a static dictionary relying on hardcoded keywords ("流", "stream", "辩论") and specific patent IDs. `search_academic_db` returns a completely static string about an IEEE paper.
- **Circuit Breaker (`llm_factory.py`)**: The circuit breaker is tightly coupled with `_call_model`, using hardcoded thresholds (3 failures, 30 seconds) rather than generic configurable parameters.

## 2. Logic Chain
1. **Argument Processor**: To be truly generic, the argument processor must not check `tool_name`. It should instead dynamically map blackboard attributes to missing tool arguments by iterating over the tool's required parameters (if available via schema) or by matching parameter names to blackboard attributes.
2. **Mock Explicit Tags**: Prepending `[MOCK_TRANSPORT]` inside function bodies is brittle. A generic approach requires a `@mock_transport` decorator that automatically intercepts return values and injects the tag (e.g., prepending for strings, or adding a meta-field for JSON/dicts) across any tool.
3. **Dynamic LLM Fallback**: The fallback should infer the expected response structure from the `system_instruction` instead of hardcoding Phase 4. If the prompt specifies a JSON format like `{"vote": "Grant|Reject|Conditional Grant"}`, a regex/parser can extract the keys and pipe-separated options to dynamically generate a valid JSON payload. Tool arguments should be generated purely based on their JSON schema types without hardcoding specific tool names.
4. **Procedural Mock Data (Patent Tools)**: Static dictionaries fail on new test cases. The mock databases must generate procedural data *derived from the input query*. By extracting tokens/keywords from the query, the mock transport can instantiate valid-looking mock patents (e.g., `EP{random}A1`, `Title: Method for {query_tokens}`) on the fly, guaranteeing a successful retrieval simulation for *any* arbitrary input.

## 3. Caveats
- Procedurally generated mock data will not have logical real-world consistency (e.g., patent claims may be nonsensical combinations of query keywords), but it is sufficient for testing architecture pipelines.
- Parsing JSON schemas from system prompts via regex for LLM fallback assumes the prompt includes a clear template (e.g., `{"vote": "..."}`). If the prompt format changes drastically, the generic regex parser might fail to construct valid JSON.

## 4. Conclusion & Concrete Strategy for Gen4 Worker

**Step 1: Implement Generic Argument Processor (`server/agentic_engine.py`)**
- Remove `if tool_name == "generate_feature_alignment_matrix":`.
- Implement a dynamic mapping: check missing arguments against blackboard attributes. If a parameter name (like `expert_annotations`) matches `hasattr(blackboard, "expert_annotations")`, dynamically inject `getattr(blackboard, "expert_annotations")`.

**Step 2: Procedural Mock Transport (`tools/patent_tools.py`)**
- Delete `SIMULATED_EPO_DATABASE`.
- In `search_patent_db`, parse `query` by splitting spaces/punctuation to extract keywords.
- Generate mock patents dynamically where `id` = `EP` + random integer + `A1`, `title` incorporates the keywords, and `features` are derived by chunking the `query`.
- In `search_academic_db`, dynamically embed the query into the return string: `f"[MOCK_TRANSPORT] Found academic paper on '{query}'...".`
- Create a `@mock_transport` Python decorator to automatically inject the `[MOCK_TRANSPORT]` tag into return values, and apply it to mock functions.

**Step 3: Dynamic LLM Fallback (`server/llm_factory.py`)**
- In `_call_local_fallback_template`, remove the hardcoded `generate_feature_alignment_matrix` tool data injection. Rely strictly on generating dummy data based on the tool's JSON schema types (string, boolean, integer).
- For response generation (Phase 4), use regex (e.g., `r"\{.*?\}"`) on `system_instruction` to find JSON templates. Dynamically parse keys and randomly select from `|` separated enums to construct the fallback JSON, instead of hardcoding "Grant"/"Reject".
- Parameterize Circuit Breaker thresholds via environment variables (e.g., `os.getenv("CB_FAILURES", 3)`).

## 5. Verification Method
- **Run the pipeline with an entirely new domain query** (e.g., "Quantum cryptography encryption mechanisms").
- **Check logs**: Verify that `search_patent_db` returns procedurally generated patents containing "Quantum cryptography" instead of failing or returning empty.
- **Trigger fallback**: Set `INJECT_LLM_FAILURE=true` and verify that the LLM fallback dynamically constructs the Phase 4 JSON and arguments without crashing, and that the `[MOCK_TRANSPORT]` tags appear via decorator injection.
- **Inspect `agentic_engine.py`**: Ensure no tool names are hardcoded in `_argument_pre_processor`.
