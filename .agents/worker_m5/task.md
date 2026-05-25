# Milestone M5: 3D 特征星图与 CoT 折叠

## 任务目标
实现 PatentX UI/UX 全景重塑的 Milestone 5 交互与视觉图化功能：
1. **[x] 手写 3D 专利特征星图投影 (Canvas 2D)**:
   - 在 `DiagnosticDashboardNew.tsx` 的核心布局区域，使用原生 HTML5 Canvas 2D 绘制一个精美的 3D 特征星系。
   - **架构设计**：
     - 中心有一个旋转发光的大恒星，代表“国内专利 (Domestic Patent)”。
     - 周围环绕着若干个行星，代表检索到的现有技术文献（如 D1, D2 等）。
     - 行星外层有卫星绕行，代表各文献的具体对比特征节点。
     - 节点之间绘制带有流星动效的连线（流光连线）。
     - 遇到新颖性冲突（`Fully_Disclosed`）的节点在提及或挂起时显示为红色，并持续产生向外扩散的微小暗红/粉色粉尘粒子。
   - **3D 旋转与投影数学**：
     - 手写三维旋转矩阵，将三维坐标 `(x, y, z)` 进行旋转变换。
     - 采用透视投影公式：`x_proj = centerX + x * focalLength / (z + zOffset)`。
     - 节点绘制半径与透明度随 `z` 坐标深浅发生变化，提供强烈的空间立体感。
     - 增加拖拽交互与阻尼衰减惯性自转，允许拖拽旋转星云。
2. **[x] Agent CoT 折叠思维链气泡**:
   - 在左侧辩论气泡中，增加一个“思维链 (CoT)”展开按钮。
   - 点击时，在气泡内部原地 Morphing 展开一个微透明暗色折叠框，展示：
     - 该智能体底层三步思维推理逻辑（如“限制特征相似度映射计算”、“EPO 审查基准 A54(2) 冲突阈值核验”等）。
     - 实时大模型 Token 消耗及预算统计（`Prompt Tokens: 2,345`, `Completion Tokens: 512`, `Total Cost: $0.0456`，使用 `font-mono`）。
   - 折叠/展开采用 Framer Motion 的 `AnimatePresence` 和 `layout` 属性驱动。
3. **[x] 更新项目里程碑状态文档**:
   - 修改项目根目录下的 `PROJECT.md`，将 Milestone M5 状态更新为 `DONE`。
4. **[x] 编译与构建验证**:
   - 在 `frontend` 目录运行 `npm run build`，整个前端项目编译打包 100% 成功，零错误、零警告。

