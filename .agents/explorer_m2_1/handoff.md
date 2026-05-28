# Handoff Report: Milestone 2 - Refactor Types & Store

## 1. Observation
I have inspected the following target files:
- `frontend/src/store/agenticTypes.ts`
- `frontend/src/store/useStore.ts`

**Identified `any` Types in `useStore.ts`:**
- Line 16: `feature_alignment_matrices: Record<string, any[]>;`
- Line 17: `expert_annotations: Record<string, any>;`
- Line 21: `retrieved_patents: any[];`
- Line 51: `let reconnectTimer: any = null;`
- Line 319: `catch (err: any) {`

**Long Functions:**
- The `connectSSE` block (Lines 60-256 in `useStore.ts`) spans ~196 lines. It heavily nests `handleMessage` (48 lines) and `handleTimelineEvent` (91 lines).

**Hardcoded Mock Data:**
- No significant mock data payloads were found in the store. However, hardcoded fallback strings exist (e.g., `'智能体评估遭遇争议，需要人类专家介入决策。'` on Line 108) and static configurations (`createInitialTimelineState`) are embedded in the type definition file.

**Error Handling:**
- Line 123 & 216: `catch (err)` inside SSE parsing functions merely logs to `console.error` and silently swallows errors, failing to update the `store.error` state.
- Line 319: Uses `err: any` and unsafely accesses `err.message`.

## 2. Logic Chain
1. **Strict Typing**: To remove `any` from `BlackboardState`, we must define specific interfaces (`FeatureAlignment`, `ExpertAnnotation`, `RetrievedPatent`). Since we don't have the exact backend schema, we will define strong foundational shapes that the implementer can refine.
2. **Timer Typing**: `reconnectTimer` should be explicitly typed using `ReturnType<typeof setTimeout> | null` to be environment-agnostic.
3. **Splitting `connectSSE`**: To improve maintainability, `handleMessage` and `handleTimelineEvent` should be extracted outside the store factory or into separate modules. They will accept the Zustand `set` and `get` functions as parameters.
4. **Error Handling**: 
   - `catch (err: any)` must be replaced with `catch (err: unknown)`. We need an `instanceof Error` check to extract the message safely.
   - SSE parsing `catch` blocks must call `set({ error: '...' })` to propagate parsing failures to the UI, rather than failing silently.

## 3. Caveats
- **Assumed Data Models**: The exact structure of `FeatureAlignment`, `ExpertAnnotation`, and `RetrievedPatent` is not fully visible in the frontend codebase. The proposed types are intelligent estimates. The implementer must ensure they align with the backend's actual JSON output.
- **Extraction Side Effects**: Moving event handlers out of `connectSSE` requires passing `set` and `get` correctly to avoid stale closures.

## 4. Conclusion
The store requires a targeted refactor to enforce TypeScript strictness, decouple SSE event logic, and harden error reporting. 

**Recommended Action Plan for Implementer:**
1. Add strict interface definitions in `agenticTypes.ts` (see snippet below).
2. Update `useStore.ts` state interface to use the new types.
3. Extract `handleMessage` and `handleTimelineEvent` into separate standalone functions, passing `set` and `get`.
4. Fix all catch blocks to use `unknown` and update the store error state properly.

### Proposed Code Changes & Comments (in Simplified Chinese)

**In `agenticTypes.ts` (Additions):**
```typescript
/** 检索到的专利类型定义 */
export interface RetrievedPatent {
  id: string;
  title: string;
  abstract: string;
  similarityScore?: number;
}

/** 特征对齐类型定义 */
export interface FeatureAlignment {
  feature: string;
  matched: boolean;
  score?: number;
  evidence?: string;
}

/** 专家注释类型定义 */
export interface ExpertAnnotation {
  comments: string[];
  approved: boolean;
  [key: string]: unknown; // 替代 any 的安全扩展
}
```

**In `useStore.ts` (Typing Fixes):**
```typescript
export interface BlackboardState {
  eval_id: string | null;
  current_step: string;
  claim_features: string[];
  // 使用严格类型替换 any[]
  feature_alignment_matrices: Record<string, FeatureAlignment[]>;
  // 使用严格类型替换 any
  expert_annotations: Record<string, ExpertAnnotation>;
  debate_logs: string[];
  overall_probability: number | null;
  overall_conclusion: string | null;
  // 使用严格类型替换 any[]
  retrieved_patents: RetrievedPatent[];
}

// 修复定时器类型
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
```

**In `useStore.ts` (Error Handling Fix):**
```typescript
// 安全的错误捕获与处理
catch (err: unknown) {
  console.error('Error during resume request:', err);
  const errorMessage = err instanceof Error ? err.message : '发送恢复请求失败';
  set({ error: errorMessage });
  return false;
}
```

**In `useStore.ts` (SSE Error Propagation):**
```typescript
} catch (err: unknown) {
  console.error('解析 SSE 事件数据失败:', err);
  // 向外暴露解析错误，以便在 UI 给出提示
  const errorMessage = err instanceof Error ? err.message : '未知的数据解析错误';
  set({ error: `SSE 解析失败: ${errorMessage}` });
}
```

## 5. Verification Method
1. **Type Checker**: Run `npx tsc --noEmit` in the `frontend/` directory to verify there are no TypeScript errors.
2. **Any Removal**: Run `grep -r ": any" frontend/src/store/` to confirm all generic `any` types have been removed.
3. **Build Check**: Run `npm run build` in `frontend/` to guarantee successful compilation.
