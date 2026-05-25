# PatentX 底层架构设计：完全积木化战略 (Block-Driven Architecture)

## 一、 战略愿景：从“独立硬编码系统”向“动态积木与管线编排”演进
受 Novoscan-Open-Core 架构的深刻影响，PatentX 在底座级别不再作为一套孤立的、采用 Python 硬编码的 LangGraph 状态机存在。PatentX 的底座设计转变为**向 Novoscan 核心编译器注册的一组特定领域的动态积木（Custom Blocks）以及预配的 JSON 管线（Pipeline JSON）**。

## 二、 积木化底座组件设计 (L1 - L3)

### 1. Agent 角色积木化 (AgentBlock - YAML 驱动)
不再在代码中硬写大模型的系统提示词与调用逻辑，而是使用 YAML 声明特定的专家角色，挂载所需的 API Tool：
*   **`patent_applicant.yaml`** (角色: `executor`): 专利申请代理人。负责提取核心发明点并结合检索结果构建辩护逻辑。
*   **`epo_examiner.yaml`** (角色: `critic`): EPO 审查员。基于新颖性、创造性、工业实用性标准，负责发起严苛质疑。
*   **`patent_judge.yaml`** (角色: `mediator`): 主审法官。负责监听辩论过程，记录争议点并作出阶段性或最终裁决。
*   **`pii_filter.yaml`** (角色: `filter`, 层级: `transform`): 数据脱敏转换器。负责在数据流入模型前进行 PII 脱敏并在报告生成前还原。

### 2. 交互模式积木化 (InteractionBlock)
彻底复用 Novoscan 已定义的通用交互积木，并在需要定制时采用 YAML 派生：
*   **`adversarial_debate.yaml` (对抗性辩论)**: 引入此交互块作为核心机制。声明法官（`moderator=1`）与辩论者（`debaters=2`）。内置回合节流阀机制（如 `max_rounds=3`，`ko_enabled=true`）。

### 3. 报告组件积木化 (ReportBlock)
*   **`patent_diagnostic_report.yaml`**: 最终交付报告的模板。声明所需的视图组件结构（例如：`patent_radar` 雷达图组件、`risk_matrix` 风险矩阵组件、`evidence_timeline` 证据时间线组件），由前端 Studio 依据类型自动渲染。

## 三、 Agentic Workflow 管线编排 (Pipeline JSON)

PatentX 最终将被固化为一份 `patentx_pipeline.json`。Novoscan 的 `PipelineCompiler` 会将这份 JSON 动态编译为具有持久化记忆（Checkpointer）的 StateGraph。

**预配置的 PatentX Pipeline 拓扑流：**
1.  **Transform 层**: `pii_filter` (数据物理脱敏拦截)
2.  **Retrieval 层**: 专利文献专网检索
3.  **Debate 层 (交互层)**: `patent_applicant` 与 `epo_examiner` 在 `adversarial_debate` 模式下激烈抗辩，`patent_judge` 进行监听与仲裁。
4.  **HITL 断点层**: 设置 `interrupt_before` 阈值，当辩论陷入死锁（法官判定无法达成共识）时，由底层引擎发出挂起信号，触发前端 `AgenticPauseCard`。
5.  **Report 层**: `patent_diagnostic_report` (组装合规报告)

## 四、 断点续传与人机协同 (HITL 零成本复用)

*   **挂起信号**: 管线在死锁点由 LangGraph 的底座天然生成 `hitl_interrupt` 事件。
*   **前端交互**: 不需要重新编写 Webhook 或 UI。当流式事件中断时，PatentX 直接复用前端 `StudioBottomDrawer` 和 `AnalysisStudioPage` 的 `AgenticPauseCard`。
*   **专家介入**: 专家通过底座现成的 `approve_and_continue`、`revise_inputs`、`abort` 三标准动作向引擎的 `/resume/stream` 路由发信号，激活挂起图的后续执行。

## 五、 TDD 开发执行策略

基于全新的底座，PatentX 的代码落地步骤简化如下：
1.  **Block 编写期**: 在 `app/agents/_custom/` 和 `app/interactions/_custom/` 目录下编写 PatentX 相关的 YAML 配置文件，无需修改底座引擎代码。
2.  **Tool 拓展期**: 根据专利查询特殊需求，开发针对特定学术/专利 API 的 Tool 函数，并注册到通用 Tool 库。
3.  **Pipeline 编译期**: 编排 JSON 配置文件，调用 Studio 底座编译接口，测试管线连通性与环路。
4.  **Agentic Tuning 联调期**: 通过前端 Agentic Canvas 可视化界面，验证断点能否正确唤起，数据能否被 PII 拦截层正确清洗。
