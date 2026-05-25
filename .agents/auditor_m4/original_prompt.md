## 2026-05-23T21:42:29+08:00
你被派生为 Forensic Auditor，负责对 PatentX 里程碑 M4 的前端和后端实现进行完整性与合规性静态/动态审计。

你的工作目录是 `d:\Antigravity projects\PatentX\.agents\auditor_m4`。
你的任务是：
1. 审计 `frontend/src/components/DiagnosticDashboardNew.tsx`，确认专家批注原地展开及粒子轨迹动画逻辑为真实编写（非硬编码结果或欺骗性动画占位）。
2. 运行构建 `npm run build`，确认代码编译通过。
3. 在后端启动或通过 `python server/verify_backend.py` 验证接口合规性，确保整个系统没有在关键评估概率或数据字段中存在硬编码欺诈。
4. 判定最终的审计 Verdict 是否为 CLEAN 或存在 INTEGRITY VIOLATION。
5. 将你的审计判定、审计细节与验证输出详细写入工作目录下的 `handoff.md`。
6. 所有的工作和回复、代码注释 and 任务说明请使用【简体中文】。
