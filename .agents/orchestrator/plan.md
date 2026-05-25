# 项目架构与宏观规划

## 1. 目标
构建 PatentX 演示系统（后端 FastAPI，前端 React + Vite），模拟完整的全息界面工作流（上传 -> 流传输 -> HITL暂停 -> 恢复 -> 仪表板）。

## 2. 计划 Milestone
- Milestone 1: **后端 Mock 实现**。构建 FastAPI 服务，包含 SSE 接口和恢复接口，编写 `verify_backend.py`。
- Milestone 2: **前端初始化与组件开发**。Vite + TS + Tailwind v3，开发 UploadHub, ThinkingIndicator, AgenticPauseCard, DiagnosticDashboard。
- Milestone 3: **端到端集成**。前端对接后端 SSE，跑通 IDLE -> STREAMING -> PAUSED (HITL) -> COMPLETED 流程。

## 3. 执行细节
我们将分别派发任务给 teamwork_preview_worker 完成上述 Milestone。并要求编写自动化测试或者审查脚本。
