# 里程碑 M4：挂起暗淡与单元格批注粒子反馈 宏观计划

## 1. 计划目标
实现挂起暗淡、冲突行聚焦高亮、冲突单元格呼吸发光、点击原地 Morphing 展开微型批注卡片、提交粒子飞入动画、吸附后状态标签 Morphing 更新、以及底部的全局 `AgenticPauseCard` 反馈连贯（4 颗能量粒子同时射出飞入并吸附）。最终确保能在 `npm run build` 下无错误地打包构建。

## 2. 详细步骤与验证方法

### 步骤 1: 设计并创建 context 统一共享状态
- 需要收集本地批注 `localAnnotations`，它是 `{[key: string]: string}`，其中 key 是 `"{domestic_feature_id}_{prior_art_id}_{prior_art_feature_id}"`。
- 本地批注编辑状态 `editingKey` 记录当前哪个单元格正在处于被批注编辑状态。如果是，对应行也属于聚焦状态不受暗淡遮罩影响。
- 在 `DiagnosticDashboard.tsx` 和 `AgenticPauseCard.tsx` 中建立反馈管道。
- 粒子动画的触发机制：维护一个 `particles` 数组在 state 中，当保存批注或点击全局 Revise 触发时生成粒子并播放 Framer Motion 动画，动画结束时更新对应单元格状态，并移除粒子。

### 步骤 2: 全局遮罩暗淡 (Global Dampen)
- 在 `step === 'PAUSED'` 时：
  - 看板头部（标题、重新分析按钮等）
  - 授权预估概率卡片与裁决意见卡片
  - 左侧的多智能体嵌套辩论日志面板
  - 对比文献列表部分
  - 对齐矩阵中，非 `Fully_Disclosed`（且尚未有专家本地批注，且不处于被批注编辑状态）的普通对齐特征行。
  - 这些部分添加类名：`opacity-30 blur-[0.5px] pointer-events-none transition-all duration-500`。
- 而以下部分保持高亮：
  - 新颖性冲突行（`status === 'Fully_Disclosed'` 或处于被批注编辑状态，即 `editingKey` 与该行相关）
  - 底部的全局 `AgenticPauseCard`（输入卡片）
  - 样式为：`opacity-100 scale-[1.005] z-10 duration-500`。
- 验证方式：修改后预览或在 `PAUSED` 状态下检查相关元素的 class。

### 步骤 3: 冲突单元格呼吸发光与点击原地 Morphing
- 在 `DiagnosticDashboard.tsx` 中：
  - 对对齐特征状态为 `Fully_Disclosed` 且尚未有专家本地批注的单元格增加呼吸发光效果。
  - 可以在 `tailwind.config.js` 或者组件内部通过 inline `<style>` 定义 `pulse-glow` 动画：
    ```css
    @keyframes pulse-glow {
      0%, 100% { box-shadow: 0 0 4px rgba(244,63,94,0.4); border-color: rgba(244,63,94,0.5); }
      50% { box-shadow: 0 0 12px rgba(244,63,94,0.8); border-color: rgba(244,63,94,0.8); }
    }
    ```
  - 点击 `Fully_Disclosed` 单元格（或状态标签，或整行）时，在原地展开：在该行（`tr`）下面，渲染一个跨 4 列的 `tr`，在里面显示微型批注卡片：
    - 包含输入批注的 `textarea`。
    - “取消”与“确认修改 (Save)”按钮。
  - 用户在微型批注卡片中输入并点击“确认修改 (Save)”时，触发“粒子注入”效果：
    - 计算当前点击的“确认修改”按钮的位置 (startX, startY) 与对应行状态 Badge 的位置 (endX, endY)。
    - 因为粒子需要是 fixed 或 absolute 定位的圆点，我们可以用 `getBoundingClientRect()` 计算两者的相对/绝对坐标。
    - 渲染微光能量粒子（直径约 12px 青色圆点），以抛物线轨迹（使用 Framer Motion keyframes，x 轴从 start 变到 end，y 轴做抛物线，例如 `y: [startY, startY - 120, endY]`）飞入并吸附在对应的对齐矩阵状态标签上。
    - 粒子吸附的瞬间，更新本地批注，且该状态标签更新为亮青色的“专家已批注”标签（`Expert_Revised`）。
- 验证方式：点击冲突行，展开批注卡片，输入并保存，看到粒子飞向 Badge 并变成“专家已批注”亮青色标签。

### 步骤 4: 双向反馈连贯与全局 Resume 触发
- 在底部的全局 `AgenticPauseCard.tsx` 交互中，或者在 `DiagnosticDashboard.tsx` 消费其提交逻辑：
  - 把 `localAnnotations` 等状态传递给 `AgenticPauseCard`，或者在 `DiagnosticDashboard` 里包装 `resumeAnalysis` 传给 `AgenticPauseCard`。
  - 点击 “专家修正 (Revise)” 按钮时：
    - 如果 `localAnnotations` 不为空，使用 `localAnnotations` 作为 details。
    - 如果 `localAnnotations` 为空，说明用户没有手动点击单元格批注，此时自动从全局文本框中提取文本，为所有 4 个冲突单元格自动分配对应的批注信息（即对于所有 `status === 'Fully_Disclosed'` 的冲突行，分配相同的全局文本作为批注）。
    - 触发 4 颗“微光能量粒子”同时从全局输入框底部（或者“专家修正”按钮）射出，以抛物线飞向并吸附到这 4 个对齐状态单元格上！
    - 粒子吸附动画完成后（延迟约 500ms），将卡片物理收缩，调用全局 `resumeAnalysis('Revise', JSON.stringify(mergedAnnotations))`。
- 验证方式：输入全局修正意见，直接点击“专家修正”，看 4 颗粒子同时飞往对齐矩阵，并在吸附后调用 `resumeAnalysis`。

### 步骤 5: 打包构建与类型校验
- 在 `frontend` 目录运行 `npm run build`，确保无错误、无警告。
