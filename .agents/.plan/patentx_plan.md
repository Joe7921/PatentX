# PatentX 计划规划 (Plan)

## 目标
实现 PatentX 项目，基于动态 Block-Driven Architecture，严格遵循“分层嵌套式Agentic workflow”（Hierarchical Nested Agent-as-Tool Workflow）。

## 任务拆解
1. **阶段一：工具开发 (M1)**
   - 在 `tools/` 目录下创建 mock 工具函数。
   - 包含专利/学术检索功能，并在代码中用注释明确标示为 mock。
   - 封装 Layer 2 Agent 作为 Tool 供 Layer 1 调用。

2. **阶段二：Agent 与 Interaction 模块开发 (M2)**
   - 创建 `app/agents/_custom/` 下的 YAML 配置文件：
     - `patent_judge.yaml` (Layer 1)
     - `epo_examiner.yaml` (Layer 2)
     - `patent_applicant.yaml` (Layer 2)
     - `pii_filter.yaml` (Transform Layer)
   - 创建 `app/interactions/_custom/` 下的 YAML 配置文件：
     - `adversarial_debate.yaml` (L1/L2 嵌套辩论循环)

3. **阶段三：管道编排 (M3)**
   - 创建 `patentx_pipeline.json`。
   - 实现 Layer 0 全局路由、嵌套 Sub-graph 逻辑以及 HITL (Human-in-the-loop) 断点。

4. **阶段四：验证脚本 (M4)**
   - 创建 `verify_config.py` 脚本，用于验证 YAML 语法、JSON 语法，以及节点依赖关系的完整性。

## 执行策略
使用 Orchestrator -> Worker 模式分步实现上述阶段。
