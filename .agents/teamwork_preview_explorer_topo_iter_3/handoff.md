# Handoff Report: Dynamic Topo UI & PiP Drafting Strategy

## 1. Observation
- The global state is managed by `useStore.ts`. It stores the topological structure under `agenticState.topologyNodes` and `agenticState.topologyEdges`. The real-time document chunks are streamed into `documentChunks`.
- `App.tsx` controls the main view routing based on the `step` variable (`UPLOAD`, `THINKING`, `PAUSED`, `DASHBOARD`).
- The milestone requires creating a Dynamic Topo Graph UI, turning the Document Preview into a floating Picture-in-Picture (PiP) window, and wiring them into `App.tsx`.
- (Note: Based on local file inspection, implementations resembling this strategy currently exist in `AgenticTopology.tsx` and `DraftingPiP.tsx`. This strategy validates and standardizes their design pattern for the milestone.)

## 2. Logic Chain

### A. Dynamic Topo UI Strategy
1. **Component Creation**: Create `DynamicTopoGraph.tsx` (or update `AgenticTopology.tsx`).
2. **Data Binding**: Subscribe to `topologyNodes` and `topologyEdges` from `useStore`.
3. **Layout**: Use a horizontally scrolling flex container to display the nodes. Auto-scroll to the right (`scrollLeft = scrollWidth`) using a `useEffect` hooked to the `topologyNodes.length`.
4. **Animation (`framer-motion`)**:
   - Wrap the node list in `<AnimatePresence>`.
   - **Nodes**: Use `<motion.div>` with `initial={{ scale: 0.8, opacity: 0 }}` and `animate={{ scale: 1, opacity: 1 }}` for entrance.
   - **Edges**: Render a connecting `<motion.div>` between nodes that animates width from 0 to full size.
   - **Active State**: Apply a custom CSS keyframe animation (`pulse-glow-active`) to the node where `status === 'active'`.
5. **Interactivity**: Clicking a node sets it as `selectedNode` in local state. This triggers a right-hand sliding side-panel (also animated via `framer-motion` `x: "100%" -> 0`) to display the `node.content` (e.g., raw agent outputs or tool logs).

### B. PiP Drafting Window Strategy
1. **Component Creation**: Create `DraftingPiP.tsx` (or update `DocumentPreview.tsx` to include PiP capabilities).
2. **Data Binding**: Subscribe to `documentChunks` and `isDraftingComplete` from `useStore`.
3. **State Management**: Use local state `isExpanded` (boolean) to track whether the UI is in the minimized PiP state or expanded reading state.
4. **Animation (`framer-motion` morphing)**:
   - Use `layoutId="pip-container"` on both the minimized and expanded wrappers. This allows `framer-motion` to smoothly morph between the small floating card and the large modal.
   - **Minimized State**: `fixed bottom-6 right-6 w-64`. Render a pulsing indicator if `!isDraftingComplete`.
   - **Expanded State**: Full-screen backdrop `fixed inset-0` with a centered `max-w-3xl` modal. Use `react-markdown` to render the joined `documentChunks`.
   - Auto-scroll the expanded view downwards as chunks arrive.

### C. Wiring in `App.tsx`
1. **Topology Placement**: Replace the static center hub in the `THINKING` and `PAUSED` steps with `<DynamicTopoGraph />`.
2. **PiP Placement**: Mount `<DraftingPiP />` globally at the bottom of the `App.tsx` render tree. This ensures the PiP window can float over *any* step (e.g., if the user reaches `DASHBOARD` while drafting is still streaming in the background).

## 3. Caveats
- **Overflow and Scaling**: If the topology graph gets extremely long, the horizontal scrolling approach might become visually overwhelming. We assume a linear or lightly branched workflow for now.
- **Z-Index Conflicts**: The PiP window and the node detail side-panel both use fixed positioning. Ensure the PiP window has an appropriate `z-index` (e.g., 50) and handles click-away so they don't block each other awkwardly.

## 4. Conclusion
The recommended strategy is a frontend-only layer mapping `useStore` arrays directly to `framer-motion` components. The topology uses a horizontal flex track with entrance animations and a slide-out details pane. The PiP window uses `layoutId` morphing to transition between a floating bottom-right indicator and a centered markdown reader. Both components should be injected into `App.tsx`—the topology tied to specific steps, and the PiP mounted globally.

## 5. Verification Method
1. Create/Update the components based on the above strategy.
2. Run the development server (`npm run dev` or equivalent) and trigger the patent evaluation workflow.
3. Observe the Topo Graph: New nodes should animate in from the right, and active nodes should pulse. Clicking a node should open the side panel.
4. Observe the PiP Window: It should appear in the bottom right while drafting, morph into a large window when clicked, and stream markdown content.
