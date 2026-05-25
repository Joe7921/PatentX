# PatentX 前端 UX 动效重塑与决策流还原实施计划（第一步）

本项目的前端 UX 重塑将分步骤进行。在第一步中，我们将聚焦于重构核心交互骨架，将目前割裂的步骤界面重写为**统一的无缝形变（Morphing）物理卡片**，升级为**科技学术蓝绿白玻毛玻璃**视觉风格，并完全还原后端 SSE 下发的 **Blackboard 辩论时间轴与特征对齐矩阵**，将 HITL 专家干预无缝集成进矩阵交互中。

## User Review Required

> [!IMPORTANT]
> 1. **核心文件重写安全**：本计划将直接修改 `frontend/src/` 下的所有核心 TSX/CSS 组件。虽然这是第一步重写，但我们将遵循 Windows 文件修改安全规则，使用精细的修改工具（如 `replace_file_content`），修改完成后使用 `npm run build` 进行编译验证，绝不破坏 Node.js 工具链。
> 2. **后端契约对接**：重塑后的前端主控台将直接消费后端 SSE 下发的 `debate_logs`、`feature_alignment_matrices` 和 `current_step` 等 Blackboard 状态，不再依赖任何硬编码模拟 data。
> 3. **视觉风格确认**：页面将完全换为 Google Gemini 标志性的“蓝紫青”四色融合高斯模糊极光，辅以高清晰度白玻磨砂毛玻璃（Glassmorphism）卡片，字体使用 Google 现代字体，若您不同意该视觉方向，请在审批时指出。

## Proposed Changes

我们将对前端项目的视觉和组件层进行以下重塑：

### 1. 基础设计系统与背景材质

#### [MODIFY] [index.css](file:///d:/Antigravity%20projects/PatentX/frontend/src/index.css)
* 引入 Google Fonts 的 `Outfit` 字体（用于标题与 Agent 徽标）和 `Inter` 字体（用于正文和特征文本）。
* 升级 `.glass-panel` 毛玻璃实用类：使用更低透明度（`bg-white/12`）、高模糊度（`backdrop-blur-xl`）、精细微亮边框（`border border-white/20`）和多重微弱阴影（`shadow-[0_8px_32px_rgba(0,0,0,0.04)]`），营造极致的通透高级感。

#### [MODIFY] [AuroraBackground.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/AuroraBackground.tsx)
* 重写 Canvas 极光背景逻辑：使用三个超大模糊 blob 并在 Canvas 渲染中设置 `globalCompositeOperation = 'screen'` 或 `mix-blend-mode: plus-lighter` 混合模式。
* 使用 Google Gemini 标志性的科技三色：科技蓝（`rgba(7, 142, 250, 0.2)`）、梦幻紫（`rgba(173, 137, 235, 0.2)`）和学术青/绿（`rgba(16, 185, 129, 0.2)`）。
* 为 blob 漂移添加带阻尼的随机曲线动效，消除原本机械旋转造成的土气感，保证在各种分辨率下背景如同生命体般自然流转。

---

### 2. 交互骨架重构（统一 Morphing 物理容器）

#### [MODIFY] [App.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/App.tsx)
* **架构重塑**：废除原本将四个步骤卡片分开销毁渲染的设计，重构为由一个统一的 `motion.div` 外层容器包裹。
* 使用 `framer-motion` 的 `layout` 属性绑定该容器。当内部状态在 `UPLOAD` -> `THINKING` -> `DASHBOARD` 之间推移时，容器将通过物理弹簧（Spring Easing: `stiffness: 160, damping: 24`）自动进行宽高伸缩形变（Morphing Transition）。
* 当检测到系统处于 `THINKING` 思考状态或 `PAUSED` 挂起状态时，外层容器边缘激活 Gemini 呼吸流光边框动画（Glow Border），作为 AI 能动性的视觉反馈。

---

### 3. 子状态卡片与决策流信息还原

#### [MODIFY] [UploadHub.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/UploadHub.tsx)
* 重塑为精美的拖拽上传控制中心：添加 `onDragOver` / `onDragLeave` / `onDrop` 事件，支持真正的文件拖拽判定，拖拽时展现极光虚线呼吸框。
* 优化文字排版，将普通蓝色按钮改用白玻高光圆角渐变按钮，辅以滑过时的微发光粒子动画。

#### [MODIFY] [ThinkingIndicator.tsx](file:///d:/Antigravity%20projects/Patent%20X/frontend/src/components/ThinkingIndicator.tsx)
* 抛弃原有的菊花转圈 Loader。
* 重构为具有 Gemini 特色的流光渐变呼吸波浪，波浪高度与流动速度根据当前 active 的分析节点（如 `parsing` 快速，`retrieval` 稳健，`debating` 激荡）做动态呼吸频率控制。

#### [MODIFY] [DiagnosticDashboard.tsx](file:///d:/Antigravity%20projects/PatentX/frontend/src/components/DiagnosticDashboard.tsx)
* **核心功能重构**：将诊断主控台重写为并排双面板布局：
  * **左侧：多 Agent 辩论时间轴**：流式监听 SSE 发送的 `debate_logs`，以对话泡泡呈现辩论过程。在气泡旁优雅标出发言 Agent 身份（法官、审查员等）以及绑定的 LLM 模型徽标（如 `GPT-4` / `Claude`）。每条新日志涌现时，采用平滑的 `fade-in-up` 动效渐进涌现。
  * **右侧：多维对齐决策矩阵**：完全从黑板数据中提取 claims 特征与 EPO 检索出的专利进行交叉对齐。绘制为响应式的网格比对矩阵。冲突单元格状态使用微光渐变色块标明：
    * `Fully_Disclosed`（新颖性冲突）：高亮警告红微光（`bg-red-500/10 text-red-600 border border-red-500/20`）
    * `Partially_Disclosed`（创造性微冲突）：黄色微光
    * `Not_Disclosed`（安全通过）：绿色微光
* **HITL 专家挂起干预合并**：
  * 废除原本突兀的 `AgenticPauseCard`。
  * 当 SSE 收到 `hitl_interrupt` 信号且 `workflowState === 'PAUSED'` 时，主控台边缘亮起深呼吸流光边框，提醒专家介入。
  * 矩阵中发生 `Fully_Disclosed` 冲突的单元格激活波动呼吸发光。人类专家只需点击该单元格，就会直接在单元格原地 Morphing 展开一个微型批注输入卡片，允许专家对该冲突特征输入指导意见（如修改 claims 或直接忽略），点击 Approve/Revise 按钮直接向后端 `/api/v1/evaluation/{id}/resume` 发送状态恢复请求，页面随即收缩并恢复流式运转。

---

## Verification Plan

### 1. 自动编译与构建验证
* 修改完每个组件后，在 `frontend` 目录下运行 `npm run build`，确保 TypeScript 类型检查无误，Vite 构建打包成功。

### 2. 交互与功能验证
* 启动后端 `python server/main.py` 并启动前端开发服务器 `npm run dev`。
* 打开浏览器访问前端控制台：
  1. 验证文件拖拽上传交互。
  2. 启动 mock 分析，观察卡片是否以流畅的 Spring Morphing 动效变长变大过渡至 Thinking 状态。
  3. 观察 Canvas 极光背景漂移是否自然，Thinking 时流光边框是否正常呼吸。
  4. 进入 Dashboard 状态后，观察 SSE 数据流发出的 `debate_logs` 和对齐矩阵是否成功流式追加 and 渲染。
  5. 挂起状态下，验证冲突单元格是否高亮发光，点击后是否能原地展开输入框、输入批注并提交，成功 Resume 整个管线。
