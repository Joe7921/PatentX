# PatentX Architecture Robustness Analysis & Generic Mock Strategy

## 1. Observation
- **`server/llm_factory.py`**: The `_call_local_fallback_template` method contains hardcoded, scripted logic for specific tools and phases. For example, it explicitly checks `if func_name == "generate_feature_alignment_matrix" and self.blackboard:` to inject mock data, and uses `if current_phase == 4:` to simulate the voting JSON format (`["Grant", "Reject", ...]`).
- **`tools/patent_tools.py`**: The mock transports are rigidly scripted. `search_patent_db` relies on a static `SIMULATED_EPO_DATABASE` dictionary containing two hardcoded patents (EP3812049A1, EP4012055A2) and a fixed keyword mapping (e.g., "stream", "debate"). `search_academic_db` returns a static string (`"IEEE Transactions..."`) regardless of the dynamic query.
- **`server/agentic_engine.py`**: The `_argument_pre_processor` uses hardcoded tool names to inject dependencies. It specifically checks `if tool_name == "generate_feature_alignment_matrix":` to inject `expert_annotations` from the blackboard into the tool arguments.

## 2. Logic Chain
- The current implementation is a "test-case specific facade". If a new patent claim (e.g., related to quantum computing) is inputted, or if new tools are added to the Agent, the fallback and mock systems will either fail or return completely irrelevant hardcoded data. 
- To make the **Circuit Breaker / Fallback** truly generic, `llm_factory.py` must stop matching specific tool names. Instead, it must dynamically read the provided `tools` JSON Schema, iterate through `parameters.properties`, and generate mock data strictly based on the parameter's `type` and `enum` fields.
- For generating generic JSON responses (like the vote decision when no tools are available), the fallback should extract expected formats by parsing the `system_instruction` using regular expressions (e.g., matching `{...}` JSON examples) rather than relying on a hardcoded `current_phase` integer.
- To make **Mock Transports** generic, `patent_tools.py` must discard the static dictionary. It should instantiate mock patent records on-the-fly by parsing the input `query` or `claim_text` into chunks, appending mock suffixes, and constructing synthetic `features`. This guarantees contextually relevant mock data for *any* domain.
- To make the **Argument Processor** generic, `agentic_engine.py` must adopt a *Dependency Injection* (DI) pattern. Instead of checking `if tool_name == ...`, it should hold a registry of available contextual objects (e.g., `{"expert_annotations": blackboard.expert_annotations}`). It can then check if a tool's schema or signature requires a parameter matching a registry key and inject it automatically.

## 3. Caveats
- Using regex to extract expected JSON formats from the `system_instruction` is heuristic and may fail if the LLM prompt's formatting changes significantly.
- Dynamic generation of mock patents is naive and will not possess deep semantic logic, which is acceptable for pipeline testing but shouldn't be mistaken for actual semantic retrieval.
- Dependency Injection in the argument processor relies on parameter naming consistency. If a tool requests `expert_notes` instead of `expert_annotations`, the generic processor won't match it unless an alias system is implemented.

## 4. Conclusion
A concrete, step-by-step strategy for the Gen4 Worker to implement generic robustness features:
1. **Schema-based Mock Generator (`llm_factory.py`)**: Replace hardcoded tool checks with dynamic JSON Schema traversal. Map types to generic generators (`string` -> `"mock_{key}"`, `enum` -> `random.choice(enum_list)`). Use regex to extract JSON templates from the prompt for tool-less responses.
2. **Dynamic Data Synthesis (`patent_tools.py`)**: Replace `SIMULATED_EPO_DATABASE` with a dynamic generator that builds fake JSON patent objects based on keywords extracted from the user's input claim. Prepend all outputs with the explicit `[MOCK_TRANSPORT]` tag.
3. **Dependency Injection Registry (`agentic_engine.py`)**: Remove tool-name checks in `_argument_pre_processor`. Create a context dictionary mapping strings to blackboard attributes, and loop through the tool's expected arguments to dynamically inject matching keys.

## 5. Verification Method
1. Disconnect the API Key or inject a failure (via `INJECT_LLM_FAILURE=true`) to force the Circuit Breaker.
2. Submit a completely novel patent claim outside the hardcoded scope (e.g., "A quantum entanglement router with photon buffers").
3. Inspect the execution logs:
   - **Database**: Ensure `search_patent_db` dynamically returns patents featuring "quantum" and "photon", not EP3812049A1.
   - **Arguments**: Ensure `expert_annotations` is seamlessly injected into tools requiring it, without `KeyError`.
   - **Fallback**: Ensure the local template successfully parses tool schemas and generates arguments like `{"domestic_feature": "mock_domestic_feature"}` without crashing.
