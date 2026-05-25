## 2026-05-23T13:25:25Z
请执行 PatentX UI/UX 全景重塑里程碑 M2：统一物理容器与极光背景。

具体任务：
1. **统一全局状态管理**：使用 `zustand` 库（已在 M1 中作为依赖声明）重塑前端状态机制。设计一个全局 Zustand store，负责管理 SSE 监听连接、黑板（Blackboard）数据，以及根据 SSE 的数据流（如 `node_start`、`hitl_interrupt`、`completed` 事件）来驱动当前的渲染步骤 `step`。实现 SSE 连接的断线容灾机制，支持自动重连。
2. **重构主 Workspace 卡片容器**：
   - 在 `frontend/src/App.tsx` 中，重构卡片布局。废弃组件级的条件渲染和 `AnimatePresence mode="wait"` 的销毁逻辑，改为在顶层使用一个统一的物理卡片外层容器：`<motion.div layout transition={{ type: "spring", stiffness: 260, damping: 26 }} ...>`。
   - 内部各阶段视图（Upload、Thinking、Paused、Dashboard）通过 `<AnimatePresence mode="popLayout">` 配合轻量淡入淡出和微距滑入效果进行切换。保证在状态变化时，外层容器可以弹性地在原地 Morphing 拉伸/收缩。
3. **重构极光背景 (`AuroraBackground.tsx`)**：
   - 采用 HTML5 Canvas 2D 结合 `mix-blend-mode`（如 `screen` / `plus-lighter`），渲染科技蓝、梦幻紫、学术青三色交织的漫反射极光。
   - 颜色斑块（blob）的运动轨迹必须是带物理阻尼的无序曲线漂移，提供 60 FPS 的流畅度且几乎不占用 CPU，严禁使用简单机械的平移或高开销的每帧像素级高斯重绘。
4. **引入毛玻璃（Glassmorphism）与 Gemini Glow 呼吸流光边框**：
   - 为主 Workspace 卡片配置极致通透的毛玻璃材质（如 `backdrop-blur-lg border border-white/20 bg-white/40 shadow-2xl` 等），并引入双重柔和阴影。
   - 当 analysis 处于 Thinking 态或 Paused 挂起态时，卡片边缘渐显亮起 Gemini Glow（呼吸流光边框效果）。
5. **引入现代设计字体**：
   - 全局加载 Google Outfit (标题) 与 Inter (正文) 字体，并在 Tailwind CSS 或 CSS 全局变量中定义以优化文本排版。
6. **运行构建验证**：
   - 在 `frontend` 目录下运行 `npm run build` 命令，验证重构的代码在打包时没有任何 TypeScript 类型报错或语法报错。
7. 将你修改的文件、具体设计、前端构建命令与结果，详细写入你的工作目录（`.agents/worker_m2/`）下的 `handoff.md` 中。
8. **语言规则**：你必须始终使用【简体中文】编写代码注释、提交说明和 handoff。
