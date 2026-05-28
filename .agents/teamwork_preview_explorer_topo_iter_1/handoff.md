# Handoff Report

## 1. Observation
- `App.tsx` has already been partially refactored to remove the split pane, currently rendering `<AgenticTopology />` and `<DraftingPiP />` in a full-screen layout.
- `src/components/AgenticTopology.tsx` currently renders `agenticState.topologyNodes` as a 1D horizontal scrolling list (`flex space-x-6`), not a true 2D topological graph with branches.
- `src/components/DraftingPiP.tsx` exists as a floating window (`fixed bottom-6 right-6`), but it lacks the requested drag capability.
- `src/components/DocumentPreview.tsx` still exists but is currently unused in `App.tsx`. 
- `src/store/useStore.ts` and `src/store/agenticTypes.ts` already construct `topologyNodes` and `topologyEdges` from SSE events (phases, agents, tools). Nodes have a `parentId` which defines the graph hierarchy.

## 2. Logic Chain
1. **Dynamic Topo Graph**: The milestone requires `DynamicTopoGraph.tsx`. Since `AgenticTopology.tsx` is just a 1D list, we should create a true `DynamicTopoGraph.tsx`. Because `topologyNodes` have `parentId` references, we can compute 2D positions (x,y) for each node (e.g., using a simple level-based layout) and render them as absolute `motion.div` elements. Edges can be drawn using an `<svg>` overlay with `<motion.path>` connecting the node coordinates.
2. **PiP Drafting Window**: The scope explicitly states to "update `DocumentPreview.tsx` to PiP". We should migrate the PiP UI logic (currently in `DraftingPiP.tsx`) back into `DocumentPreview.tsx` and enhance it with framer-motion's `drag` prop (`<motion.div drag dragMomentum={false} dragConstraints={...}>`) to satisfy the "draggable" requirement. `DraftingPiP.tsx` can then be safely removed.
3. **Wiring in App.tsx**: Replace `AgenticTopology` with `DynamicTopoGraph`. Replace `DraftingPiP` with the updated `DocumentPreview`. Pass the `agenticState` from `useStore` to the topo graph to drive the framer-motion animations.

## 3. Caveats
- Building a full 2D layout engine from scratch using just `framer-motion` requires a coordinate calculation step (e.g., assigning a depth/level to each node based on `parentId`). The implementer will need to add a simple tree layout function before rendering the nodes.
- When `DocumentPreview` becomes draggable, it must have `dragListener` set on a specific header handle to prevent text-selection from triggering drags accidentally.

## 4. Conclusion
**Implementation Strategy:**
1. **Create `src/components/DynamicTopoGraph.tsx`**:
   - Subscribe to `useStore((state) => state.agenticState)`.
   - Compute X, Y coordinates for `topologyNodes` based on their `parentId`.
   - Render nodes using `<motion.div layout initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}>`.
   - Render edges using an absolute `<svg>` layer with `<motion.path>` connecting the calculated center points of nodes.
   - Retain the drawer click logic to view detailed logs.
2. **Update `src/components/DocumentPreview.tsx`**:
   - Transform it into a floating window using `<motion.div className="fixed ..." drag dragMomentum={false}>`.
   - Incorporate the collapse/expand logic from `DraftingPiP.tsx`.
   - Delete `DraftingPiP.tsx` to clean up redundancy.
3. **Update `src/App.tsx`**:
   - Import `DynamicTopoGraph` and `DocumentPreview`.
   - Mount `DynamicTopoGraph` in the main container and `DocumentPreview` globally as the floating PiP.

## 5. Verification Method
1. Ensure the code compiles and builds successfully via `npm run build`.
2. Run the frontend application and trigger a patent analysis.
3. Visually verify that the `DynamicTopoGraph` branches out in a 2D space (e.g., multiple agents stemming from a single phase).
4. Verify that the `DocumentPreview` PiP window can be dragged across the screen and can expand/collapse without layout breaking.
