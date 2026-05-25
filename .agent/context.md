# PatentX 流式 Agentic 推理可视化系统 — 上下文

## 项目状态: M1-M4 实现完成，待构建验证

## 宏观方向
将 PatentX 从硬编码5步SSE管道重构为EPO 3审查员协作系统：
1. 4阶段半自主Agentic工作流 (文档分析与检索 → 内部审查会议 → 口头审理 → 最终裁决) ✅
2. ReAct循环 (Think → Act → Observe) 每步独立SSE事件 ✅
3. 垂直时间线UI (Gemini风格动画 + 打字机效果) ✅
4. 3D翻牌投票面板 (perspective + rotateY) ✅
5. HITL内联时间线节点 (琥珀色主题) ✅
6. 仪表盘推理过程折叠查看 ✅

## 技术栈
- Backend: Python FastAPI (server/main.py, blackboard.py, agentic_engine.py, llm_factory.py)
- Frontend: Vite + React + TypeScript + Zustand(自定义shim) + Framer Motion v10 + TailwindCSS v3
- SSE协议: phase_start, agent_think, agent_act, agent_observe, phase_complete, vote_cast, agent_summon, hitl_interrupt, completed
- AuroraBackground 极光背景 (slate-50基色 + multiply-blend)

## 里程碑
| # | 名称 | 状态 |
|---|------|------|
| M1 | 后端 Agentic SSE 引擎 | ✅ 完成 |
| M2 | 前端时间线组件 | ✅ 完成 |
| M3 | 投票面板 + HITL内联 | ✅ 完成 |
| M4 | 仪表盘集成 + 推理过程折叠 | ✅ 完成 |
| M5 | 全链路E2E验证 | ⏳ 待构建验证 |

## 新增/修改文件清单

### 后端 (M1)
| 文件 | 操作 | 说明 |
|------|------|------|
| `server/agentic_engine.py` | 新建(734行) | 4阶段EPO审查工作流核心引擎 |
| `server/main.py` | 重写(165行←379行) | analyze_stream委托给agentic_engine |
| `server/blackboard.py` | 已有扩展(188行) | 含phase/react/votes/legal扩展 |

### 前端 (M2+M3+M4)
| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/store/agenticTypes.ts` | 新建(149行) | Agent主题+类型定义 |
| `frontend/src/components/timeline/TypewriterText.tsx` | 新建(~83行) | 打字机效果 |
| `frontend/src/components/timeline/ReactStepCard.tsx` | 新建(~103行) | ReAct步骤卡片 |
| `frontend/src/components/timeline/PhaseNode.tsx` | 新建(169行) | 阶段节点 |
| `frontend/src/components/timeline/TimelineConnector.tsx` | 新建(~69行) | 垂直连接器 |
| `frontend/src/components/timeline/VotingPanel.tsx` | 新建(191行) | 3D翻转投票面板 |
| `frontend/src/components/timeline/HITLNode.tsx` | 新建(~117行) | HITL内联节点 |
| `frontend/src/components/AgenticTimeline.tsx` | 新建(119行) | 主时间线容器 |
| `frontend/src/store/useStore.ts` | 修改(367行) | SSE事件扩展 |
| `frontend/src/App.tsx` | 修改(94行) | AgenticTimeline替换 |
| `frontend/src/components/DiagnosticDashboard.tsx` | 修改 | 推理过程折叠 |

## 关键约束
- 所有代码注释和UI文本使用简体中文
- Windows PowerShell环境
- 禁止PowerShell修改源代码文件(BOM风险)
- 新UI与AuroraBackground视觉风格和谐
- 非必要不硬编码
- zustand使用自定义shim (frontend/src/store/zustand.ts)，非npm原版

## 详细计划
见 `.agent/.plan/streaming_agentic_plan.md`

## 最后更新: 2026-05-25T16:39:00+08:00
