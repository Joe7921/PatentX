## 2026-05-23T15:22:17Z
请执行 PatentX 前端 UI/UX 全景重塑项目的全局 Forensic Integrity 审计。
你的工作目录应该设定为 `d:\Antigravity projects\PatentX\.agents\victory_auditor`（请在你运行后创建并作为你的工作目录）。

你的审计工作必须涵盖：
1. **真实性验证**：审查整个 PatentX 项目所有修改的代码（包括 M1-M5 新增和重构的前后端代码），确保所有功能（Zustand 全局状态、Canvas 2D 极光背景、物理容器、欢迎向导、注意力高亮、批注粒子反馈、3D 专利特征星图、CoT 面板折叠等）全部为真实、有效实现，**严禁任何硬编码测试结果、虚假响应、假数据直接返回或后门**。
2. **构建与集成运行**：
   - 切换到 `frontend` 目录运行 `npm run build`，确认前端构建 100% 成功，零类型 and 打包错误。
   - 切换到 `server` 目录运行后端 E2E 集成测试 `py run_test.py`，确认测试 100% 通过，并确实包含对三维联合定位键、LLM 自动 Fallback 降级预警、TokenBudget 滑动窗口截断以及 Resume 介入后大模型第二轮辩论决策注入（重估概率 0.95）的真实断言。
3. **输出要求**：
   - 在你的工作目录下输出详细审计报告 `audit_report.md`，并在其中给出最终判定 Verdict：必须明确是 **CLEAN** 还是 **VIOLATION**。如果发现任何作弊行为，必须如实报告。
   - 编写 `handoff.md`，完成后向我（Orchestrator v2，conversation ID: 6f6ddd56-c7ea-4fcf-b36f-3cdeee139a5c）发送消息报告完成及审计结果。
4. **语言约束**：审计过程中的工作、回复、代码注释和任务说明请使用【简体中文】。
