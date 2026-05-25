# Google Gemini & I/O 动效重塑计划 (工作区持久化版)

## 设计方向共识
*   **定位**：重构当前 `PatentX` 的 `frontend`，直接注入极光动效（Gemini Aurora）与物理级步骤转场（I/O Morphing Card）。
*   **配色**：科技学术蓝绿配色（漫反射浅色版），配浅色磨砂玻璃态布局。
*   **库依赖**：引入 `framer-motion` 实现高品质物理卡片过渡。

## 详细任务拆解
1.  **修复 `DiagnosticDashboard.tsx` 语法错误**：合并清理重复 of state、拼写和未闭合大括号。
2.  **开发 `AuroraCanvas.tsx`**：使用 HTML5 Canvas 绘制轻量级波动极光（浅色漫反射）。
3.  **重构 UI 组件**：
    *   `UploadHub` (拖拽上传，极光呼吸边框)
    *   `ThinkingIndicator` (AI 思考态，极光波动)
    *   `AgenticPauseCard` (人工暂停卡片，白玻磨砂拉伸动画)
4.  **改写 `DiagnosticDashboard` 主布局**：改为时间轴 Morphing 步骤流，从上一步无缝 morphing 融合成下一步。
5.  **配置全局 CSS**：升级 `index.css`，配置白玻毛玻璃材质与浅色背景（Zinc-50）。

