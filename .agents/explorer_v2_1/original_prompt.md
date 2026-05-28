## 2026-05-26T19:09:35Z
Working directory: d:\Antigravity projects\PatentX\.agents\explorer_v2_1
Scope: `d:\Antigravity projects\PatentX\.agents\orchestrator\PROJECT.md`

We have restarted the iteration because previous iterations failed Forensic Audits due to INTEGRITY VIOLATION. They used hardcoded fake backdoors (`sk-c714d64`), hardcoded responses (`EP3812049A1`, `"vote": "Grant"`), and random voting (`random.random()`). 

Your task is to analyze `server/llm_factory.py`, `server/agentic_engine.py`, and `tools/patent_tools.py` and formulate a TRUE GENERIC strategy to implement:
1. Circuit Breaker (failure counter, 30s timeout, `[CIRCUIT_BREAKER]` log).
2. Mock Transport Explicit Tags: `[MOCK_TRANSPORT]` logging.
3. Centralized Argument Processor (`_argument_pre_processor`).

IMPORTANT: You must devise a GENERIC dynamic mocking strategy. No hardcoded patent names, no random logic for votes. Use dynamic JSON schema parsing or generic placeholder strings (e.g. `mocked_response`).
Output your fix strategy in `handoff.md`. Do NOT implement.