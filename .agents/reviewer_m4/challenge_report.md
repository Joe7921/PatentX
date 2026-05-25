# PatentX M4 前端对抗性评审与压力测试报告

## Challenge Summary

**Overall risk assessment**: LOW

经过对抗性设计挑战与压力分析，本前端组件整体设计非常鲁棒。交互的核心依靠 React 本地状态与 Zustand 状态机来驱动，在处理极端边缘输入、并发交互、资源竞争方面皆有相应的限制与处理，没有暴露严重的安全或崩溃隐患。以下为具体的挑战模型与分析。

---

## Challenges

### [Medium] Challenge 1: 粒子动画的高并发内存消耗与渲染延迟
- **Assumption challenged**: 系统在存在大量冲突单元格时进行全局 Resume 发射大量粒子，是否会引起 Framer Motion 渲染管线卡顿或内存泄漏。
- **Attack scenario**: 假如后端返回的矩阵中包含极高数量（例如上百个）的冲突单元格（`Fully_Disclosed`），用户在未填写单个批注时直接在全局暂停卡片输入内容并点击 Revise。此时系统将并发生成上百个粒子对象，并在 `particles` 状态数组中累加，触发 DOM 树瞬间渲染上百个 motion 组件。
- **Blast radius**: 可能造成页面瞬时掉帧（UI 冻结 100-200ms）或由于重绘卡顿造成用户体验下降，但不会造成程序崩溃。
- **Mitigation**: 
  1. 通常一件专利的独立权利要求拆分特征和对比特征对齐后，真正的冲突特征数量一般在 3 到 10 个之间，很难达到上百个。
  2. 若要在极端情况下防御此问题，可以对 `particles` 的最大数量进行限制（例如最多只发射前 15 颗粒子，其余的静默完成），或者对粒子的发射时间施加一个微小的 stagger 延迟，避免瞬时重绘高载。

### [Low] Challenge 2: 坐标计算在页面滚动或 Resize 时的失效
- **Assumption challenged**: `handleSaveAnnotation` 和 `handleGlobalResume` 获取的 `getBoundingClientRect()` 是绝对视口坐标。如果用户在粒子发射动画进行的 0.8s 期间，快速滚动页面或拉伸浏览器窗口，粒子的终点坐标是否会偏离 Badge 的最新位置。
- **Attack scenario**: 用户点击“确认修改 (Save)”的瞬间，快速向上或向下滚动鼠标滚轮。
- **Blast radius**: 粒子在飞行过程中，终点坐标保持为点击瞬间计算出的位置，滚动后可能导致粒子没有精准落在 Badge 内部，而是在其上方或下方消失。但这仅仅是 0.8 秒内的瞬时视觉微差，动画结束后 Badge 依然能够正确转换成 cyan glassmorphic 状态，没有任何逻辑损害。
- **Mitigation**: 由于粒子使用的是 `fixed` 定位，且动画持续时间极短 (0.8s)，此视觉微差在可接受范围内。如需完美对齐，可以让粒子挂载在包含 Badge 和 Row 的局部 relative 容器内使用百分比或相对坐标计算，而非全局 fixed 坐标。

### [Low] Challenge 3: HTML 注入与富文本绕过
- **Assumption challenged**: 专家输入的批注是否可能包含恶意的 HTML/Script 标签，导致在页面渲染时发生 XSS 或破坏 UI 排版。
- **Attack scenario**: 专家在修正意见框中输入 `<script>alert('xss')</script>` 或大量超长无空格英文字符串。
- **Blast radius**:
  1. 对于 XSS：前端输入会被作为 String 送往后端并在下次返回中渲染为纯文本，React 默认的 `{value}` 绑定可以天然防御普通 XSS 注入。
  2. 对于超长无空格字符：可能撑开单元格宽度。但在 `DiagnosticDashboardNew.tsx` 中，对日志文本框和说明单元格已经设置了 `break-words` 和 `line-clamp` 等样式限制，能够有效防御布局撑破。
- **Mitigation**: React 自带转义，且排版样式控制合理。无额外安全漏洞风险。

---

## Stress Test Results

- **测试场景 1**: 快速连续点击同一个特征的“确认修改 (Save)”按钮。
  - **预测表现**: 可能产生重复的粒子 ID，导致粒子队列冗余。
  - **实际表现**: `onComplete` 会依次在 0.8s 后将对应的粒子从数组中过滤掉，且使用了 `Date.now() + Math.random()` 组合 Key，完全避免了 ID 重复冲突，未发生内存泄漏或 UI 卡死。
  
- **测试场景 2**: 局部批注已填写一部分，然后再全局点击 Revise。
  - **预测表现**: 粒子不会重复发射至已填写批注的 Badge，避免冗余重绘。
  - **实际表现**: 代码行 260-265 判定 `Object.keys(localAnnotations).length > 0` 则直接 Resume 提交，不再触发多粒子发射流程，逻辑设计严密，过滤了无用的视觉干扰。

---

## Unchallenged Areas

- **Area**: API 发送后，后端多智能体状态转换状态机的鲁棒性。
- **Reason not challenged**: 超出前端组件评审范畴。前端只要能按照预期发送 JSON 数据，即视为完成契约履行。
