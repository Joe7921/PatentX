# Handoff Report: Dynamic Topo UI Fix Strategy

## Observation
1. **Integrity Violation**: `DocumentPreview.tsx` remains a full-page layout component, while a new file `DraftingPiP.tsx` was created to implement the Picture-in-Picture feature. The `DraftingPiP.tsx` implementation lacks the `drag` prop on its `framer-motion` container, making it non-draggable.
2. **O(N^2) String Concatenation**: In `useStore.ts`, streamed text chunks are stored as an array (`documentChunks: string[]`). Every chunk triggers a state update appending to the array. Components then call `documentChunks.join('')` on every render. With `N` chunks, this concatenation takes `O(N)` per render and `O(N^2)` total time, blocking the main thread.
3. **Markdown Rendering**: `DraftingPiP.tsx` renders raw text (`{content}`) directly within a generic `div`, entirely discarding the `ReactMarkdown` parser that was previously utilized in `DocumentPreview.tsx`.
4. **Virtualization Missing**: `DynamicTopoGraph.tsx` natively maps over the full `topologyNodes` array (lines 60-98) inside a flex container. It relies entirely on DOM overflow scrolling, dropping frames due to layout and animation thrashing when the node count grows large.

## Logic Chain
1. The project requirement was to *transform* `DocumentPreview.tsx` into a PiP, rather than creating a secondary component. Merging the PiP state logic (expanded/collapsed) from `DraftingPiP.tsx` into `DocumentPreview.tsx` and removing the redundant `DraftingPiP.tsx` file restores design integrity.
2. The PiP needs to be movable. Adding the `drag` and `dragMomentum={false}` props to the absolute/fixed `<motion.div>` in `DocumentPreview.tsx` enables Framer Motion's drag capabilities.
3. The string concatenation bottleneck occurs because React renders call `.join('')` on a constantly expanding array. By refactoring the Zustand store (`useStore.ts`) to use a single `documentText: string` and appending chunks natively (`documentText: state.documentText + data.chunk`), we leverage V8's string builder optimizations and completely eliminate the `join('')` computation during render.
4. Rendering raw Markdown syntax degrades the UI. Restoring the use of `ReactMarkdown` (already present in `DocumentPreview.tsx`) inside the new PiP layout ensures standard formatting.
5. Unbounded list rendering tanks framerates. Wrapping the node mapping in `DynamicTopoGraph.tsx` with a horizontal virtualizer (e.g., `@tanstack/react-virtual` or a custom scroll-based culler) ensures only visible nodes are mounted in the DOM, preserving smooth animation performance regardless of history length.

## Caveats
- Using `@tanstack/react-virtual` may require adding the package to dependencies. If adding new dependencies is not permitted, a manual windowing calculation using `containerRef.current.scrollLeft` and fixed node widths (e.g., 144px per node) is required.
- Adding `drag` to the entire PiP modal might interfere with internal text selection or scrolling. It's recommended to constrain dragging by using a `dragControls` instance or applying the drag listener specifically to the modal's header element.
- Since `DraftingPiP.tsx` was wired up elsewhere, any parent layout or dashboard component importing it must be updated to import and use the refactored `DocumentPreview.tsx`.

## Conclusion
To address all failures, implement the following strategy:
1. **Refactor `DocumentPreview.tsx` & Restore Integrity**: Move the PiP states (`isExpanded`, `isDismissed`) and modal DOM structure from `DraftingPiP.tsx` into `DocumentPreview.tsx`. Delete `DraftingPiP.tsx` and update imports. Add `drag` to the floating `motion.div`. Use `ReactMarkdown` for text display.
2. **Resolve Main Thread Bottleneck**: In `useStore.ts`, change `documentChunks: string[]` to `documentText: string`. In the `document_chunk` event handler, update state via `documentText: state.documentText + data.chunk`. Consume this optimized string directly in the UI.
3. **Virtualize Topo Graph**: In `DynamicTopoGraph.tsx`, implement a horizontal virtual list (via `@tanstack/react-virtual` or manual culling) to only mount `TopologyNode` elements that fall within the container's visible bounds.

## Verification Method
1. **Integrity & Drag**: Inspect `src/components/`. Verify `DraftingPiP.tsx` is deleted. Open the app and observe `DocumentPreview.tsx` appearing as a PiP widget. Click and drag the widget; it must move smoothly across the viewport.
2. **Performance Check**: Run the streaming draft action. Monitor the Chrome DevTools Performance tab and verify that there are no long tasks related to string `.join()` operations blocking the main thread.
3. **Markdown**: Check the streamed text in the PiP widget; it should render lists and bold styling correctly, not raw Markdown syntax.
4. **Virtualization**: Create a topology with >100 nodes. Inspect the DOM within `DynamicTopoGraph`. As you scroll horizontally, only the currently visible nodes (and a small overscan buffer) should exist in the DOM structure.
