# PatentX 流式 Agentic 推理可视化系统 — 详细实施计划

## 架构概览

### 当前架构
- **后端**: 硬编码5步SSE管道 (parsing → retrieval → debating → hitl_interrupted → completed)
- **前端**: 4状态机 (UPLOAD → THINKING → PAUSED → DASHBOARD)，ThinkingIndicator为简单spinner
- **SSE事件**: node_start, node_complete, hitl_interrupt, completed

### 目标架构
- **后端**: EPO 3审查员协作系统，4阶段半自主Agentic工作流，每阶段含ReAct循环
- **前端**: 垂直时间线UI，双层(宏观阶段+微观ReAct步骤)，打字机效果，Agent身份主题
- **SSE事件**: phase_start, agent_think, agent_act, agent_observe, phase_complete, vote_cast, agent_summon, hitl_interrupt, completed

---

## M1: 后端 Agentic SSE 引擎

### 目标
将 `server/main.py` 的硬编码管道替换为4阶段EPO协作工作流

### 涉及文件
- `server/main.py` — 重写 analyze_stream 端点
- `server/blackboard.py` — 扩展状态模型，增加阶段/Agent/ReAct/投票状态
- `server/agentic_engine.py` — **新建**，Agentic工作流引擎
- `server/agents/` — **新建目录**，Agent定义(FirstExaminer, SecondExaminer, Chairman, ApplicantRep, LegalExaminer)

### 详细设计

#### 1.1 Blackboard 扩展
```python
# 新增字段
current_phase: int  # 1-4
current_phase_name: str  # document_analysis, internal_review, oral_proceedings, final_decision
agents: Dict[str, AgentState]  # 每个agent的状态
react_steps: List[ReactStep]  # 所有ReAct步骤历史
votes: List[VoteRecord]  # 投票记录
legal_examiner_summoned: bool  # 是否召唤了法律审查员
hitl_required: bool  # 是否需要HITL
```

#### 1.2 SSE事件协议
```
phase_start:  {phase: 1-4, name: str, agents: [str]}
agent_think:  {agent: str, phase: int, round: int, content: str}
agent_act:    {agent: str, phase: int, round: int, tool: str, content: str}
agent_observe:{agent: str, phase: int, round: int, content: str}
phase_complete:{phase: int, summary: str}
agent_summon: {agent: "legal_examiner", reason: str}
vote_cast:    {agent: str, vote: "Grant"|"Reject"|"Conditional Grant", reasoning: str}
hitl_interrupt:{id: str, reason: str, phase: int}
completed:    {conclusion: str, probability: float, votes: [...]}
```

#### 1.3 四阶段工作流
- **Phase 1 (文档分析与检索)**: 仅 first_examiner，ReAct循环(最多8轮)
  - Think: 分析权利要求特征
  - Act: 调用 search_patent_db / search_academic_db
  - Observe: 整理检索结果
- **Phase 2 (内部审查会议)**: second_examiner + chairman，ReAct循环
  - Chairman主持，判断是否需要召唤Legal Examiner (agent_summon)
  - 如有重大分歧，触发HITL
- **Phase 3 (口头审理)**: 4个主要agent对抗辩论
  - Chairman主持，first_examiner + second_examiner vs applicant_representative
  - Legal Examiner(如已召唤)参与
- **Phase 4 (最终裁决)**: 投票
  - 3或4人投票(取决于Legal Examiner是否参与)
  - 每票发出 vote_cast SSE事件

### 验收标准
- SSE事件序列正确: phase_start → (agent_think → agent_act → agent_observe)+ → phase_complete
- Phase 1只有first_examiner
- Phase 2有second_examiner和chairman
- Phase 3有4个agent
- Phase 4发出3-4个vote_cast事件
- 法律争议时发出agent_summon
- 后端无导入错误

---

## M2: 前端时间线组件

### 目标
替换ThinkingIndicator为垂直时间线UI

### 涉及文件
- `frontend/src/components/AgenticTimeline.tsx` — **新建**，主时间线容器
- `frontend/src/components/timeline/PhaseNode.tsx` — **新建**，阶段节点
- `frontend/src/components/timeline/ReactStepCard.tsx` — **新建**，ReAct步骤卡片
- `frontend/src/components/timeline/TimelineConnector.tsx` — **新建**，连接线
- `frontend/src/components/timeline/TypewriterText.tsx` — **新建**，打字机效果
- `frontend/src/store/useStore.ts` — 扩展状态，增加时间线状态管理
- `frontend/src/store/agenticTypes.ts` — **新建**，类型定义
- `frontend/src/App.tsx` — 替换THINKING状态渲染

### 详细设计

