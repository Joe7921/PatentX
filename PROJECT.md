# Project: PatentX Mock System
# Scope: Full System

## Architecture
- **Server**: FastAPI mock backend, listening for API requests, simulating stream and handling HITL (Human-In-The-Loop) resume.
- **Frontend**: Vite React+TS single-page app utilizing TailwindCSS v3. Subscribes to SSE from the server and provides interactive components.

## Milestones (历史版本已完成)
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Backend Mock | `server/main.py`, `verify_backend.py` | none | DONE |
| 2 | Frontend Build | `frontend/*` (Vite, UI Components) | M1 | DONE |
| 3 | E2E Integration | UI interaction, State machine transitions | M2 | DONE |

## UI/UX 全景重塑里程碑 (v2.0)
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | 依赖审计与后端 SSE 适配   | `server/main.py`, `tools/patent_tools.py`       | none         | DONE        |
| M2 | 统一物理容器与极光背景     | `frontend/src/App.tsx`, `AuroraBackground.tsx` | M1           | DONE        |
| M3 | 欢迎向导与注意力焦点锁定   | `frontend/src/components/*` (对接 SSE)          | M2           | DONE        |
| M4 | 挂起暗淡与单元格批注粒子反馈 | `frontend/src/components/*`, `/resume`          | M3           | DONE        |
| M5 | 3D 特征星图与 CoT 折叠     | 3D 星图组件, 辩论日志 CoT 折叠                 | M4           | DONE        |
| M6 | 全链路构建与 E2E 验证 | 前端打包与 E2E 测试, Auditor 审计 | M5 | DONE |
| M7 | 废除 3D 星图与恢复原有风格 | 移除 3D 星图与 CoT 面板, 还原 App.tsx 各卡片独立动画 | M6 | DONE |
| M8 | iPhone 远程 Web 控制台部署 | 部署 Guacamole 远程桌面及 ttyd 网页终端, 对接 Tailscale IP 端口 | M7 | DONE |


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
- `d:\Antigravity projects\PatentX\frontend\`
  - Vite project files
  - `src/components/UploadHub.tsx`
  - `src/components/ThinkingIndicator.tsx`
  - `src/components/AgenticPauseCard.tsx`
  - `src/components/DiagnosticDashboard.tsx`
