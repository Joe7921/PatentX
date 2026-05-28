# PatentX 全局上下文 — 完整版

> 最后更新：2026-05-27T00:40:00+08:00
> 状态：**全自主 Agentic 引擎重构已完成，并完成了系统鲁棒性及异常降级机制的增强与验证。**

---

## 一、项目定位

PatentX 是一个**多智能体专利新颖性评估系统**，模拟 EPO（欧洲专利局）真实三审查员合议庭工作流。核心价值：

1. 将国内专利放到 EPO 体系下进行新颖性评估
2. 多 Agent 实时对抗辩论，每个推理步骤流式可视化
3. 既可作为**独立业务板块**服务客户，也可作为 **Novoscan 超级工具（Super Tool）**被 Novoscan 中央 Agent 调用

---

## 二、技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python FastAPI + asyncio + SSE（`text/event-stream`）|
| Agent 引擎 | `server/agentic_engine.py`（待重构为真实 ReAct）|
| 共享状态 | `server/blackboard.py`（asyncio.Lock 保护）|
| LLM 路由 | `server/llm_factory.py`（DeepSeek API，支持 function calling）|
| 数据工具 | `server/tools/patent_tools.py`（待升级为 MCP Server）|
| 专利数据库 | `server/adapters/bigquery_adapter.py`（BigQuery `patents-public-data`，gcp-key.json 已配置）|
| 前端 | Vite + React + TypeScript + Zustand（自定义shim）+ Framer Motion v10 + TailwindCSS v3 |
| Agent 配置 | `app/agents/_custom/*.yaml`（YAML 声明式，含 llm/tools/prompts）|

---

## 三、当前架构问题（已确认）

**核心缺陷：现有 `agentic_engine.py` 是伪 Agentic 系统（已确认为 Pipeline）**

| 应有的自主行为 | 当前实际实现 |
|---|---|
| LLM 自主决定调哪个工具、调几次 | Python 引擎硬编码调用顺序 |
| 向量/语义检索真实 EP 专利 | 关键词匹配 2 条假专利 |
| L1 法官动态路由辩论 | 按固定模板顺序发言 |
| Chairman 自主决定召唤 Legal Examiner | `fully_disclosed_count >= 1` 硬判断 |
| 投票由各 Agent LLM 独立推理产生 | `random.random()` + 固定概率常量 |
| 黑板动态 Prompt 组装 | 每次 LLM 调用用预写 Fallback 模板 |

---

## 四、全自主重构计划（已批准执行）

### 4.1 目标架构

```
用户输入 claim
    │
    ▼
FastAPI /api/v1/analyze/stream
    │
    ▼
agentic_engine.py（真实 ReAct 引擎）
    │
    ├─ 每阶段：组装黑板上下文 → 调 LLMFactory（带 tools schema）
    │
    ├─ LLM 返回 tool_calls → MCPClient.call_tool(name, args)
    │        └─ 路由到 MCP Server → BigQueryAdapter / patent_tools
    │
    ├─ 工具结果回传 LLM → LLM 继续推理
    │
    ├─ LLM 返回终止标记 → 引擎推进到下一阶段
    │
    └─ 每步 yield SSE 事件 → 前端实时渲染
```

### 4.2 MCP 接入方案（已确定：方案 A）

- 后端自建 MCP Server（`server/mcp_server.py`），Python `mcp` SDK
- 暴露工具：`search_patent_db`、`search_academic_db`、`generate_feature_alignment_matrix`
- `LLMFactory` 传 `tools` 参数给 DeepSeek → DeepSeek 返回 `tool_calls`
- `MCPClient` 统一执行工具调用并返回结果
- 扩展新工具：只需启动新 MCP Server，零改引擎代码

### 4.3 里程碑

| 里程碑 | 内容 | 状态 |
|--------|------|------|
| M1 | MCP Server 建设（工具层） | [x] 已完成 |
| M2 | LLMFactory 升级（function calling） | [x] 已完成 |
| M3 | agentic_engine.py 完全重写（真实 ReAct） | [x] 已完成 |
| M4 | Agent YAML 配置扩展（工具权限声明） | [x] 已完成 |
| M5 | 前端 SSE 适配（新增字段向后兼容） | [x] 已完成 |
| M_verify | 全链路验证与降级下特征 ID 缺陷修复 | [x] 已完成 |
| M_robustness | 系统鲁棒性增强（熔断、参数预处理、明确 Mock） | [x] 已完成 |

