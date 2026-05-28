# 阶段移交报告：Milestone 2 Refactor Types & Store

## 1. 观察发现 (Observation)

经过对 `frontend/src/store/agenticTypes.ts` 和 `frontend/src/store/useStore.ts` 的深入代码审查，观察到以下现象：

1. **`any` 类型的泛滥**：
   - `useStore.ts` 存在多处 `any` 类型定义，包括：
     - `feature_alignment_matrices: Record<string, any[]>;`
     - `expert_annotations: Record<string, any>;`
     - `retrieved_patents: any[];`
     - `let reconnectTimer: any = null;`
     - `catch (err: any)` 在 `resumeAnalysis` 方法中。

2. **超长函数未拆分**：
   - `useStore.ts` 中的 `connectSSE` 函数极长（涵盖了约 200 行代码），其中内联定义了庞大的 `handleMessage` 和 `handleTimelineEvent` 事件处理函数。这导致 Zustand Store 的定义极度臃肿，违背了职责分离原则。

3. **硬编码的 Mock 数据**：
   - 在 `agenticTypes.ts` 的 `createInitialTimelineState` 方法中，`phases` 数组被硬编码初始化为包含 4 个阶段（`document_analysis`, `internal_review`, `oral_proceedings`, `final_decision`）的死数据。
   - `useStore.ts` 中处理 `phase_start` 时，仅对已存在的硬编码 Phase 进行 `map` 更新，若后端下发新的阶段则无法动态追加。
   - `hitl_interrupt` 事件中包含了 `data.phase`，但 `useStore` 忽略了该字段，导致前端组件（如 `AgenticTimeline.tsx`）不得不硬编码猜测 HITL 的插入位置。

4. **错误处理不完善**：
   - 在 `handleMessage` 和 `handleTimelineEvent` 的 `try-catch` 块中，对 `JSON.parse(event.data)` 的异常仅仅做了 `console.error`，没有将异常状态同步到 Store 的 `error` 字段中。
   - `resumeAnalysis` 函数中，当 `!response.ok` 时，直接 `await response.json()`，如果服务器返回 502/504 的 HTML 页面，这里会触发 JSON 解析异常导致奔溃。且 `catch` 块中使用了粗暴的 `err: any`。

## 2. 逻辑推演 (Logic Chain)

1. **类型安全性重构**：消除 `any` 是确保重构成功的基石。通过梳理 `DiagnosticDashboard.tsx` 组件的实际消费情况，可以推导出确切的接口模型（如 `AlignmentFeature` 和 `RetrievedPatent`），并将其统一定义在 `agenticTypes.ts` 中。
2. **状态驱动动态化（消除 Mock）**：将时间线的阶段定义完全交由后端的 SSE 事件流驱动。初始化时 `phases` 应为空数组 `[]`，在接收到 `phase_start` 时动态 push 生成对应的阶段状态，同时将 `hitlPhase` 存入 Store，使得前端完全解耦，不再依赖固定阶段的数量假设。
3. **架构解耦拆分**：由于 Zustand store 工厂函数内部包含庞大的逻辑，应当把事件处理函数抽离为独立的 Helper 函数，或者将其注册逻辑移至独立的模块（如 `sseService.ts`），并仅仅通过调用 Store 的 action（如 `setTimelineEvent`, `setMainEvent`）来更新状态，从而使 `useStore.ts` 恢复轻量级。
4. **防御性编程**：API 通信中对于非 2xx 响应的内容解析必须先使用 `.text()` 或放在 `try-catch` 里，以免非预期的网关报错破坏程序的健壮性。

## 3. 注意事项 (Caveats)

- 移除了硬编码的 phases 可能会导致在收到第一个 `phase_start` 前，UI 上没有任何时间线节点显示，这在业务逻辑上是正常的。
- 在 `useStore.ts` 中拆分长函数时，需要通过闭包或参数显式传递 Zustand 的 `get` 和 `set` 方法。
- 请注意在定义新接口（如 `AlignmentFeature`）时，需确保符合后端实际下发的蛇形命名（Snake Case）字段，以适配 `blackboard` 数据。

## 4. 结论与重构策略 (Conclusion)

建议执行以下代码修改策略（注意：代码注释必须使用简体中文）：

### 步骤 1: 补充并严格化类型 (`agenticTypes.ts` & `useStore.ts`)
在 `agenticTypes.ts` 尾部增加：
```typescript
/** 特征对齐项 */
export interface AlignmentFeature {
  domestic_feature_id?: string;
  domestic_feature: string;
  prior_art_feature_id: string;
  prior_art_feature_text: string;
  status: string;
  explanation: string;
}

/** 检索到的对比文献 */
export interface RetrievedPatent {
  id: string;
  patent_family: string;
  title: string;
  claim_1: string;
}
```
更新 `useStore.ts` 的类型定义：
- `feature_alignment_matrices: Record<string, AlignmentFeature[]>;`
- `expert_annotations: Record<string, string>;`
- `retrieved_patents: RetrievedPatent[];`
- `reconnectTimer: ReturnType<typeof setTimeout> | null;`
- `AgenticTimelineState` 补充字段 `hitlPhase?: number;`

### 步骤 2: 消除 Mock 数据
- 修改 `agenticTypes.ts` 中的 `createInitialTimelineState`，让 `phases` 初始化为 `[]`。
- 修改 `useStore.ts` 中针对 `phase_start` 的处理：
```typescript
const phaseId = data.phase as number;
const existingPhase = agSt.phases.find(p => p.id === phaseId);
let updatedPhases;
if (existingPhase) {
  updatedPhases = agSt.phases.map(p => p.id === phaseId ? {
    ...p, status: 'active' as const, name: data.name || p.name, title: data.title || p.title, agents: data.agents || p.agents
  } : p);
} else {
  // 动态新增由后端驱动的阶段
  updatedPhases = [...agSt.phases, {
    id: phaseId, name: data.name || \`phase_\${phaseId}\`, title: data.title || \`阶段 \${phaseId}\`, status: 'active' as const, agents: data.agents || [], steps: []
  }];
}
```
- 在 `hitl_interrupt` 事件处理中保存 `hitlPhase: data.phase`，供视图层使用。

### 步骤 3: 拆分函数与错误处理增强
- 在 `useStore.ts` 中提取 `handleMessage(event, set, get)` 和 `handleTimelineEvent(event, set, get)` 为模块内顶层的纯函数，从 `connectSSE` 中剥离出来。
- 在 `resumeAnalysis` 中使用安全的错误捕获：
```typescript
catch (err: unknown) {
  const errorMessage = err instanceof Error ? err.message : String(err);
  set({ error: errorMessage || 'Failed to send resume request' });
}
```
- 同样对于 `await response.json()` 包裹 `try-catch` 或回退到 `await response.text()`。

## 5. 验证方法 (Verification Method)

- **类型检查验证**：运行 `npm run build` 或 `npx tsc --noEmit`，确保 `frontend/src/store/useStore.ts` 没有任何 TypeScript 的 `any` 报错。
- **状态树验证**：前端启动后，发起一次诊断评估，观察 Network SSE 流推送 `phase_start` 时，时间线节点是否能从空状态成功动态生成渲染。
- **代码规范验证**：检查 `useStore.ts` 中 `connectSSE` 是否已瘦身，对应的 handler 是否成功抽离；确认所有新增代码的注释为【简体中文】。
