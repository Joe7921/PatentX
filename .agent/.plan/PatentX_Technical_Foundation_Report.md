# PatentX 技术底座报告 v3.1

> **文档状态**: 终稿待审 | **日期**: 2026-05-21  
> **架构底色**: 分层嵌套 Agent-as-Tool Agentic Workflow  
> **定位**: 底座架构级设计纲领

---

## 一、底色宣言

> **PatentX 是一个分层嵌套的 Agent-as-Tool Agentic Workflow 系统。**

核心理念：

1. **Agentic Workflow** — Agent 拥有自主推理与动态决策权，不是被动节点。
2. **Agent as Tool** — 专精审查 Agent 各自拥有独立 LLM 推理链，被包装为 Tool 供上层 Agent 调用。
3. **分层嵌套** — 中央编排 Agent 负责全局策略；法官 Agent 作为子编排者领导庭审辩论；各专精审查员和律师是法官手中的武器。

---

## 二、分层嵌套架构

```
Layer 0 ── 中央编排 Agent (全局 ReAct)
            │  职责：信息够不够？需不需要辩论？最终出报告
            │
            ├── search_epo_patents          [Utility Tool]
            ├── search_academic             [Utility Tool]
            ├── pii_mask / pii_unmask       [Utility Tool]
            ├── generate_report             [Utility Tool]
            │
            └── run_hearing ──────────────── [🔥 Agent Tool — 嵌套子系统]
                   │
Layer 1 ── 法官 Agent (庭审 ReAct 子循环)
                   │  职责：问谁、问什么、几轮、何时结案、何时叫人类
                   │
                   ├── call_novelty_examiner        [Agent Tool]
                   ├── call_inventive_step_examiner  [Agent Tool]
                   ├── call_industrial_examiner      [Agent Tool]
                   ├── call_applicant                [Agent Tool]
                   ├── request_human_expert          [HITL Tool]
                   │
                   └── (演进预留) spawn_expert       [动态生成 Tool]
                          │
Layer 2 ── 专精 Agent (被调用时启动独立 LLM 推理链)
            ├── 新颖性审查员    — 专攻 EPC Art.54
            ├── 创造性审查员    — 专攻 EPC Art.56
            ├── 工业实用性审查员 — 专攻 EPC Art.57
            └── 申请方律师      — 提取发明亮点，逐条反驳
```

### 各层职责边界

| 层级 | 角色 | 自主决策范围 | 不应做的事 |
|------|------|------------|-----------|
| **L0 中央** | 全局编排者 | 信息充分性判断、是否开庭、报告生成 | 不直接指挥辩论细节 |
| **L1 法官** | 庭审指挥官 | 选择质询哪个审查员、辩论轮次、是否需要 HITL | 不做全局检索或报告生成 |
| **L2 专家** | 领域武器 | 在自身专业内自主推理和论证 | 不决定辩论流程 |

---

## 三、双态生态定位

| 形态 | 说明 | 运行时 |
|------|------|--------|
| **独立业务板块** | 自有前端 + API，单独对外服务 | PatentX 自建 LangGraph Agentic Runtime |
| **Novoscan 超级工具** | 被 Novoscan 中央 Agent 调用 | Novoscan 编排器接管 Layer 0 |

> 无论哪种形态，Layer 1（法官领导辩论）和 Layer 2（专精审查员）的行为逻辑完全一致。

---

## 四、Agent Tool 完整清单

### 4.1 Layer 2 — Agent Tool（拥有独立 LLM 推理链）

| Tool 名称 | Agent 角色 | role_type | 专攻领域 |
|-----------|-----------|-----------|---------|
| `call_novelty_examiner` | 新颖性审查员 | `critic` | EPC Art.54 — 是否已被现有技术公开 |
| `call_inventive_step_examiner` | 创造性审查员 | `critic` | EPC Art.56 — 是否对本领域技术人员显而易见 |
| `call_industrial_examiner` | 工业实用性审查员 | `critic` | EPC Art.57 — 是否可在工业中制造或使用 |
| `call_applicant` | 专利申请代理律师 | `executor` | 提取发明亮点，针对性反驳各审查员质疑 |