### 4.4 关键文件变更清单

| 文件 | 操作 | 说明 |
|------|------|------|
| `server/mcp_server.py` | 新建 | MCP Server，暴露所有工具 |
| `server/mcp_client.py` | 新建 | MCPClient，统一工具调用路由 |
| `server/agentic_engine.py` | 完全重写 | 真实 ReAct 引擎，LLM 主导 |
| `server/llm_factory.py` | 重写 | 支持 tools 参数、tool_calls 解析 |
| `server/blackboard.py` | 扩展 | 新增 build_context_for_agent() 动态组装 |
| `server/tools/patent_tools.py` | 扩展 | 注册为 MCP 工具 |
| `app/agents/_custom/*.yaml` | 修改 | 扩展 tools 声明、max_react_rounds、终止指令 |
| `frontend/src/store/useStore.ts` | 小幅修改 | 处理新增 SSE 字段（向后兼容） |
| `frontend/src/store/agenticTypes.ts` | 小幅修改 | 新增 tool_args、tool_result_preview 字段 |

---

## 五、计划设计的完整拓扑架构（以此为准）

> 来源：`PatentX_Technical_Foundation_Report.md` v3.1（终稿，最权威）

### 5.1 分层嵌套 Agent-as-Tool 架构（设计目标）

```
用户终端 UI（探测舱上传 / 双屏看板）
    │  SSE 实时流
    ▼
API 网关 & SSE 推流总线（FastAPI /api/v1/analyze/stream）
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 0 — 中央编排 Agent（全局 ReAct 循环）              │
│  职责：信息够不够？需不需要开庭？最终生成报告              │
│                                                         │
│  Utility Tools（确定性函数）:                            │
│  ├── search_epo_patents        → MCP Server            │
│  │       └── BigQueryAdapter  → patents-public-data    │
│  ├── search_academic          → MCP Server             │
│  ├── pii_mask / pii_unmask    → MCP Server             │
│  ├── generate_report          → MCP Server             │
│  └── run_hearing ─────────────────────────────────┐    │
│                                                   │    │
└───────────────────────────────────────────────────┼────┘
                                                    │ 🔥 Agent Tool（嵌套子系统）
                                                    ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — 法官 Agent（庭审 ReAct 子循环）               │
│  职责：问谁、问什么、几轮、何时结案、何时叫人类           │
│                                                         │
│  Agent Tools（每个都是独立 LLM 推理链）:                 │
│  ├── call_novelty_examiner      → L2 新颖性审查员        │
│  ├── call_inventive_step_examiner → L2 创造性审查员      │
│  ├── call_industrial_examiner   → L2 工业实用性审查员    │
│  ├── call_applicant             → L2 专利申请代理律师    │
│  ├── request_human_expert       → HITL 挂起工具         │
│  └── (演进预留) spawn_expert    → 动态生成临时专家       │
│                                                         │
└───────────────┬───────────────────────────────────┬─────┘
                │ 被法官按需调用                     │
                ▼                                   ▼
┌──────────────────────────┐       ┌──────────────────────────┐
│  Layer 2 — 专精 Agent    │       │  Layer 2 — 律师 Agent    │
│  新颖性审查员  EPC Art.54 │       │  专利申请代理律师         │
│  创造性审查员  EPC Art.56 │       │  提取发明亮点 逐条反驳    │
│  工业实用性    EPC Art.57 │       │                          │
└──────────────────────────┘       └──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────┐
│  MCP Server 工具层（独立进程/in-process）                  │
│  ├── search_patent_db     → BigQueryAdapter              │
│  │       └── patents-public-data（Google BigQuery）      │
│  ├── search_academic_db   → OpenAlex / arXiv             │
│  ├── generate_feature_alignment_matrix                   │
│  └── (未来扩展) EPO OPS、Lens API 等                     │
└──────────────────────────────────────────────────────────┘
```

### 5.2 当前拓扑图 HTML 与计划的差异（需修正）

`PatentX_Architecture_Visualization.html` 存在以下**与设计计划不符**的内容：

