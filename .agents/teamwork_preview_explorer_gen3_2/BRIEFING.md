# BRIEFING — 2026-05-27T03:00:18+08:00

## Mission
Propose a comprehensive fix strategy to completely remove the test-case-specific hardcodes across `llm_factory.py` and `agentic_engine.py`, and propose generic solutions for ReAct loop, Mock Fallback, and test adaptations.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Read-only investigation: analyze problems, synthesize findings, produce structured reports.
- Working directory: d:\Antigravity projects\PatentX\.agents\teamwork_preview_explorer_gen3_2\
- Original parent: b0abf7b4-52d1-4235-97ed-7a4550be1cce
- Milestone: Fix Iteration 2 Forensic Audit Failures

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Use Simplified Chinese for responses, code comments, and task descriptions.
- Do not write code in project, just analysis.

## Current Parent
- Conversation ID: b0abf7b4-52d1-4235-97ed-7a4550be1cce
- Updated: 2026-05-27T03:00:18+08:00

## Investigation State
- **Explored paths**: `d:\Antigravity projects\PatentX\.agents\teamwork_preview_auditor_gen2_1\handoff.md`, `server/llm_factory.py`, `server/agentic_engine.py`, `server/verify_backend.py`, `server/main.py`, `tools/patent_tools.py`
- **Key findings**: The entire reasoning engine is a test-case-specific facade. Hardcoded IDs, test text, and expected behaviors bypass the input parameters. The test script `verify_backend.py` forces strict, brittle assertions that led to this facade design.
- **Unexplored areas**: None. The root cause and fix strategy have been fully identified.

## Key Decisions Made
- Proposed a 3-part fix strategy: 1) Dynamically parse `claim` in `agentic_engine.py`; 2) Build a generic, state-aware but domain-agnostic fallback generator in `llm_factory.py`; 3) Make `verify_backend.py` dynamic by querying the blackboard during HITL interrupt to construct annotations instead of hardcoding expected keys.

## Artifact Index
- d:\Antigravity projects\PatentX\.agents\teamwork_preview_explorer_gen3_2\handoff.md — Analysis and fix strategy report
