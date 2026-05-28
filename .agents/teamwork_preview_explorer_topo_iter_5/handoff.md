# Handoff Report

## Observation
1. **Integrity Violation**: 
   - `PROJECT.md` dictates "update `DocumentPreview.tsx` to PiP, wire up in `App.tsx`".
   - `App.tsx` (line 96) currently imports and renders `<DraftingPiP />`.
   - `DraftingPiP.tsx` is an entirely separate component that lacks `framer-motion`'s `drag` property on its floating container.
   - `DocumentPreview.tsx` (the intended target) is currently abandoned/dead code.
2. **O(N^2) String Concatenation Bottleneck**:
   - `DraftingPiP.tsx` (line 16) and `DocumentPreview.tsx` (line 10) both compute `documentChunks.join('')` on every render.
   - As `documentChunks` grows during streaming, joining the full array on every React frame creates an O(N^2) block on the main thread.
3. **Raw Text without Markdown**:
   - `DraftingPiP.tsx` renders the concatenated `content` string directly inside a `div` (line 110), bypassing markdown formatting.
   - `DocumentPreview.tsx` (line 108) correctly utilizes `<ReactMarkdown>` but isn't being used.
4. **DynamicTopoGraph lacks Virtualization**:
   - `DynamicTopoGraph.tsx` (lines 60-97) maps over the entire `topologyNodes` array and renders `motion.div` for every node, regardless of visibility. This causes severe frame drops when node count is high.

## Logic Chain
1. **Fixing the Integrity Violation & Markdown Issue**: We must deprecate/delete `DraftingPiP.tsx` and refactor `DocumentPreview.tsx` to serve as the floating PiP window. Wrapping `DocumentPreview`'s root in a `<motion.div drag dragMomentum={false}>` will satisfy the missing drag requirement. Re-integrating `DocumentPreview` into `App.tsx` naturally fixes the Markdown parsing issue, as it already incorporates `<ReactMarkdown>`.
2. **Fixing the O(N^2) String Concatenation**: Instead of running `join('')` on every render cycle, `DocumentPreview.tsx` should manage a local `string` state. A `useEffect` hooked to `documentChunks` can slice only the newly added chunks (tracked via a `useRef` index) and append them to the local string state (`setText(prev => prev + newChunks.join(''))`). This reduces the concatenation time complexity from O(N^2) to O(N).
3. **Fixing the Virtualization Frame Drops**: `DynamicTopoGraph.tsx` needs a windowing mechanism. Since no external virtualization library (like `react-window`) is installed, we can implement manual horizontal virtualization. By attaching an `onScroll` handler to the scrollable container, we can derive `startIndex` and `endIndex` based on `scrollLeft` and an estimated item width (e.g., node width + gap). Rendering only `topologyNodes.slice(startIndex, endIndex)` and using spacer `div`s to pad the unrendered space will maintain the correct scroll width while drastically reducing DOM nodes and Framer Motion overhead.

## Caveats
- Calculating the exact item width for virtualization might require some CSS adjustments in `DynamicTopoGraph.tsx` to ensure spacer `div`s perfectly align with the expected total scroll width. Removing `space-x-6` in favor of explicit `margin-right` on items makes calculations deterministic.
- Dragging a PiP requires `dragConstraints` (usually to a parent reference or viewport boundaries) so it doesn't get dragged out of the visible screen area.

## Conclusion
The previous iteration failed because it substituted the required file transformation with a pre-existing/new file (`DraftingPiP`), omitting key features like dragging and Markdown parsing. Furthermore, rendering logic in both the PiP and Topo components scales poorly with data size.

The Implementer should:
1. Delete `DraftingPiP.tsx`.
2. Refactor `DocumentPreview.tsx` into a draggable PiP using `<motion.div drag>`.
3. Update `App.tsx` to render `<DocumentPreview />` instead of `<DraftingPiP />`.
4. Optimize `DocumentPreview.tsx` text concatenation by maintaining an incremental local string state instead of joining the whole array on every render.
5. Add manual horizontal virtualization to `DynamicTopoGraph.tsx` by slicing `topologyNodes` based on scroll position and inserting layout-preserving spacer `div`s.

## Verification Method
1. `npm run build` in the `frontend` folder ensures no TypeScript errors.
2. Inspect `App.tsx` to verify `<DocumentPreview />` is used and `DraftingPiP` is gone.
3. Inspect `DocumentPreview.tsx` to verify `<motion.div drag>` is present and text is built incrementally.
4. Inspect `DynamicTopoGraph.tsx` to verify `.slice(startIndex, endIndex)` is used for rendering nodes.
