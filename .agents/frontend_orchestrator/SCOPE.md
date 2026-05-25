# Scope: Frontend Build and E2E Integration

## Architecture
- **Frontend**: Vite React+TS single-page app utilizing TailwindCSS v3. Subscribes to SSE from the server and provides interactive components.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M2 | Frontend Build & Integration | `frontend/*` (Vite, UI Components, SSE integration) | M1 (Backend) | DONE |

## Interface Contracts
### Frontend ↔ Backend
- `GET /api/v1/analyze/stream`: Returns `text/event-stream`. 
  - Events: `node_start`, `hitl_interrupt` (includes { "id": "<eval_id>" }), `completed`.
- `POST /api/v1/evaluation/{id}/resume`: Body: `{"action": "Approve|Revise", "details": "..."}`. Returns `{"status": "resumed"}`.
