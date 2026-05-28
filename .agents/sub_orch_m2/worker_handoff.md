# Refactoring Plan: Milestone 2 (Types & Store)

## Context
This is a synthesis of the deep review performed by 3 codebase explorers. The goal is to refactor `frontend/src/store/agenticTypes.ts` and `frontend/src/store/useStore.ts` to ensure strict type safety, split long functions, remove hardcoded data, and improve error handling.

## Execution Steps

### 1. Define Strict Types (`agenticTypes.ts`)
Add the following strict type interfaces to replace `any` in the store state. 

```typescript
/** 特征对齐项定义 */
export interface AlignmentFeature {
  domestic_feature_id?: string;
  prior_art_feature_id?: string;
  domestic_feature?: string;
  prior_art_feature_text?: string;
  status: string;
  explanation?: string;
  [key: string]: unknown;
}

/** 检索到的专利项定义 */
export interface RetrievedPatent {
  id: string;
  patent_family?: string;
  title?: string;
  claim_1?: string;
  [key: string]: unknown;
}

/** 专家注释定义 */
export interface ExpertAnnotation {
  [key: string]: unknown;
}
```

### 2. Update Store Interfaces (`useStore.ts`)
Update the `BlackboardState` and variable declarations to use the new strict types.
- `feature_alignment_matrices: Record<string, AlignmentFeature[]>;`
- `expert_annotations: Record<string, ExpertAnnotation>;`
- `retrieved_patents: RetrievedPatent[];`
- `let reconnectTimer: ReturnType<typeof setTimeout> | null = null;`
- Update the interface in `useStore.ts` or move `BlackboardState` to `agenticTypes.ts` as appropriate, making sure to eliminate all `: any` types.

### 3. Remove Hardcoded Mock Data
In `agenticTypes.ts`, locate `createInitialTimelineState`. Currently, it hardcodes an array of 4 phases (`document_analysis`, etc.).
- Change it to return an empty array for phases: `phases: []`

In `useStore.ts`, within the `handleTimelineEvent` (or equivalent) logic for `phase_start`:
- Change the logic so that if the `phase` ID does not exist in `phases`, it dynamically creates and pushes the new phase into the `phases` array, instead of solely relying on `map` over pre-existing mock phases.

### 4. Split Long Functions
The `connectSSE` function in `useStore.ts` is extremely long (~200 lines).
- Extract the `handleMessage` and `handleTimelineEvent` logic into separate standalone functions (either outside the factory or in a separate file if needed, but keeping them in `useStore.ts` as standalone functions is fine).
- Pass the necessary Zustand `set` and `get` functions to these extracted handlers.

### 5. Improve Error Handling
In `useStore.ts`:
- Change `catch (err: any)` to `catch (err: unknown)` in `resumeAnalysis` and everywhere else.
- In `resumeAnalysis`, when `!response.ok`, safely parse the response (e.g., wrap `response.json()` in a try-catch and fallback to `.text()` if JSON parsing fails, because of 502/504 HTML error pages).
- In the SSE event listeners (where `JSON.parse(event.data)` happens), if parsing fails, do not just `console.error` silently. Ensure you call `set({ error: errorMessage })` so the UI can react to the failure.

## Verification
1. Run `npm run build` in the `frontend/` directory to ensure no TypeScript compilation errors exist.
2. Verify that `any` has been completely eliminated from the store logic.

**IMPORTANT:**
- All code comments added or modified must be in **Simplified Chinese (简体中文)**.
- Do not use PowerShell to modify files. Use your built-in file editing tools (e.g., `replace_file_content` or `multi_replace_file_content`).
- Ensure no mock data remains for phases.
