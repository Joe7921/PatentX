# Scope: Milestone 2: Refactor Types & Store

## Architecture
- Refactor `frontend/src/store/agenticTypes.ts` and `frontend/src/store/useStore.ts`
- Remove `any` types, split long functions, remove hardcoded mock data, add proper error handling.
- Build test: `npm run build` in `frontend/`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M2_Refactor | agenticTypes.ts and useStore.ts refactoring | none | IN_PROGRESS |

## Interface Contracts
### frontend/src/store ↔ components
- Strict types required. No `any`.
