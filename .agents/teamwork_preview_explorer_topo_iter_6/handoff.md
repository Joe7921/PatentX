# Handoff Report: Dynamic Topo UI Fix Strategy

## Observation
- **Integrity Violation**: The previous worker created/wired up `frontend/src/components/DraftingPiP.tsx` (which lacks the `drag` property from `framer-motion`) instead of transforming the existing `frontend/src/components/DocumentPreview.tsx`. `DocumentPreview.tsx` remains as the original static view.
- **String Concatenation Bottleneck**: Both `DocumentPreview.tsx` (line 10) and `DraftingPiP.tsx` (line 16) use `documentChunks.join('')` on every render, which is an O(N^2) operation when chunks stream in frequently, blocking the main thread.
- **Raw Text in PiP**: `DraftingPiP.tsx` renders the joined string directly inside a `div` (line 110) rather than using a Markdown parser.
- **Lack of Virtualization**: `frontend/src/components/DynamicTopoGraph.tsx` maps over all `topologyNodes` (line 60) and renders them in a flex container without any virtualization, causing DOM bloat and frame drops when the node count grows.

## Logic Chain
1. To resolve the integrity violation, `DraftingPiP.tsx` should be deleted, and all PiP functionalities (including the `drag` property from `framer-motion`) must be implemented directly inside `DocumentPreview.tsx`.
2. To fix the main thread blocking issue from O(N^2) string concatenation, we must replace the `join('')` call. Since the state is an array of chunks, we can use a `useEffect` with a `ref` tracking the last processed index to incrementally append new chunks to a local `text` state. Incremental appending avoids re-joining the entire array on every render.
3. Rendering raw text in the PiP is solved by retaining and using the `ReactMarkdown` component (currently in `DocumentPreview.tsx`) in the newly transformed draggable PiP.
4. To eliminate frame drops in `DynamicTopoGraph.tsx`, the horizontal node list must be virtualized. By wrapping the flex container with a virtualization library (like `@tanstack/react-virtual`'s `useVirtualizer` configured for horizontal scrolling), only the nodes currently in the viewport will be rendered.

## Caveats
- Using `@tanstack/react-virtual` or `react-window` requires adding a new dependency to the `frontend/package.json` if it's not already installed.
- Implementing the `drag` property on `motion.div` might require configuring `dragConstraints` to prevent the PiP from being dragged out of the visible screen area.
- Incremental string concatenation in a React state (`useState`) might still trigger large React re-renders for massive strings; if performance is still an issue, we might need a direct DOM ref update for the streaming text, but local state incrementing is a necessary first step over `join('')`.

## Conclusion
A complete fix involves:
1. Deleting `DraftingPiP.tsx`.
2. Refactoring `DocumentPreview.tsx` to serve as a Draggable PiP. Wrap its outer container in a `<motion.div drag dragMomentum={false} ...>` component to enable free dragging.
3. Inside `DocumentPreview.tsx`, replace `const text = documentChunks.join('')` with an incremental string builder (`useEffect` that appends `chunks.slice(lastIndex.current).join('')` to a local string state).
4. Ensure `DocumentPreview.tsx` continues to use `<ReactMarkdown>` to render the text content.
5. In `DynamicTopoGraph.tsx`, replace the static `.map` of `topologyNodes` with a horizontal virtualized list (e.g., using `@tanstack/react-virtual`), ensuring only visible nodes are mounted in the DOM.

## Verification Method
- **Integrity**: Verify `DraftingPiP.tsx` is deleted and `DocumentPreview.tsx` contains `<motion.div drag...>` for PiP capabilities.
- **Performance**: Monitor the performance tab during text streaming; there should be no O(N^2) long tasks from `join('')`.
- **Markdown**: Inject Markdown text (e.g., `**bold**`) into the chunks and confirm it renders visually bold in the PiP instead of showing raw asterisks.
- **Virtualization**: Inspect the DOM in dev tools for `DynamicTopoGraph.tsx` while scrolling horizontally with 100+ nodes; the number of child DOM nodes should remain constant (only visible nodes + buffer).