### 4.2 Layer 0/1 — Utility Tool（确定性函数）

| Tool 名称 | 所属层 | 职责 |
|-----------|-------|------|
| `search_epo_patents` | L0 | EPO 专利数据库检索 |
| `search_academic` | L0 | 学术文献检索 (OpenAlex/arXiv) |
| `pii_mask` / `pii_unmask` | L0 | 隐私脱敏与还原 |
| `generate_report` | L0 | 组装结构化诊断报告 |
| `run_hearing` | L0→L1 | 启动法官子编排循环（嵌套 Agentic 入口） |
| `request_human_expert` | L1 | 触发 HITL 挂起 |

### 4.3 演进预留 — `spawn_expert`

底座阶段法官只能从固定专家池调用。后续演进方向：

```python
# 法官在辩论中发现需要新领域专家时
spawn_expert(
    role_description="材料学光子晶体领域专家",
    focus="非对称缺陷层的能带隙闭合机制",
    base_template="generic_expert.yaml"
)
# → 系统基于通用模板 + 法官描述，实时生成临时 Agent Tool
# → 若生成质量不足，自动降级为 HITL 请求人类专家
```

---

## 五、ReAct 行为示例：完整诊断流程

### Layer 0 — 中央编排 Agent

```
[Thought] 收到一份光子晶体波导的 EPO 专利申请。先脱敏。
[Action]  pii_mask(document)
[Obs]     遮蔽 3 处 PII

[Thought] 检索 EPO 对比文献。
[Action]  search_epo_patents(query="光子晶体波导", ipc="G02B 6/12")
[Obs]     找到 8 篇，EP2019876A 高度相关

[Thought] 再查学术文献补充证据。
[Action]  search_academic(query="photonic crystal waveguide bandgap")
[Obs]     找到 12 篇相关论文

[Thought] 信息充分了。启动庭审，交给法官。
[Action]  run_hearing(patent=脱敏文本, prior_art=[EP2019876A...], papers=[...])
[Obs]     法官裁决：创造性成立，授权概率 87%

[Thought] 庭审结束，生成报告。
[Action]  generate_report(verdict=裁决, debate_log=辩论记录)
[Final]   诊断报告已生成。
```

### Layer 1 — 法官 Agent（`run_hearing` 内部）

```
[Thought] 本案涉及光子晶体波导，先从新颖性入手。
[Action]  call_novelty_examiner(patent=文本, prior_art=对比文献)
[Obs]     新颖性审查员：权利要求1的波导结构与EP2019876A相似度>80%

[Thought] 新颖性受到挑战，让律师回应。
[Action]  call_applicant(objection=新颖性意见, patent=文本)
[Obs]     律师：我方引入了"非对称缺陷层"，对比文献完全未披露

[Thought] 律师提出了缺陷层差异。让创造性审查员评估这个差异是否显而易见。
[Action]  call_inventive_step_examiner(
             patent=文本, 
             specific_feature="非对称缺陷层",
             applicant_argument=律师辩护
          )
[Obs]     创造性审查员：该缺陷层的具体气压参数存在描述歧义，无法判断

[Thought] 审查员和律师都无法就这个物理参数达成一致。需要人类专家释明。
[Action]  request_human_expert(
             reason="非对称缺陷层气压参数的物理机制描述歧义",
             context=完整辩论记录
          )
[HITL 挂起] → 等待人类专家释明

--- 专家提交释明后恢复 ---

[Thought] 收到专家释明。让创造性审查员基于新信息重新评估。
[Action]  call_inventive_step_examiner(
             patent=文本,
             expert_clarification=专家释明,
             mode="re_evaluate"
          )
[Obs]     创造性审查员：接受专家释明，确认该特征具有非显而易见性

[Thought] 三个维度审查完成。工业实用性方面本案是标准半导体工艺，快速确认。
[Action]  call_industrial_examiner(patent=文本)
[Obs]     工业实用性审查员：完全满足 Art.57，可在标准晶圆厂实施

[Thought] 所有维度审查完毕，可以做最终裁决。
[Return]  { verdict: "创造性成立", probability: 87%, rationale: "..." }
```

