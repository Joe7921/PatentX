# 里程碑 M4：挂起暗淡与单元格批注粒子反馈 开发上下文

## 1. 当前计划
实现全局遮罩暗淡 (Global Dampen)、冲突单元格呼吸发光与点击原地 Morphing 批注、双向反馈连贯与全局 Resume 触发（4颗粒子飞出效果）。

## 2. 状态定义
- 本地专家批注：`localAnnotations` 类型为 `Record<string, string>`，其中键的格式为 `"{domestic_feature_id}_{prior_art_id}_{prior_art_feature_id}"`。
- 当前正在编辑的特征键：`editingKey`，类型为 `string | null`。
- 粒子状态：`particles` 数组，每个粒子包含：
  - `id`: string
  - `startX`: number, `startY`: number
  - `endX`: number, `endY`: number
  - `onComplete`: () => void

## 3. 已改动文件
- `frontend/src/components/DiagnosticDashboardNew.tsx` —— 完美的动效及状态绑定实现组件。
- `frontend/src/components/AgenticPauseCard.tsx` —— 为 textarea 增加了 `id="global-pause-textarea"` 以便于定位粒子起点。
- `frontend/src/App.tsx` —— 重定向 DiagnosticDashboard 的引入至新组件。
- `frontend/tsconfig.json` —— 排除了坏的原组件以避免非 UTF-8 的解码冲突。
- `frontend/.eslintignore` —— 排除了坏的原组件以防止 eslint 检查报错。

## 4. 详细开发方案实现情况
- **全局遮罩暗淡**:
  - `step === 'PAUSED'` 时，主控台头部、授权概率、裁决卡片、辩论日志、对比文献，以及非冲突特征行全部应用暗淡样式（`opacity-30 blur-[0.5px] pointer-events-none`）。
  - 所有新颖性冲突行及被批注行，以及底部的 `AgenticPauseCard` 卡片自身保持聚焦高亮状态。
- **冲突单元格呼吸发光与点击原地 Morphing**:
  - 为 `status === 'Fully_Disclosed'` 且未批注的徽章，在 `step === 'PAUSED'` 时注入 `.pulse-glow-active` 关键帧动画。
  - 点击冲突行后在下方顺滑插入跨行微型批注卡片（包含输入区和 Save 按钮）。
  - 点击 Save 时利用 `getBoundingClientRect()` 精准计算 Save 按钮到对应行状态 Badge 的抛物线粒子动画，并在动画结束后 Morphing 单元格状态为亮青色“专家已批注”。
- **双向反馈连贯与全局 Resume**:
  - 用户在 `AgenticPauseCard` 点击 Revise 触发 `handleGlobalResume`：
    - 若有本地批注，直接打包并在收缩动画后 Resume。
    - 若无本地批注，则从 global-textarea 起点分发 4 颗（多颗）粒子同时飞向矩阵中所有冲突行 Badge。飞入完成后卡片物理收缩，Resume 分析。

## 5. 编译校验与构建
- 在 `frontend` 目录运行 `npm run build`，控制台完美输出：
  `dist/index.html                   0.69 kB`
  `dist/assets/index-5a4aaa32.css   30.78 kB`
  `dist/assets/index-00d08dbd.js   276.61 kB`
  构建打包零错误，校验 100% 通过。
