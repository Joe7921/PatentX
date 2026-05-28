# Original User Request

## 2026-05-27T02:07:58Z

Implement architecture robustness features (Circuit Breaker, Argument Processor, Mocking explicit tags) into the PatentX backend based on the agreed implementation plan.

Working directory: d:\Antigravity projects\PatentX
Integrity mode: development

## Reference Material
- Implementation Plan: `C:\Users\zhouh\.gemini\antigravity\brain\60536a7a-e3a9-4266-ae31-1c353c5978d0\implementation_plan.md`

## Requirements

### R1. Implement Circuit Breaker
Modify `server/llm_factory.py` to add a global failure counter and circuit breaker timeout. If failures exceed a threshold for a specific model, short-circuit and fallback immediately. Log heavily using the exact prefix `[CIRCUIT_BREAKER]`.

### R2. Label Mock Transport Explicitly
Modify `server/llm_factory.py` (specifically `_call_local_fallback_template`) and `tools/patent_tools.py` (`search_academic_db`) to prominently output `[MOCK_TRANSPORT]` in their return values or logs whenever they use mock fallback data.

### R3. Centralize Argument Processor
Modify `server/agentic_engine.py` to extract the tool argument correction/padding logic (specifically for `generate_feature_alignment_matrix`) into a separate `_argument_pre_processor` function. Log interventions with the prefix `[ARGUMENT_PROCESSOR]`.

### R4. Language and Safety Rules
The teamwork agents MUST follow the global user rules: use Simplified Chinese for all replies/comments, do not modify UI/CSS without permission, and never use PowerShell to modify file contents (must use MCP file tools to preserve UTF-8 without BOM).

## Acceptance Criteria

### Verification Checks
- [ ] Integration test suite `python server/run_test.py` passes with 100% success rate.
- [ ] Manual inspection of code confirms `[CIRCUIT_BREAKER]` and `[MOCK_TRANSPORT]` and `[ARGUMENT_PROCESSOR]` tags are correctly implemented.
- [ ] `agentic_engine.py` is refactored properly without breaking the multi-agent reaction loop.

When you have achieved the Acceptance Criteria and completed the mission, declare victory and send me a message confirming completion.