| 位置 | 当前拓扑图描述（待修正） | 计划设计的事实 |
|------|--------------------------|---------------|
| Tab1 - PatentX 节点说明 | "全面采用 YAML 驱动…由 Novoscan PipelineCompiler 动态编译运行" | 计划是 FastAPI + L0/L1/L2 分层嵌套 ReAct，**不依赖 PipelineCompiler**，是独立引擎 |
| Tab1 - 基础设施层 | "深度复用 Novoscan AiClientProvider" | 计划中独立模式下自建 LLM 路由（`LLMFactory`）；仅在 Novoscan 集成模式下才复用 |
| Tab1 - 拓扑节点层次 | 仅4层：用户→网关→[Novoscan+PatentX]→共享基座 | 计划中应有：用户→网关→L0中央Agent→L1法官Agent→L2专精Agents，以及独立的 MCP Server 工具层 |
| Tab2 - 模拟步骤2 | "RAG 预热：并发拉取 EPO 历史特征分类缓存" | 计划中没有预热缓存，L0 Agent 主动通过 `search_epo_patents` MCP 工具实时检索 |
| Tab2 - HITL 触发 | 固定步骤3触发 | 计划中由 L1 法官 Agent 在辩论中**自主调用** `request_human_expert` 工具触发，不是固定步骤 |
| Tab3 - 3分钟降级 | "达到 3 分钟，前端 SSE 链接优雅切断" | 计划中是 HITL 10 分钟超时（`asyncio.wait_for`, timeout=600），SSE 3分钟指前端展示"合议中"，后端仍继续 |
| Tab1 | 缺少 MCP Server 层 | 计划中 MCP Server 是独立工具层，需要在拓扑图中体现 |

### 5.3 双态生态定位（计划确定）

| 形态 | 说明 | L0 层 |
|------|------|-------|
| **独立业务板块** | 自有前端 + API，单独对外服务 | PatentX 自建 L0 中央编排 Agent |
| **Novoscan 超级工具** | 被 Novoscan 中央 Agent 调用 | Novoscan 接管 Layer 0，PatentX 从 L1 法官层入口接收参数 |

> Layer 1（法官领导庭审）和 Layer 2（专精审查员）行为逻辑在两种形态下完全一致。

### 5.4 HITL 双层触发机制（计划确定）

| 触发层 | 触发场景 | 触发方式 |
|--------|----------|---------|
| **L1 法官** | 辩论中出现技术歧义，专家池无法解决 | 法官自主调用 `request_human_expert(reason, context)` 工具 |
| **L0 中央** | 整体流程异常（如所有检索无结果） | 中央 Agent 自主判断后触发 |

HITL 完整流程：
```
法官调用 request_human_expert()
    → asyncio.Event 挂起（timeout=600s）
    → SSE 推送 hitl_interrupt → 前端时间线内联 HITL 节点展开
    → 专家提交 POST /api/v1/evaluation/{id}/resume
    → 黑板写入 expert_annotations
    → asyncio.Event.set() → 法官 ReAct 继续
```

### 5.5 前端 SSE 监听兼容性分析

`useStore.ts` 现有监听与新架构**完全兼容**，理由：
- 现有事件类型全部保留（`phase_start / agent_think / agent_act / agent_observe / vote_cast` 等）
- 新增字段（`tool_args`、`tool_result_preview`）为可选字段，前端未使用时自动忽略

**需要新增的类型字段（小改 `agenticTypes.ts`）：**

```typescript
export interface ReactStep {
  // 现有字段不变...
  tool_args?: Record<string, unknown>;   // LLM 传入工具的参数
  tool_result_preview?: string;          // 工具返回结果摘要
  is_tool_decision?: boolean;            // 区分"决定调工具"和"纯思考"
}
```

**`DynamicTopoGraph.tsx` 小改建议：**
- 工具节点（`type: 'tool'`）新增 `tool_args` 悬浮展示
- 同一 phase 内 tool 节点数量和种类由 LLM 动态决定，现有 `parentId` 追踪逻辑已能处理，**无需重写**

---

## 六、关键约束（所有 Agent 执行前必读）

