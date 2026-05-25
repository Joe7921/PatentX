# PatentX 前端全景动效重构与流式决策还原方案 (v2) - 已批准执行

本方案已获得用户批准，正式进入执行阶段。本重构案将全量落实 M1 至 M6 包含“依赖审计”、“物理容器形变”、“欢迎向导/焦点锁定”、“HITL粒子反馈”、“3D星图（Canvas 2D）”在内的六大里程碑，并全量纳入三项高价值交互与状态容灾建议。

## 最终确定的技术决策 (Confirmed Decisions)

1. **3D 专利特征星图选型**：采用**【选项一：轻量化 Native Canvas 2D 物理拟真】**。
   * *实现*：利用原生 2D Canvas 手写简易的 3D-to-2D 旋转与投影转换算法，模拟星体发光与连线流光。
   * *优势*：0 新增外部包体积依赖，性能极佳，彻底避免 WebGL 的硬件白屏与 GPU 兼容风险。
2. **优化建议全部纳入**：
   * 状态管理与连接容灾 (Zustand/React Context)
   * 物理回弹拖拽阻尼反馈 (framer-motion tilt & spring bounce)
   * 单元格批注多人防冲突锁 (Blackboard Read-Write Lock)

---

## 最终重构里程碑计划 (Milestones & Tasks)

### M1. 依赖审计与后端 SSE 适配
* **任务**：
  * 审计前端构建工具链与 package.json。
  * 修复现有批注定位键的冲突漏洞。将原有的 `prior_art_id_prior_art_feature_id` 定位键重构为三维联合键 `domestic_feature_id_prior_art_id_prior_art_feature_id`，以支持多个国内 claims 特征与同一对比专利特征的精确定位，防止批注覆盖。
  * 在后端 `main.py` 和 `blackboard.py` 扩展对应的 `/resume` 数据结构支持，向前端下发联合锁。

### M2. 统一物理容器与四色极光背景
* **任务**：
  * 合并 `UploadHub`、`ThinkingIndicator`、`AgenticPauseCard` 和 `DiagnosticDashboard` 至单一 `WorkspaceCard` 容器。
  * 使用 `framer-motion` 的 `layout` 属性与 Spring 物理弹簧算法（`stiffness: 160, damping: 24`）控制卡片状态 Morphing，解决卡片高度瞬间跳跃和闪烁瓶颈。
  * 支持由 `framer-motion` 驱动的轻微物理倾斜（Tilt）与弹性惯性回弹手势。
  * 开发 `AuroraBackground.tsx`：Canvas GPU 漫反射蓝、紫、青三色极光，以及运行/挂起时的卡片流光边框（Gemini Glow）。

### M3. 欢迎向导与注意力焦点锁定
* **任务**：
  * 注入 “AI 交互式欢迎向导”（流光打字机显示平台定位与三步流程指引，拖拽文件时卡片平滑坍塌折叠消失）。
  * 全量对接后端 `/api/v1/analyze/stream` SSE 数据源。
  * 引入 Zustand / React Context 状态管理与连接容灾：当用户刷新页面或连接意外闪断时，系统能根据 `eval_id` 自动从黑板恢复当前步骤、辩论历史与矩阵数据。
  * 实现运行期注意力聚焦：当前分析的 claims 特征行与左侧 Agent 辩论气泡同步发光，突出当前 AI 活动点。

### M4. 挂起期全局暗淡与原地单元格批注反馈
* **任务**：
  * 挂起时全局非冲突面板半透明暗淡（认知负荷管理）。
  * 冲突的对齐矩阵单元格波纹呼吸发光，点击原地 Morphing 展开微型批注框。
  * 单元格批注的多人协作防冲突锁定（Blackboard 读写锁）：当某位专家正在编辑某冲突单元格时，通过 SSE 广播锁定该输入状态，防止多人同时覆盖修改。
  * 注入粒子抛物线飞入吸附动画：提交批注后，文字转化为能量微光粒子飞入并吸附在单元格上，状态变为青色“专家已批注”，面板渐变解冻（300ms），系统 Resume。

### M5. 3D 特征星图与 CoT 折叠（分步二期）
* **任务**：
  * 基于原生 Canvas 2D 投射专利 claims 星云。国内专利为核心恒星，外围为现有技术小行星，滚动连线表达冲突。支持 3D-to-2D 旋转拖拽与粒子扩散物理动效。
  * 实现 Agent 发言气泡原地 Morphing 展开大模型底层的 CoT 推理思维链大纲与实时 token 消耗预算（GPT-4 / Claude 等），增强“白盒可信度”。

### M6. 全链路构建与 E2E 验证
* **任务**：
  * 编译检查（vite build），确保零类型错误与警告。
  * E2E 全链路交互走通与性能审计（60fps 极光运行）。
