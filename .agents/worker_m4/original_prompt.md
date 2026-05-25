## 2026-05-23T13:35:37Z

你被派生为 Frontend Interactive and Animation Worker，负责执行 PatentX UI/UX 全景重塑里程碑 M4：挂起暗淡与单元格批注粒子反馈。

你的工作目录是 `d:\Antigravity projects\PatentX\.agents\worker_m4`。
你的任务是在 `frontend/src/components/DiagnosticDashboard.tsx` 和相关组件中实现 R5 的全部交互动效与数据绑定逻辑。

### 具体任务：
1. **全局遮罩暗淡 (Global Dampen)**:
   - 当 `step === 'PAUSED'` 时，主控台的以下非冲突部分应该添加 `opacity-30 blur-[0.5px] pointer-events-none transition-all duration-500` 样式：
     - 看板头部（标题、重新分析按钮等）
     - 授权预估概率卡片与裁决意见卡片
     - 对左侧的多智能体嵌套辩论日志面板
     - 对比文献列表部分
     - 对齐矩阵中，非 `Fully_Disclosed`（且尚未有专家本地批注）的普通对齐特征行。
   - 而所有发生新颖性冲突（`status === 'Fully_Disclosed'` 或处于被批注编辑状态）的行，以及底部的全局 `AgenticPauseCard`（输入卡片）必须保持 `opacity-100 scale-[1.005] z-10 duration-500` 的高亮聚焦状态，不受遮罩影响且可正常点击交互。

2. **冲突单元格呼吸发光与点击原地 Morphing**:
   - 在 `DiagnosticDashboard.tsx` 中为对齐特征状态为 `Fully_Disclosed` 的单元格（或状态标签）增加呼吸发光的 CSS/Tailwind 动画效果。当处于 `PAUSED` 状态时，它的发光效果应该激活（可以用 `@keyframes pulse-glow`）。
   - 允许用户直接点击该发光单元格（或整行），在原地展开（即在当前 `tr` 下面新增一个跨 4 列的 `tr`）一个微型批注卡片。微型卡片应包含：
     - 输入批注的 textarea。
     - “取消” 和 “确认修改 (Save)” 按钮。
   - 用户在微型批注卡片中输入意见并点击“确认修改 (Save)”时，触发“粒子注入”效果：
     - 计算当前点击的“确认修改”按钮的位置（startX, startY）与该行状态 Badge 的位置（endX, endY）。
     - 渲染一个微光能量粒子（如一个 absolute/fixed 定位、发光、直径约 12px 的青色圆点），以抛物线轨迹（使用 Framer Motion keyframes，例如 x 从 start 到 end，y 在中途向上抛起 -120px 弧度，再落入 end）飞入并吸附在对应的对齐矩阵状态标签上。
     - 粒子吸附的瞬间，该单元格的状态标签以 Morphing 动画过渡更新为亮青色的“专家已批注”标签（即渲染一个文本为 `专家已批注`、样式为亮青色 backdrop-blur 磨砂微光的标签，类似于其他微光胶囊标签，使用状态为 `[专家修正]` 或 `Expert_Revised`）。
     - 本地保存该特征的批注数据（例如存储在组件局部状态 `localAnnotations` 中，Key 使用特征的三维联合定位坐标 `f"{domestic_feature_id}_{prior_art_id}_{prior_art_feature_id}"`）。

3. **双向反馈连贯与全局 Resume 触发**:
   - 在底部的全局 `AgenticPauseCard.tsx` 交互中，或者在 `DiagnosticDashboard.tsx` 中消费它的提交逻辑：
     - 当用户在 `AgenticPauseCard` 点击 “专家修正 (Revise)” 按钮时：
       - 如果用户已经通过点击单元格保存了一些本地批注，直接使用 these 本地批注作为 details 字典。
       - 如果 `localAnnotations` 为空，说明用户没有手动点击单元格批注，此时为了保障走通流程（特别是后端集成测试），自动从全局文本框中提取文本，为所有 4 个冲突单元格自动分配对应的批注信息，并触发 4 颗“微光能量粒子”同时从全局输入框底部射出、呈抛物线飞向并吸附到这 4 个对齐状态单元格上！
       - 在所有粒子吸附动画完成后（建议延迟 500ms），将卡片物理收缩，调用全局 `resumeAnalysis('Revise', JSON.stringify(mergedAnnotations))`，全局暗淡遮罩褪去（解冻亮起），状态转换回 `THINKING` 阶段。

4. **打包构建与类型校验**:
   - 在修改完成后，在 `frontend` 目录下运行 `npm run build` 命令。
   - 确保编译零错误、零警告，并且没有因新增状态或动画引入 TypeScript 类型报错。

⚠️ **MANDATORY INTEGRITY WARNING**:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
