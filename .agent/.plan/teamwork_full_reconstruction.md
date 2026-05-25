# Teamwork Project Prompt — Draft

> Status: Step 9 — Ready for launch — awaiting user approval
> Goal: Craft prompt → get user approval → delegate to teamwork_preview

全面重塑 PatentX 前端 UI/UX 交互与视觉效果，构建一个符合 Google Gemini 呼吸极光、Google I/O Container Transform 动效与共享 Blackboard 架构的智能 Agentic Workflow 诊断控制台，并分步骤实现从核心骨架到高级 3D 专利星图的完整重构。特别注重用户精力管理、新手指引与高度连贯的人机双向操作反馈。

Working directory: d:/Antigravity projects/PatentX/frontend
Integrity mode: development

---

## Requirements

### R1. 统一 Workspace 物理容器与弹簧 Morphing 过渡
* **容器形变**：将现有的多个散乱步骤卡片（UploadHub、ThinkingIndicator、AgenticPauseCard、Dashboard）合并为同一个物理卡片容器。使用 `framer-motion` 的 `layout` 以及物理弹簧参数（Spring: Stiffness & Damping）控制容器大小与边界，在状态切换时实现卡片容器在原地的无缝形变收缩与拉伸。
* **渐变过渡**：容器内部元素在卡片形状改变时，伴随容器的拉伸流畅淡入/淡出与微距滑入（Fade & Slide），避免硬性的条件销毁或高度跳跃闪烁。

### R2. 谷歌级视觉材质与四色漫反射极光背景
* **白玻磨砂毛玻璃**：配置极致纯净的 Glassmorphism 材质样式。背景采用极低不透明度，配合强高斯模糊、极细白色高光渐变边框和双重超柔和投影，营造轻盈通透的视觉层次。
* **漫反射极光背景**：重构 `AuroraBackground.tsx`。使用原生 Canvas 结合 `mix-blend-mode`（如 `screen` / `plus-lighter`），渲染科技蓝、梦幻紫、学术青三色交织的漫反射背景。blob 漂移需带有阻尼的无序物理曲线，消除土气的简单机械位移。
* **智能呼吸流光**：在 AI 处于分析（Thinking）或等待干预（Paused）时，工作台卡片边缘亮起 Gemini Glow 呼吸流光边框，动态隐喻 AI 能量运转状态。
* **现代字体**：全局采用 Google 现代设计字体（标题 Outfit，正文 Inter），优化文字排版与对比。

### R3. AI 交互式欢迎向导与新手指引（认知负荷管理）
* **定位打字机**：用户首次进入或处于 IDLE 状态时，Workspace 核心卡片表面以流光打字机效果渐显平台一句话核心定位：“基于多 Agent 嵌套辩论的欧洲专利局 EPO 诊断与特征对齐评估系统”。
* **三步指引**：卡片下方平滑 Morphing 展开三个极简的流程指示卡片（①拖入文档或输入 Claim -> ②观察 Agent 推理辩论与黑板特征矩阵 -> ③必要时介入批注冲突并一键 Resume），帮助新手用户瞬间建立心智模型。当用户开始拖拽文件或输入时，指引卡片自动收缩消失。

### R4. 运行期注意力聚焦与 AI 活动流焦点锁定（精力管理）
* **多 Agent 辩论流**：在 Dashboard 中流式消费 `/api/v1/analyze/stream` SSE 的 `debate_logs`，以对话泡泡形式流式向上推移渲染。标明发言 Agent 身份（法官、审查员等）以及对应的物理大模型标签（如 GPT-4 / Claude 等）。
* **对齐决策矩阵**：右侧展示国内专利特征与 EPO 现有技术的对齐矩阵，单元格对齐状态采用彩色微光小标签精致呈现。
* **焦点同步锁定**：分析运行时，AI 正在分析哪个特征（或由哪个 Agent 正在发言），决策矩阵中的对应特征行（或左侧辩论气泡）将同步发光，通过高亮锁定使用户的注意力始终凝聚在活动点上，避免面对大范围表格时感到迷茫。

### R5. 挂起期全局暗淡与交互式单元格级 HITL 批注
* **全局遮罩暗淡**：当收到 `hitl_interrupt` 信号且状态挂起时，主控台除冲突特征与输入卡片外，其他干扰面板全部半透明暗淡（Dampen），将用户精力强制收窄。
* **冲突单元格呼吸**：矩阵中发生新颖性冲突（`Fully_Disclosed`）的单元格开始做波纹呼吸发光。用户直接点击该发光单元格，即在原地 Morphing 展开一个微型的批注卡片，允许专家输入修正意见。
* **粒子注入双向反馈**：专家点击 Resume 按钮后，输入的文字批注化作一颗“微光能量粒子”，从批注框中以抛物线轨迹流畅地飞入并吸附在对应的对齐矩阵单元格上，单元格状态标签瞬间 Morphing 改变为亮青色的“专家已批注”标签。接着，输入卡片物理收缩，全局面板渐变解冻亮起，辩论轴流式追加“专家指令已注入”并继续流动，实现完美的手势与动画连贯。

### R6. 高级智能特征星图与思维链折叠（分步二期）
* **3D 专利特征星图投影**：在 Dashboard 核心区域利用 Canvas 或 3D 渲染库呈现专利特征星云。国内专利为核心恒星，检索到的多份现有技术为外围小行星。辩论时在星体节点间流动流光连线，冲突时行星变红并产生粒子扩散，把复杂的条款对比图形化。
* **Agent COT 折叠思维气泡**：支持点击辩论轴中 Agent 发言，原地 Morphing 展开大模型底层的 CoT 推理思维链大纲与实时 token 消耗预算，增强系统的“白盒可信度”。

---

## Acceptance Criteria

### 1. 物理动效与过渡
- [ ] 卡片容器在 Upload、Thinking、Dashboard/Paused 状态切换时的 Morphing 形变绝对平滑，卡片外圈阴影与边框同步变形，无任何高度跳闪、闪烁或错位。
- [ ] 极光背景 Canvas 在所有主流分辨率下帧率达到 60fps（或适配显示器最高刷新率），CPU 占用极低，无由于 canvas 重绘导致的 UI 渲染阻塞。
- [ ] 首次进入时的“打字机流光向导”渲染位置及字体缩放正确，拖拽文件时卡片向内坍塌收缩的动效无延迟。
- [ ] HITL 专家批注提交时，“微光粒子”飞入吸附动画轨迹连贯，吸附瞬间表格状态改变及全局暗淡解冻（渐变动画耗时 300ms-400ms）过程顺畅，无界面卡顿。

### 2. 状态机制与数据一致性
- [ ] 对接后端 SSE 接口，辩论日志和矩阵内容完全与当前 evaluation 的 Blackboard 实时数据吻合，未发生丢包、多重追加或文字截断。
- [ ] 单元格级 HITL 触发行星高亮或矩阵发光无误，批注框展开不影响周边布局，点击 Resume 后能顺利让后台继续运转。
- [ ] 项目在 `frontend` 运行 `npm run build` 构建编译零错误、零警告。
