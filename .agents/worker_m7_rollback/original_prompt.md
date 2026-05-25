## 2026-05-23T15:40:00Z

请执行 PatentX 前端 UI/UX 项目里程碑 M7：废除 3D 特征星图与恢复原有 UI 设计风格。

你的工作目录将设定在 `d:\Antigravity projects\PatentX\.agents\worker_m7_rollback`（请在执行后创建）。

具体开发与回滚任务如下：
1. **修改 `frontend/src/App.tsx`**：
   - 回滚外观：移除外层包裹各面板的统一物理卡片容器 `<motion.div layout ...>` 及其 Gemini 流光呼吸外边框。
   - 恢复多卡片独立切换：恢复原本由多个独立浮动卡片（`UploadHub`、`ThinkingIndicator`、`AgenticPauseCard`、`DiagnosticDashboard`）通过 `<AnimatePresence mode="wait">` 控制销毁和切换的动画布局。
   - 将 `DiagnosticDashboard` 组件的引入指向原始的无星图组件 `./components/DiagnosticDashboard`，完全废除引入 and 使用 `DiagnosticDashboardNew`。
   - 确保 `useStore` Zustand 状态对接的完整业务逻辑予以保留。
2. **删除冗余前端文件**：
   - 删除 `frontend/src/components/FeatureStarChart.tsx` (3D 特征星图)
   - 删除 `frontend/src/components/CoTExplanation.tsx` (思维链折叠面板)
   - 删除 `frontend/src/components/DiagnosticDashboardNew.tsx` (新版集成控制台)
   - 注意：可以使用 PowerShell 的 `Remove-Item` 命令去安全删除它们。
3. **运行构建与测试验证**：
   - 切换到 `frontend` 目录运行：`npm run build`，确保前端编译 100% 成功，无任何 TypeScript 类型检查错误或打包警告。
   - 切换到 `server` 目录运行：`py run_test.py`，确保后端全链路集成测试 100% 通过（验证专家 Resume 介入后的三维批注注入、第二轮辩论与授权率 95.0% 重算逻辑仍然完好并能够正常通过断言）。
4. **输出交接文档**：
   - 将你修改与删除的文件、具体重构设计、前端构建与后端测试验证命令及结果，详细写入你的工作目录下的 `handoff.md` 中。
5. **语言约束**：你必须始终使用【简体中文】编写代码注释、提交说明和 handoff。
