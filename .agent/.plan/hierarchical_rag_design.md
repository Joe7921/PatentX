# PatentX 专利多级嵌套 RAG 与多层 Agent 数据交互技术方案

基于与用户的 `/grill-me` 深度对齐，系统确立了以下高级数据利用与 AI 驱动型检索架构方案。

## 1. 核心架构设计 (Hierarchical Parent-Child RAG)

### 1.1 数据入库与切分策略 (Ingestion & Chunking)
对于 EPO 及全球对比专利文件，数据按以下嵌套层级进行处理：
*   **父块 (Parent Chunk)**：
    *   粒度：**整项权利要求 (Claims)**（例如独立权利要求 1，从属权利要求 2-5 组合段落）。
    *   属性：包含完整的法律保护边界及上下文。
*   **子块 (Child Chunk)**：
    *   粒度：**技术特征限制条款 (Technical Limitations)**。通过 LLM 将一项独立权利要求拆解为 3-5 个具体的技术特征片段（例如：“一种用于专利评估的数据网关，其特征在于... [特征A：SSE流式传输]；[特征B：动态断点暂停]”）。
    *   向量化：仅对子块（具体特征片段）进行 Embedding 编码并存入向量数据库，以便进行超细粒度的技术重合度匹配。

### 1.2 检索与召回逻辑 (Parent-Child Recursive Retrieval)
1.  **特征拆解**：用户上传国内专利（CN），L0 编排 Agent 先将其权利要求拆解为多个独立的**国内技术特征子块**。
2.  **子块匹配**：使用国内特征子块的向量，去向量数据库中检索最相似的 EPO 专利特征子块（Top-K）。
3.  **父块拉回**：一旦匹配到某个 EPO 专利的特征子块，数据库根据关联外键，自动召回其**所属的整项权利要求（父块）**。
4.  **组装上下文**：将召回的完整权利要求及其高亮匹配段落，拼装为结构化 Context，输入给 L2 层审查 Agent。

---

## 2. Agent 层级数据流通 (Matrix & Debate)

```
[国内专利输入]
      │
      ▼
 (L0 编排器) ───► [拆解特征 & 向量检索] ───► [拉回 EP 专利父块]
                                                   │
                                                   ▼
                                         (L2 epo_examiner)
                                                   │ (逐案比对)
                                                   ▼
                                        [特征对齐差异矩阵]
                                                   │
                                                   ▼
                                          (L1 patent_judge)
                                                   │ (组织辩论)
                                                   ▼
                                         (L2 patent_applicant)
                                                   │
                                                   ▼
                                         [输出评估决策报告]
```

*   **L2 审查员级 (epo_examiner)**：
    *   输入：国内专利特征、召回的某一个 EP 对比文件权利要求。
    *   任务：进行单案精细化对比，逐一判定国内特征是否被该对比文件披露。
    *   输出：结构化的 **特征对齐矩阵 (Feature Alignment Matrix)**：
        ```json
        {
          "prior_art_id": "EP3812049A1",
          "alignments": [
            {
              "domestic_feature": "特征A: SSE流式状态同步",
              "prior_art_text": "说明书第4段: ...通过Server-Sent Events进行状态同步...",
              "status": "Fully_Disclosed",
              "novelty_impact": "High"
            }
          ]
        }
        ```
*   **L1 法官级 (patent_judge)**：
    *   任务：汇总 L2 提交的多份特征对齐矩阵，识别核心冲突点，组织 `epo_examiner` 与 `patent_applicant`（申请人代理）进行定向辩论，判断是否具有“新颖性”与“创造性”。
*   **L0 决策报告生成**：
    *   收集法官裁决和最终的特征对齐数据，直接渲染为前端的双屏高亮对比看板，并导出 PDF。

## 3. 全局共享黑板上下文管理架构 (Blackboard Context Management)

在多层级、对抗式的 Agent 辩论生命周期中，为了保持 Token 效率并确保专家干预（HITL）时的状态一致性，采用 **全局共享黑板 (Blackboard Pattern)** 架构管理上下文。

### 3.1 核心设计逻辑
*   **Agent 无状态化 (Stateless Agents)**：Layer 2 的专精 Agent（如 `epo_examiner` 和 `patent_applicant`）以及 Layer 1 的 `patent_judge` 本身均不维护独立的会话历史。它们不留存长期会话记忆，避免随着辩论轮数增加导致 Prompt 极速膨胀。
*   **集中式黑板 (Central Blackboard)**：由 Layer 0 维护一个全局唯一的共享状态对象（即 Blackboard）。其数据结构包括：
    1.  `global_eval_id`：评估任务的唯一标识。
    2.  `claim_features`：用户上传的国内专利原始权利要求及拆解后的特征子块列表。
    3.  `feature_alignment_matrices`：各个对比文件的特征对齐矩阵映射结果（由 epo_examiner 写入并不断更新）。
    4.  `expert_annotations`：人类专家在 HITL 介入时输入的修改、批注或裁判倾向信息。
    5.  `debate_logs`：结构化的辩论精炼发言摘要，而非完整对话。
*   **动态 Prompt 组装 (Dynamic Prompt Assembly)**：
    1.  法官 Agent 需要组织辩论或审查员需要比对时，由上层路由根据当前的议程（Agenda），从黑板中提取**最小相关数据子集**。
    2.  例如，当辩论焦点在“特征 A”时，法官 Agent 仅从黑板提取“特征 A”的对齐矩阵及相关的 HITL 批注，拼装为精简的上下文发送给审查员和申请人 Agent，而不发送其余无关特征的数据。

### 3.2 HITL 状态同步机制
*   当系统触发 `hitl_interrupt` 暂停（例如在辩论轮次后或最终决策前），人类专家通过前端 DiagnosticDashboard 进行 Approve/Revise 介入。
*   专家修改的细节（如：“修正对比文件 1 中特征 A 的匹配度为 Partially_Disclosed”）将通过 POST `/resume` 写入全局黑板的 `expert_annotations`。
*   系统恢复运行后，L1 法官 Agent 从黑板读取最新批注，并在组装后续 Prompt 时强制将专家的批注作为“既定法律事实”置顶，使下层 L2 专精 Agent 自动对齐专家的意志。

---

## 4. 待办开发任务 (Task Breakdown)
*   [ ] 设计 `database/schema`，建立 Parent-Child 专利表关联。
*   [ ] 编写 Python 脚本调用 LLM，将 EP 专利的权利要求书自动化拆解为限制特征条款并入库。
*   [ ] 实现 Parent-Child 递归检索算法。
*   [ ] 在 `tools/patent_tools.py` 中，将 Mock 函数升级为真正的向量召回与特征比对逻辑。
*   [ ] 在后端实现全局共享黑板（Blackboard）的数据结构与动态 Prompt 组装逻辑。

