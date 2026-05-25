# 审计实施计划 (Milestone M5 Integrity Audit Plan)

本计划旨在独立验证 PatentX UI/UX 全景重塑里程碑 M5 的工作成果真实性、完整性以及前端项目的构建正确性。

## 审计目标
1. 验证 Canvas 3D 星图 (`PatentStarChart.tsx`, `FeatureStarChart.tsx`) 是否为真实的 3D 数学投影、旋转矩阵与粒子物理扩散模拟，非静态平面图。
2. 验证 CoT 思维链折叠组件 (`CoTExplanation.tsx`) 的 Token 消耗与大纲步骤是否为自适应数据流，非静态硬编码。
3. 验证主诊断看板 (`DiagnosticDashboardNew.tsx`) 与底层 SSE 数据流/专家批注是否连贯，无作弊逻辑或硬编码。
4. 验证前端项目构建 (`npm run build`) 100% 编译成功，无 TypeScript/类型错误。
5. 检查是否合规地未使用 Three.js 等三维库。
6. 出具 Verdict 审计报告并归档到 `.agents/auditor_m5/handoff.md`。

## 验证步骤与检查项

### 步骤 1：源代码静态与动态分析 (已完成)
- 检查星图绘制组件中的 3D 转换矩阵三角函数与透视投影计算。
- 检查星图粒子喷射系统的 3D 世界坐标系更新、速度阻尼衰减以及 Painter 景深排序算法。
- 检查 CoT 推理步骤和 Token 消耗是否根据 `contentSeed` 作出确定性哈希和自适应正则表达式判定。
- 确认 `package.json` 及源码中均未引入 three.js 等三维渲染库。

### 步骤 2：项目构建验证 (已完成)
- 在 `frontend` 目录下运行 `npm run build`。
- 验证打包输出结果，确保打包过程 100% 成功。

### 步骤 3：审计结论裁定与报告输出 (进行中)
- 出具 Verdict 结论（**CLEAN** / **INTEGRITY VIOLATION**）。
- 编写并写入 `.agents/auditor_m5/handoff.md`，提供完整证据链与数学换算细节。
