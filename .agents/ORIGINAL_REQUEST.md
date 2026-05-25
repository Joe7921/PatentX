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
