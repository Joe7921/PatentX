# Handoff Report: Milestone 2: Refactor Types & Store

## Observation
- **文件检查**: 深入审查了 `frontend/src/store/agenticTypes.ts` 和 `frontend/src/store/useStore.ts`。
- **`any` 类型**: 
  - `useStore.ts` 第 16 行：`feature_alignment_matrices: Record<string, any[]>;`
  - `useStore.ts` 第 17 行：`expert_annotations: Record<string, any>;`
  - `useStore.ts` 第 21 行：`retrieved_patents: any[];`
  - `useStore.ts` 第 51 行：`let reconnectTimer: any = null;`
  - `useStore.ts` 第 319 行：`catch (err: any)`
- **过长的函数**: `useStore.ts` 中的 `connectSSE` 函数非常长（约 200 行），内部包含了深层嵌套的 `handleMessage` 和 `handleTimelineEvent` 事件处理逻辑。
- **硬编码的 Mock 数据**: `agenticTypes.ts` 中的 `createInitialTimelineState()` 函数硬编码返回了一个包含 4 个固定阶段（如 `document_analysis`, `internal_review` 等）的 `phases` 数组。这是一个静态的占位数据，使得应用无法完全基于 SSE 流动态构建时间线。
- **错误处理缺失/不规范**:
  - `useStore.ts` 的 `resumeAnalysis` 函数中，`if (!response.ok)` 分支直接使用 `await response.json()`。如果服务器返回 502/504 等 HTML 错误页面，JSON 解析将抛出未捕获异常。
  - SSE 事件解析（`JSON.parse(event.data)`）失败时，仅仅是 `console.error`，并没有将异常状态同步到全局 Store 中反馈给用户。

## Logic Chain
1. **消除 `any` 类型**: 必须在 `agenticTypes.ts` 中定义 `FeatureAlignmentItem` 和 `RetrievedPatentItem` 等强类型接口，并将 `BlackboardState` 移动或引用到这些严格类型，避免运行时隐患。
2. **拆分长函数**: 将 `connectSSE` 内的 `handleMessage` 和 `handleTimelineEvent` 提取为独立的高阶函数（可接收 `set` 和 `get` 作为参数），从而降低 `useStore.ts` 的代码圈复杂度。
3. **移除硬编码 Mock 数据**: 将 `createInitialTimelineState` 改为返回空数组 `phases: []`。同时，`useStore.ts` 中的 `phase_start` 处理器应修改为：当收到新阶段事件时，检查是否已存在该阶段，若不存在则动态 `push` 到 `phases` 数组中，实现真正的服务端驱动。
4. **完善错误处理**: 在 `resumeAnalysis` 中，将 `err: any` 替换为 `err: unknown`，并在 `response.json()` 周围增加 `try/catch`，降级回退到 `response.text()`；在 `connectSSE` 中，如果发生致命的解析错误，调用 `set({ error: ... })` 更新状态。

## Caveats
- 如果 `phases` 初始化为空数组，前端 UI（如 `AgenticTimeline.tsx`）在刚加载时将不显示任何阶段节点，直到接收到服务端的 `phase_start` 事件。这是事件驱动 UI 的正确预期，但需要确认实现时正确处理了空数组的渲染逻辑（目前观察代码，UI 可以兼容空数组）。
- 后端数据结构的具体细节可能有细微变化，因此定义的 `FeatureAlignmentItem` 和 `RetrievedPatentItem` 等接口可以使用可选属性或索引签名（如 `[key: string]: unknown`）来兼顾严格性与灵活性。

## Conclusion
请 Implementer 按照以下重构策略执行修改：
1. **类型定义提取**: 将 `BlackboardState` 从 `useStore.ts` 移动到 `agenticTypes.ts`。定义 `FeatureAlignmentItem` 和 `RetrievedPatentItem`，替换掉所有的 `any`。将 `reconnectTimer` 的类型设为 `ReturnType<typeof setTimeout> | null`。
2. **状态初始化重构**: 修改 `agenticTypes.ts` 中的 `createInitialTimelineState`，使 `phases: []` 初始化为空。
3. **状态更新逻辑重构**: 在 `useStore.ts` 的 `handleTimelineEvent`（`phase_start` 分支）中，改为：若 `agSt.phases` 中不存在该 `phaseId`，则向数组 `push` 新阶段对象。
4. **长函数拆分**: 将 `handleMessage` 和 `handleTimelineEvent` 逻辑抽离出 `connectSSE`，可作为独立工厂函数或置于模块作用域中。
5. **错误处理加固**: 修正 `resumeAnalysis` 的 `catch (err: unknown)`，并用 `try/catch` 包裹 `await response.json()`。

**代码建议示例**：
```typescript
// 在 agenticTypes.ts 中添加：
/** 特征对齐项定义 */
export interface FeatureAlignmentItem {
  domestic_feature_id?: string;
  prior_art_feature_id?: string;
  domestic_feature?: string;
  prior_art_feature_text?: string;
  status: string;
  explanation?: string;
  [key: string]: unknown;
}

/** 检索到的专利项定义 */
export interface RetrievedPatentItem {
  id: string;
  patent_family?: string;
  title?: string;
  claim_1?: string;
  [key: string]: unknown;
}
```

## Verification Method
1. 运行 `npm run build`（在 `frontend/` 目录下），确保无 TypeScript 类型报错和语法错误。
2. 使用 `grep_search` 在 `frontend/src/store/` 下搜索 `any`，确保已彻底消除所有的 `any` 类型。
3. 检查 `useStore.ts`，确认 `connectSSE` 已经被拆分且逻辑清晰。
4. 检查 `agenticTypes.ts`，确认 `createInitialTimelineState` 返回的 `phases` 为空数组。