#### 2.1 类型定义 (agenticTypes.ts)
```typescript
interface AgentTheme { name: string; color: string; icon: string; bgClass: string; borderClass: string; }
interface ReactStep { type: 'think' | 'act' | 'observe'; agent: string; content: string; round: number; timestamp: number; }
interface PhaseState { id: number; name: string; status: 'pending' | 'active' | 'completed'; agents: string[]; steps: ReactStep[]; }
interface VoteRecord { agent: string; vote: string; reasoning: string; revealed: boolean; }
interface AgenticTimelineState { phases: PhaseState[]; votes: VoteRecord[]; currentPhase: number; legalExaminerSummoned: boolean; hitlRequired: boolean; }
```

#### 2.2 Agent主题配色
- First Examiner: 蓝色 (#3B82F6), 搜索图标
- Second Examiner: 琥珀色 (#F59E0B), 审查图标
- Chairman: 紫色 (#8B5CF6), 法槌图标
- Applicant Representative: 青色 (#06B6D4), 盾牌图标
- Legal Examiner: 玫瑰色 (#F43F5E), 天秤图标

#### 2.3 时间线动画规范
- 阶段节点: active时发光边框(box-shadow pulse), completed时折叠+对勾
- ReAct卡片: slide-in from below (y: 20 → 0, opacity: 0 → 1, duration: 0.3s)
- Think卡片: italic文字 + subtle pulse背景 + 🧠图标
- Act卡片: agent主题色背景
- Observe卡片: 数据摘要样式
- 打字机效果: requestAnimationFrame逐字渲染 + 闪烁光标
- 连接线: 灰色→蓝色流动填充动画

#### 2.4 Store扩展
- 新增 agenticState 对象管理时间线状态
- 扩展SSE事件处理: phase_start, agent_think, agent_act, agent_observe, phase_complete, vote_cast, agent_summon

### 验收标准
- 4个阶段节点垂直排列
- 活跃阶段有发光动画，完成阶段折叠+对勾，待处理灰显
- ReAct卡片滑入动画+打字机效果
- Think/Act/Observe卡片视觉区分
- 每个agent有独特颜色主题

---

## M3: 投票面板 + HITL内联

### 目标
3D翻牌投票面板 + HITL内联时间线节点

### 涉及文件
- `frontend/src/components/timeline/VotingPanel.tsx` — **新建**，投票面板
- `frontend/src/components/timeline/VoteCard.tsx` — **新建**，投票卡片(3D翻转)
- `frontend/src/components/timeline/HITLNode.tsx` — **新建**，HITL内联节点

### 详细设计

#### 3.1 投票面板
- 3或4张投票卡片水平排列
- 初始显示"?"(背面)
- 每张卡片间隔1.5s依次翻转(3D Y轴旋转, perspective: 1000px, rotateY: 0→180°)
- 翻转后显示: 投票结果 + agent颜色标识 + 理由摘要
- 全部翻转后，底部显示最终多数决(金色发光动画)

#### 3.2 HITL内联节点
- 琥珀色主题节点，嵌入时间线Phase 2和Phase 3之间
- 展开时显示: 文字输入区 + 批准/修正按钮
- 复用AgenticPauseCard逻辑
- 提交后节点折叠+对勾，时间线继续

### 验收标准
- 投票卡片从"?"翻转显示结果
- 3D Y轴旋转动画可见
- HITL在时间线内(非独立页面/模态框)
- 文本输入和提交按钮正常工作

---

## M4: 仪表盘集成 + 推理过程折叠

### 目标
完成后显示DiagnosticDashboard，顶部可折叠查看推理时间线

### 涉及文件
- `frontend/src/components/DiagnosticDashboard.tsx` — 修改，顶部增加折叠按钮
- `frontend/src/App.tsx` — 修改DASHBOARD状态渲染逻辑

### 详细设计
- Dashboard顶部增加"查看推理过程"按钮
- 点击展开只读时间线(所有阶段completed，无打字机动画，文字完整渲染)
- 使用Framer Motion AnimatePresence实现展开/折叠动画

### 验收标准
- 流程完成后显示DiagnosticDashboard
- "查看推理过程"按钮可折叠展开
- 展开的时间线为只读状态

---

## M5: 全链路E2E验证

### 目标
确保前后端完整联调通过

### 验证内容
- `npm run build` 零错误
- 后端无导入错误
- SSE流完整走通4阶段
- 前端时间线正确渲染所有事件
- 投票面板动画正常
- HITL内联正常
- 仪表盘折叠正常

---

## 里程碑依赖关系
```
M1 (后端引擎) ──→ M5 (E2E验证)
   ↘                ↗
M2 (前端时间线) ─→ M3 (投票+HITL) → M4 (仪表盘集成) → M5
```

## 执行策略
- M1和M2可并行开始(后端和前端独立开发)
- M3依赖M2(需要时间线组件框架)
- M4依赖M2+M3(需要完整时间线)
- M5依赖M1+M4(需要前后端都完成)

## 风险与缓解
- **LLM API调用**: 后端保持Mock模式可运行，不依赖真实API
- **framer-motion版本**: 当前v10.x，确保使用兼容API
- **zustand自定义shim**: 项目使用自定义zustand实现而非npm包，需保持兼容
- **TypeScript严格模式**: tsconfig中的strict可能导致类型错误
