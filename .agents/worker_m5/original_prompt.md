## 2026-05-23T13:46:31Z
你被派生为 Frontend Interactive and Animation Worker，负责执行 PatentX UI/UX 全景重塑里程碑 M5：3D 特征星图与 CoT 折叠。

你的工作目录是 `d:\Antigravity projects\PatentX\.agents\worker_m5`。
你的任务是在 `frontend/src/components/DiagnosticDashboardNew.tsx` 和相关组件中实现 R6 的全部交互与 Canvas 3D 特效、CoT 折叠动效，并更新 `PROJECT.md` 状态。

### 具体任务：
1. **手写 3D 专利特征星图投影 (Canvas 2D)**:
   - 在 `DiagnosticDashboardNew.tsx` 布局中引入一个 Canvas 组件（如 3D 专利星云面板），大小自适应。
   - **数据绑定**：中心渲染国内专利核心（带发光波纹的黄色或蓝色球体）。周围轨道围绕着召回的现有技术文献（如 `EP3812049A1` 等）作为行星球体。行星上如果有冲突特征（即行 status 含有 `Fully_Disclosed` / `Conflict`），行星渲染为醒目的红色/粉色球体，并向外释放抛射运动的暗红微小尘埃粒子。
   - **3D 引擎数学实现**：
     - 在组件中定义节点数组，每个节点包含三维坐标 `(x, y, z)`，行星围绕中心 `(0,0,0)` 运转。
     - 手写三维旋转（用三角函数 `sin`, `cos` 在每一帧根据 `rotationX`, `rotationY` 更新三维坐标）。
     - 使用透视投影变换：`x_2d = centerX + x * focalLength / (z + zOffset)`，`y_2d = centerY + y * focalLength / (z + zOffset)`。
     - 绘制半径随 `z` 缩放，使其具有强烈的景深感（近大远小，远端半透明，近端高亮）。
     - 支持鼠标在 Canvas 拖拽改变星图视点角旋转（监听 drag 交互并累加旋转角速度与阻尼衰减）。
     - 在连线上绘制运动的粒子代表 SSE 辩论数据流动（流光效果）。

2. **Agent CoT 折叠思维链气泡**:
   - 在左侧发言气泡内，增加一个精美按钮（如“展开思维链 (CoT)”）。
   - 点击时原地展开一个半透明磨砂折叠层，包含：
     - 思维链流程大纲：
       - `1. 提取国内专利核心权利特征要素`
       - `2. EPO 数据源检索关联度匹配`
       - `3. 法律新颖性冲突判定评估`
     - 智能体资源耗费计量：
       - `输入 Token: 1,450 | 输出 Token: 320`
       - `当前预算消耗: $0.0053`
   - 使用 Framer Motion 驱动折叠展开，平滑伸缩大小。

3. **更新 `PROJECT.md` 里程碑状态**:
   - 读取并修改 `d:\Antigravity projects\PatentX\PROJECT.md`。将里程碑 M2、M3、M4 的 Status 列更新为 `DONE`，将 M5 的 Status 列更新为 `IN_PROGRESS`。确保格式对齐。

4. **构建验证**:
   - 在 `frontend` 目录运行 `npm run build`，确保整个前端项目编译打包零错误、零警告。

⚠️ **MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.


## 2026-05-23T13:47:30Z
请执行 PatentX UI/UX 全景重塑里程碑 M5：3D 特征星图与 CoT 折叠。

工作目录：d:\Antigravity projects\PatentX\frontend
你需要修改或创建以下前端组件：
1. **新建 3D 特征星图组件 (`frontend/src/components/FeatureStarChart.tsx`)**：
   - 采用 HTML5 Canvas 2D 进行高性能渲染，**严禁安装/使用 `three.js` 及其配套库**。
   - 实现手写的 3D-to-2D 旋转与投影转换算法：
     * 维护三维坐标 (x, y, z)，基于 `x_2d = centerX + x * focalLength / (z + zOffset)` 投影到二维屏幕上。
     * 计算三维旋转矩阵，基于鼠标拖拽（MouseDown/MouseMove/MouseUp）改变旋转角度 (angleX, angleY)，并支持惯性/阻尼衰减交互（释放鼠标后，星图能依惯性继续缓速自转至停止）。
     * 节点渲染半径与透明度需随景深 `z` 轴坐标变化：距离近的节点较大且亮，距离远的节点较小且半透明。
   - 拓扑关系设计：
     * **核心恒星**（中心大发光节点）：国内申请专利（如 'Domestic Patent'）。
     * **行星**（中型发光节点）：召回的对比文献（如 'D1', 'D2' 等），围绕核心恒星在不同的轨道高度运行。
     * **卫星**（小型发光节点）：对比文献中具体的对比特征节点（如 'D1_1', 'D1_2' 等），围绕其对应的行星运行或以连线绑定。
   - 动效与反馈机制：
     * **流光连线**：在 SSE 播放辩论日志时，如果当前辩论提及某国内特征 ID（如 `DF_0` 或 `DF_1`），从中心恒星向对应的卫星节点发射一条流动的亮蓝色光斑或波纹连线。
     * **冲突扩散粒子**：如果某个特征在矩阵中状态为完全公开（`Fully_Disclosed`，即存在新颖性冲突），对应的卫星节点在当前被高亮提及，或者当分析被挂起（`step === 'PAUSED'`）时，该节点变红并持续向外喷射/扩散红色微粒。
   - 将这个星图组件引入并渲染在 `DiagnosticDashboardNew.tsx` 的合适位置（例如，与对比文献/对齐矩阵并排，或者单独作为一块视觉焦点卡片）。

2. **实现 Agent COT 折叠思维气泡 (`frontend/src/components/DiagnosticDashboardNew.tsx`)**：
   - 重构对话气泡的渲染，在非 System 的发言气泡内，增加一个精美的折叠按钮，支持点击原地 Morphing 折叠或展开该 Agent 的“思维链（CoT）大纲”与“Token / 预算消耗看板”。
   - 折叠展开动画采用 Framer Motion (`motion.div` 的 `layout` 和 `animate`）实现高度与内容的平滑过渡。
   - **思维链大纲步骤 (CoT)**：
     * 解析/模拟该发言步骤 of the three white-box analysis steps, for example:
       1. 限制特征相似度映射计算（如：`DF_x` 与 `D1_y` 映射置信度为 `xx%`）
       2. EPO 审查基准 A54(2) 冲突阈值核验
       3. 拟定辩论策略与授权概率修正推演
   - **实时 Token & 预算看板**：
     * 显示该次推理的 Mock Token 消耗统计，如：`Prompt Tokens: 2,345`, `Completion Tokens: 512`, `Total cost: $0.0456`，使用等宽字体（`font-mono`）展示，强化“可解释性与白盒白玻感”。

3. **打包构建验证**：
   - 必须在 `frontend` 目录下运行 `npm run build` 命令，验证修改后的代码 100% 编译成功，没有任何 TypeScript 类型或构建错误。
   - 如果发现其他 TS 编译错误，请及时进行修复。

4. 将修改的具体代码、设计思路、构建命令及结果详细写在你的 handoff.md 中，并向我汇报。
5. **语言规则**：所有代码注释、日志输出、Handoff 及任务说明均使用【简体中文】。
