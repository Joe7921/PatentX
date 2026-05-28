# Scope: Milestone 1: Restore LandingPage

## Architecture
- `LandingPage.tsx` provides the first screen experience (Slogan, background, etc.).
- `UploadHub` should be embedded within `LandingPage`.
- `App.tsx` should render `LandingPage` in its initial state (or `UPLOAD` state), rather than directly rendering `UploadHub`.
- Inputs from `LandingPage` flow to the Zustand store to trigger the analysis flow.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Restore LandingPage | Find or recreate LandingPage.tsx, integrate UploadHub, wire to Zustand store, build verify | none | DONE |

## Interface Contracts
### App.tsx ↔ LandingPage.tsx
- App renders LandingPage.
### LandingPage.tsx ↔ UploadHub.tsx
- LandingPage renders UploadHub internally.
### LandingPage.tsx ↔ Zustand Store
- Proper action dispatch to trigger state changes.