> **注意**：法官自主选择了先问新颖性、再问创造性、最后快速确认工业实用性的策略。面对不同专利，法官可能采用完全不同的审问顺序和轮次。

---

## 六、HITL 人机协同

### 6.1 双层触发点

| 触发层 | 场景 | 触发者 |
|--------|------|--------|
| **L1 法官** | 辩论中出现技术歧义，专家池无法解决 | 法官自主判断后调用 `request_human_expert` |
| **L0 中央** | 整体流程异常（如所有检索无结果） | 中央 Agent 自主判断后触发 |

### 6.2 交互流程

```
法官调用 request_human_expert(reason, context)
    ↓
LangGraph interrupt → 图状态冻结到 Checkpointer
    ↓
SSE 推送 hitl_interrupt → 前端展示暂停卡片
    ↓
人类专家提交释明 → POST /resume
    ↓
图状态恢复 → 法官 ReAct 循环继续（从断点处恢复）
```

### 6.3 独立模式 vs Novoscan 集成模式

| | 独立模式 | Novoscan 集成 |
|---|---|---|
| 暂停 UI | PatentX 自有听证看板 | 复用 `AgenticPauseCard` |
| 恢复路由 | `/api/v1/evaluation/{id}/resume` | `/api/v1/agentic/thread/{id}/resume/stream` |
| 标准动作 | `approve` / `revise` / `abort` | 相同 |

---

## 七、安全与防护

| 机制 | 实现 |
|------|------|
| **S3 物理隔绝** | Presigned URL 直传，24H TTL 硬销毁 |
| **PII 脱敏** | `pii_mask` Tool 在 L0 层拦截，LLM 调用前自动遮蔽 |
| **优雅降级** | 3 分钟 SSE 上限，超时转异步 + 邮件分发 |
| **节流阀** | L0 `max_iterations` 限制总轮次；L1 法官 `max_debate_rounds` 限制辩论轮次 |

---

## 八、可观测性 (Langfuse)

| 观测维度 | 实现 |
|---------|------|
| **L0 ReAct 轨迹** | 中央 Agent 每步 Thought/Action/Obs 全量记录 |
| **L1 庭审轨迹** | 法官子循环的完整辩论链路独立成 Trace |
| **L2 Agent 快照** | 各专精审查员被调用时，内部 Prompt + 输出捕获为 Span |
| **语义异常** | Agent 输出无效 JSON 或拒绝回答 → `Semantic_Parse_Error` 报警 |
| **Token 流速** | TTFT / TPS 追踪，超时前预警 |

---

## 九、技术宪法（四大接口契约）

1. **依赖反转** — 禁止硬编码 LLM SDK，通过 `AiClientProvider` 抽象接口
2. **SSE 解耦** — 实时数据唯一通道为 SSE，JSON Schema 严格规范
3. **JWT 身份** — 不自建用户表，只认 JWT 中的 `user_id`
4. **插件签名** — 对外入口符合 `marketplace_plugins` (execution_mode='builtin')

---

## 十、开发路线图

| 阶段 | 工作 | 产出 |
|------|------|------|
| **1. 专精 Agent 编写** | 4 个 Agent YAML + 专精 Prompt | `novelty_examiner.yaml` 等 |
| **2. Utility Tool 开发** | EPO 检索、PII 脱敏等工具函数 | `tools/patent_*.py` |
| **3. 法官子编排器** | 基于 LangGraph 构建法官 ReAct 子图 | `hearing_graph.py` |
| **4. 中央编排器** | L0 全局 ReAct Agent + Tool 注册 | `orchestrator.py` |
| **5. HITL 双层打通** | L1 interrupt + resume 全链路 | API + 前端 |
| **6. 观测接入** | Langfuse 分层 Trace/Span | 观测面板 |

### 演进路线

```
底座 (当前)                    演进目标
┌─────────────┐              ┌──────────────────┐
│ 固定专家池   │  ──────────► │ spawn_expert      │
│ 4个专精Agent │              │ 法官动态招募专家   │
│             │              │ 质量不足→降级HITL  │
└─────────────┘              └──────────────────┘
```
