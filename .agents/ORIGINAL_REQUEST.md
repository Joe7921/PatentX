# Original User Request

## Initial Request — 2026-05-23T12:00:58Z

Refactor the PatentX React frontend to use Google Gemini-style UI (Aurora Canvas Background) and I/O Morphing Card transitions.

Working directory: d:\Antigravity projects\PatentX\frontend
Integrity mode: development

## Requirements

### R1. UI Library Integration
Install `framer-motion` and `lucide-react` into the existing Vite React+TS project.

### R2. Global Styles & Tailwind
Configure `tailwind.config.js` (Tailwind v3) with an "aurora" color palette (sky, mint, teal). Add a `.glass-panel` utility class to `index.css` to achieve a light Glassmorphism effect (backdrop blur, white translucent background, soft shadow).

### R3. Aurora Canvas Background
Implement `src/components/AuroraBackground.tsx` using a native HTML5 Canvas to render a slow, soft moving gradient (Aurora effect) in the background. Do not use heavy WebGL libraries.

### R4. Morphing Components & Transitions
Refactor `App.tsx` to wrap the main step flow in `framer-motion`'s `AnimatePresence`. Refactor `UploadHub`, `ThinkingIndicator`, `AgenticPauseCard`, and `DiagnosticDashboard` to use `motion.div` and `layoutId` so they morph smoothly into each other. Fix any pre-existing syntax errors in `DiagnosticDashboard.tsx`.

## Acceptance Criteria

### Build & Syntax Verification
- [ ] **Production Build**: Running `npm run build` in the `frontend` directory must complete successfully with exit code 0, proving there are no unresolved TypeScript errors, missing imports, or JSX syntax errors.
- [ ] **Dependency Check**: `framer-motion` and `lucide-react` must be present in `package.json`.
- [ ] **Style Verification**: `index.css` must define `.glass-panel`.
- [ ] The `DiagnosticDashboard.tsx` must render correctly without the previous syntax bugs (unclosed braces/duplicate states).


## Follow-up — 2026-05-27T01:59:40+08:00

# Teamwork Project Prompt — Draft

> Status: Launched.
> Goal: Complete implementation and verification of robust architecture features.

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