1. **[P0] 多智能体沙盒隔离**：任何涉及多文件重构的子 Agent 调用必须使用 `Workspace: 'branch'`
2. **[P0] 核心文件保护**：修改 `.agent/protected_files.json` 内的文件前必须获得用户明确授权
3. **Windows PowerShell 环境**：命令用 `;` 分隔，禁止 `&&`；禁止 `Set-Content`/`Out-File` 修改源代码
4. **所有代码注释和 UI 文本使用简体中文**
5. **zustand 使用自定义 shim**（`frontend/src/store/zustand.ts`），禁止 `npm install zustand`
6. **非必要不硬编码**：工具列表、Agent 角色、Prompt 均从 YAML 读取，不写死在 Python 代码里
7. **LLM Fallback 链**：DeepSeek API Key 缺失时，降级为高质量预写模板，系统继续运行，不崩溃
8. **BigQuery 降级**：GCP 连接失败时，自动回退 Mock 数据库，SSE 流继续

---

## 七、目录结构（关键路径）

```
PatentX/
├── .agent/
│   ├── context.md          ← 本文件
│   ├── task.md             ← 执行任务跟踪
│   └── .plan/              ← 所有历史设计计划（15份）
├── server/
│   ├── main.py             ← FastAPI 入口（3个API端点）
│   ├── agentic_engine.py   ← 待重写：真实ReAct引擎
│   ├── blackboard.py       ← 共享状态（asyncio.Lock）
│   ├── llm_factory.py      ← 待重写：支持function calling
│   ├── mcp_server.py       ← 待新建：MCP Server
│   ├── mcp_client.py       ← 待新建：MCPClient
│   ├── gcp-key.json        ← GCP服务账号密钥（已存在）
│   ├── .env                ← DEEPSEEK_API_KEY 配置
│   ├── adapters/
│   │   ├── base_adapter.py
│   │   ├── bigquery_adapter.py  ← BigQuery真实查询（已实现）
│   │   ├── epo_ops_adapter.py
│   │   └── lens_adapter.py
│   └── tools/
│       └── patent_tools.py ← 待升级：注册为MCP工具
├── app/agents/_custom/
│   ├── epo_examiner.yaml   ← 待扩展：tools声明、终止指令
│   ├── patent_judge.yaml   ← 待扩展
│   ├── patent_applicant.yaml
│   └── pii_filter.yaml
└── frontend/src/
    ├── store/
    │   ├── useStore.ts      ← SSE监听（向后兼容，小改）
    │   ├── agenticTypes.ts  ← 类型定义（新增tool_args等字段）
    │   └── zustand.ts       ← 自定义shim（禁止替换）
    └── components/
        ├── AgenticTimeline.tsx
        ├── DynamicTopoGraph.tsx  ← 需新增tool_args悬浮展示
        └── timeline/
```

---

## 八、SSE 事件协议（完整版，含新增字段）

```
phase_start:    {phase: 1-4, name: str, title: str, agents: [str]}
agent_think:    {agent: str, phase: int, round: int, content: str, is_tool_decision?: bool}
agent_act:      {agent: str, phase: int, round: int, tool: str, content: str,
                 tool_args?: {...},           ← 新增：LLM传入工具的参数
                 tool_result_preview?: str}   ← 新增：工具返回摘要
agent_observe:  {agent: str, phase: int, round: int, content: str}
phase_complete: {phase: int, summary: str}
agent_summon:   {agent: "legal_examiner", reason: str}
hitl_interrupt: {id: str, reason: str, phase: int}
vote_cast:      {agent: str, vote: "Grant"|"Reject"|"Conditional Grant", reasoning: str}
completed:      {conclusion: str, probability: float, votes: [...], state: {...}}
error:          {type: "error", message: str}
```

---

## 九、BigQuery 配置状态

- `server/gcp-key.json`：GCP 服务账号密钥**已存在**
- `server/api_pool.yaml`：`google_bigquery.mock_fallback = false`（已配置真实模式）
- `server/adapters/bigquery_adapter.py`：完整实现，含 SQL 查询 `patents-public-data.patents.publications`
- **当前问题**：`agentic_engine.py` 绕过了 `bigquery_adapter`，直接调用 `patent_tools.py` 假数据
- **重构后**：LLM 通过 MCP `search_patent_db` 工具调用 → `BigQueryAdapter.retrieve()` → 真实 BigQuery

---

## 十、需要同步更新的文档（重构完成后）

1. `PatentX_Architecture_Visualization.html` — 拓扑图节点说明需更新（见第五节）
2. `.agent/task.md` — 执行任务跟踪
3. `.agent/.plan/streaming_agentic_plan.md` — 验收标准需追加真实自主性验证条目
