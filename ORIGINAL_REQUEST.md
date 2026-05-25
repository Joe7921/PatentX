# Original User Request

## Initial Request — 2026-05-25T16:06:51+08:00

Refactor the PatentX project to implement a **streaming Agentic reasoning visualization system**. Replace the current hardcoded 5-step SSE pipeline with a half-autonomous Agentic workflow modeled after the real **EPO Examining Division** (3-examiner collegiate system with ReAct loops), and replace the simple ThinkingIndicator spinner with a rich **vertical timeline UI** featuring Gemini-style animations for every reasoning step. The purpose is a **production-quality demo** that showcases multi-agent collaboration to potential investors and partners.

Working directory: `d:\Antigravity projects\PatentX`
Integrity mode: development

**Important context about the existing codebase:**
- Backend: Python FastAPI server at `server/main.py`, with `blackboard.py` state management, `llm_factory.py` for LLM instantiation, and Agent YAML configs in `app/agents/_custom/`
- Frontend: Vite + React + TypeScript + Zustand + Framer Motion + TailwindCSS at `frontend/`
- Currently uses SSE (Server-Sent Events) with 4 event types (`node_start`, `node_complete`, `hitl_interrupt`, `completed`) to stream a hardcoded pipeline
- The frontend has an `AuroraBackground` canvas component with multiply-blend aurora particles on a light `slate-50` base — all new UI must visually harmonize with this existing aesthetic
- **Windows PowerShell environment** — all terminal commands must use PowerShell syntax (`;` not `&&`, no `export`, no `rm -rf`)
- **CRITICAL file editing rule**: Never use PowerShell `Set-Content`, `Out-File`, or `Add-Content` to modify source code files (BOM injection breaks Node.js toolchain). Always use the provided file-editing tools.
- All code comments and UI text must be in **Simplified Chinese (简体中文)**

## Requirements

### R1. Agentic Backend with EPO 3-Examiner Collegiate System

The backend SSE event stream must be restructured around a **4-phase half-autonomous Agentic workflow** that models the real EPO Examining Division:

**Phases**: (1) Document Analysis & Search — only the First Examiner works alone, (2) Internal Review Meeting — all 3 examiners convene for the first time, (3) Oral Proceedings — examiner group vs. applicant representative adversarial debate chaired by the Chairman, (4) Final Decision — collegiate vote.

**Agents**: First Examiner (primary searcher/analyzer), Second Examiner (cross-reviewer), Chairman (process controller, chairs meetings, leads vote), Applicant Representative (defense counsel, only appears in phase 3), Legal Examiner (dynamically summoned by Chairman when pure legal disputes arise — the 4th person).

**ReAct loops**: Within each phase, the lead agent operates in Think→Act→Observe cycles, autonomously deciding what to do next. Each cycle step is pushed to the frontend as a separate SSE event. Maximum 8 ReAct rounds per agent per phase.

**"1-person backbone + 3-person collective decision" mode**: Phase 1 is the First Examiner working alone (like EPO's single-line contact). The 3-person (or 4-person) collective vote only happens at the final decision point.

**Dynamic Agent summoning**: The Chairman may autonomously decide to summon the Legal Examiner during the Internal Review Meeting when pure legal (not technical) disputes are detected.

**HITL (Human-in-the-Loop)**: After the Internal Review Meeting, if the Chairman determines major divergence exists, the system pauses for human expert intervention before proceeding to Oral Proceedings.

### R2. Frontend Vertical Timeline with Per-Node Animation

Replace the existing `ThinkingIndicator` spinner with a **dual-layer vertical timeline component** that visualizes the entire Agentic reasoning process:

**Macro layer**: 4 phase nodes arranged vertically. Active phase has a glowing border animation, completed phases show a checkmark and collapse, pending phases are grayed out.

**Micro layer**: Inside each expanded phase node, individual ReAct steps (Think/Act/Observe) appear as cards that slide in from below with opacity fade-in. Think cards have italic text and a subtle pulse background (like inner monologue). Act cards use the agent's color theme. Observe cards show data summaries.

**Agent identity**: Each agent has a distinct color theme and icon. The agent's avatar and name are displayed on each card.

**Typewriter effect**: All agent text content renders character-by-character using `requestAnimationFrame`, with a blinking cursor. The backend sends complete text in one SSE event; the frontend drives the animation.

**Timeline connectors**: Lines between phase nodes animate from gray to blue as phases complete (flowing fill effect).

### R3. Collegiate Voting Visualization

In the Final Decision phase, implement a **card-flip voting panel**:
- Each examiner (3 or 4 if Legal Examiner was summoned) has a vote card showing "?" initially
- Cards flip one at a time with a 3D Y-axis CSS rotation animation (1.5s interval between cards)
- After flipping, each card reveals: the vote (Grant / Reject / Conditional Grant), the agent's color badge, and a brief reasoning excerpt
- After all cards are revealed, the final majority decision appears at the bottom with a golden glow animation

### R4. HITL Inline Integration

The HITL interruption must be embedded **within the timeline** as a special amber-colored phase node — not as a separate page. When activated, the node expands to show the expert input panel (text area + approve/revise buttons). After submission, the node collapses with a checkmark and the timeline continues flowing downward. The existing `AgenticPauseCard` logic should be reused inside this inline panel.

### R5. Dashboard Integration

After the entire Agentic flow completes, the view transitions to the existing `DiagnosticDashboard`. Add a collapsible "View Reasoning Process" button at the top of the Dashboard that, when clicked, expands a read-only version of the timeline (all phases completed, no typewriter animations, all text fully rendered).

## Acceptance Criteria

### Backend Agentic Flow
- [ ] Starting an analysis produces SSE events in the sequence: `phase_start` → (`agent_think` → `agent_act` → `agent_observe`)+ → `phase_complete`, repeated for each of the 4 phases
- [ ] Phase 1 SSE events only reference `first_examiner` as the acting agent; Phase 2 events reference `second_examiner` and `chairman`; Phase 3 events reference all four main agents
- [ ] A `vote_cast` SSE event is emitted for each voting examiner in Phase 4, containing a `vote` field with one of three values and a `reasoning` field
- [ ] When legal disputes are detected, an `agent_summon` SSE event is emitted before the Legal Examiner's actions, and the Legal Examiner participates in the final vote (4 `vote_cast` events instead of 3)

### Frontend Timeline Visualization
- [ ] The vertical timeline renders exactly 4 phase nodes; the currently active phase is visually distinct (animated glow border) from completed (collapsed with checkmark) and pending (grayed out) phases
- [ ] Each ReAct step card (Think/Act/Observe) appears with a visible slide-in animation and the text renders character-by-character (typewriter effect) — not all at once
- [ ] Think cards are visually distinct from Act and Observe cards (different background, italic text, brain icon)
- [ ] Each agent's cards display the agent's unique color theme and icon, making it immediately clear which agent is speaking

### Voting and HITL
- [ ] The voting panel shows cards that start face-down ("?") and flip one at a time with a visible 3D rotation animation
- [ ] HITL intervention appears as an inline node within the timeline (not a separate page/modal), with a working text input and submit buttons that resume the backend flow
- [ ] After the flow completes, the `DiagnosticDashboard` is displayed with a working "View Reasoning Process" toggle that expands the completed timeline

### Build Integrity
- [ ] `npm run build` in the `frontend/` directory completes with zero errors
- [ ] The backend server starts without import errors and the full SSE flow can be triggered via `GET /api/v1/analyze/stream`
