## 2026-05-23T16:01:10Z
【任务描述】
你被派生为 `victory_auditor_m7`（类型：`teamwork_preview_auditor`），负责对 M7 里程碑（废除 3D 特征星图与恢复原有 UI 设计风格）后的全局状态执行 Forensic Audit，以确保系统的真实性与完整性。

你的工作目录是 `d:\Antigravity projects\PatentX\.agents\victory_auditor_m7`。

【审计重点】
1. **清理验证**：
   - 验证 `frontend/src/components` 下是否已物理删除 `FeatureStarChart.tsx`、`CoTExplanation.tsx`、`DiagnosticDashboardNew.tsx`。
   - 检查全局代码中是否无任何地方引用这些已被废弃的组件。
2. **UI 风格回滚验证**：
   - 检查 `frontend/src/App.tsx` 确已恢复多卡片独立浮动切换布局，看板指向 `DiagnosticDashboard` 且没有包含 any 3D 专利星图或 CoT 折叠相关的特征。
3. **真实性与合规性检查**：
   - 验证后端集成测试和前端打包中是否存在硬编码结果、特设 of backdoor 逻辑、fabrication 行为或任何欺骗手段（确保 Verdict 为 CLEAN）。
4. **编译与全链路测试实际运行**：
   - 在 `frontend` 目录运行 `npm run build` 验证前端打包输出是否无 TS 错误或警告。
   - 在 `server` 目录运行 `py run_test.py` 验证后端集成测试是否全部通过（包含 Fallback 降级日志、Token Budget 截断检测、第二轮辩论注入以及授权率重算至 0.95）。
5. **审计报告输出**：
   - 实时更新 `progress.md` 记录进程。
   - 完成后，在你的工作目录中输出最终审计报告 `audit_report.md`，并在 handoff.md 或消息中明确输出审计评级 Verdict (CLEAN / VIOLATION)。

【完成标准】
- 完成上述所有审计并产出 `audit_report.md` 和 `handoff.md`。
- 给出清晰的审计结论 Verdict。
