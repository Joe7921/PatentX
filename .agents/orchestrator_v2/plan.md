# UX 重塑与回滚/远程部署实施计划 (PatentX Plan)

## 里程碑计划

### M1: 依赖审计与后端 SSE 适配
- 后端批注定位重构为三维联合键 `f"{domestic_feature_id}_{prior_art_id}_{prior_art_feature['id']}"`。
- 修改 `/resume` 端点以接收并写入 Blackboard 数据。
- 后端 Round 2 多 Agent 辩论决策注入。
- 前端添加 `zustand` 状态管理。

### M2: 统一物理容器与极光背景
- 使用 Zustand 规范全局状态并处理断线自动重连。
- 替换为单个物理卡片容器（Framer Motion 弹性形变过渡）。
- 手写极光背景 Canvas（多色混色和物理阻尼无序漂移轨迹）。
- 实现 Thinking/Paused 状态下的 Gemini Glow 流流光流边框。

### M3: 欢迎向导与注意力焦点锁定
- 欢迎向导流光打字机显示以及三步新手卡片。
- 当输入/拖拽时向新手卡片平滑折叠塌陷。
- 流式渲染多 Agent 嵌套辩论气泡（大模型标签）。
- SSE 动态高亮发光锁定决策矩阵行与辩论气泡。

### M4: 挂起暗淡与单元格批注粒子反馈
- 挂起状态（hitl_interrupt/PAUSED）下全场暗淡，仅高亮冲突行。
- 单元格呼吸发光，点击展开微型批注输入卡片。
- 提交 Resume 时，专家批注化为微光能量粒子抛物线飞入吸附。

### M5: 3D 特征星图与 CoT 折叠
- Canvas 原生 3D-to-2D 旋转投影星云绘制（国内专利恒星、现有技术行星）。
- 行体流光连线、冲突行星变红并扩散粒子。
- 点击发言气泡展开 CoT 思维链大纲与实时 token 消耗预算。

### M6: 全链路构建与 E2E 验证
- 启动正式 FastAPI/Uvicorn E2E 集成测试，验证 95.0% 概率重算与 token 滑动窗口。
- 前端 `npm run build` 100% 编译通过。

### M7: 废除 3D 星图与恢复原有风格 (回滚)
- 废弃 3D 星图与 CoT 折叠。
- 恢复 App.tsx 为各步骤卡片独立浮动切换。
- **物理删除** 冗余前端文件 `FeatureStarChart.tsx`、`CoTExplanation.tsx`、`DiagnosticDashboardNew.tsx`，后续在结项复核阶段通过 Python `os.remove` 彻底物理清除遗留 `PatentStarChart.tsx` 3D 文件。
- 前后端重新编译、测试与 Forensic 审计 100% 通过。

### M8: iPhone 远程 Web 控制台部署
- Scratch 目录配置 Guacamole 免数据库容器以及 WebSSH 安全凭证 user-mapping。
- 编写一键自适应 IP 监测的 `start-webssh.ps1` and 终端控制 `start-terminal.ps1`。
- 提供 iPhone Safari 免客户端连接与 Vite host 本地发布说明。
