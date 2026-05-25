# 废除 3D 星图与恢复原有 UI 设计风格实施计划

## 核心修改逻辑

1.  **废除 3D 特征星图与 CoT 折叠**：在仪表盘中移除 `FeatureStarChart` 和 `CoTExplanation` 的导入与渲染。将页面逻辑切换回最初无星图的 `DiagnosticDashboard.tsx` 页面。
2.  **完全恢复原有设计风格**：在 `App.tsx` 中移除将所有卡片合并合并到同一 `glass-panel` 物理卡片的原地 Morphing 机制及 Gemini 流光呼吸外边框。恢复原始的多个独立浮动卡片通过 `AnimatePresence` `mode="wait"` 的无缝动画切换风格。
3.  **保留后端业务逻辑联调**：保留在 M1 里程碑中开发的“三维定位键专家批注”和“Zustand 与 SSE 状态流对接逻辑”，确保全链路构建与 E2E 验证依然 100% 通过。

## 涉及文件及修改方案

### [Component: Frontend]

#### [MODIFY] [App.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/App.tsx)
*   **回滚外观**：移除外层的合并物理容器 `motion.div` 以及 Gemini 流光边框，让各个卡片独立切换。
*   **回滚控制台**：将 `DiagnosticDashboard` 指向 `./components/DiagnosticDashboard.tsx`（即无星图的版本），而不是 `DiagnosticDashboardNew.tsx`。
*   **业务逻辑维持**：保留 `useStore` Zustand 状态对接。

#### [DELETE] [FeatureStarChart.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/FeatureStarChart.tsx)
*   完全废除此 3D 特征星图物理 Canvas 2D 组件。

#### [DELETE] [CoTExplanation.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/CoTExplanation.tsx)
*   完全废除此思维链折叠白盒大纲组件。

#### [DELETE] [DiagnosticDashboardNew.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/DiagnosticDashboardNew.tsx)
*   完全废除此前包含 3D 星图在内的新控制台临时过渡组件。

## 验证计划

### 自动化验证
*   在 `frontend` 目录下运行 `npm run build` 确保前端完美编译，无任何类型缺失或模块引入错误。
*   运行 `py server/run_test.py` 确保后端全链路集成测试与三维定位批注 Resume 逻辑依然 100% 绿灯。
