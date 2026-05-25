# Scope: Milestone 1: Backend Mock

## Architecture
- FastAPI mock backend, listening for API requests, simulating stream and handling HITL (Human-In-The-Loop) resume.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Backend Mock | `server/main.py`, `verify_backend.py` | none | DONE |

## Interface Contracts
### Frontend ↔ Backend
- `GET /api/v1/analyze/stream`: Returns `text/event-stream`. 
  - Events: `node_start`, `hitl_interrupt` (includes { "id": "<eval_id>" }), `completed`.
- `POST /api/v1/evaluation/{id}/resume`: Body: `{"action": "Approve|Revise", "details": "..."}`. Returns `{"status": "resumed"}`.

## Code Layout
- `d:\Antigravity projects\PatentX\server\`
  - `main.py`
  - `requirements.txt`
  - `verify_backend.py`
