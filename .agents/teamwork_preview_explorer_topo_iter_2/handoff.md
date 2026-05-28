# 1. Observation
- `PROJECT.md` 规定里程碑 1 为 "Dynamic Topo UI"，需要创建 `DynamicTopoGraph.tsx`，将 `DocumentPreview.tsx` 改造为 PiP（画中画）模式，并在 `App.tsx` 中完成总装。
- 检索前端代码发现，`frontend/src/store/useStore.ts` 已经实现并维护了完整的 `agenticState`，其中包含 `topologyNodes` 和 `topologyEdges`（节点与连线状态），以及专利流式生成的 `documentChunks`。
- 当前代码库已存在 `AgenticTopology.tsx`（实现了一个基础水平滚动节点展示）和 `DraftingPiP.tsx`（实现了一个基本的画中画弹出窗口）。而旧的 `DocumentPreview.tsx` 仍然是一个标准的长列表组件。
- `App.tsx` 已经移除了 SplitPane，并且当前代码引入了 `<AgenticTopology />`（中心展示）和 `<DraftingPiP />`（全局挂载）。

# 2. Logic Chain
- 鉴于 `useStore.ts` 的后端状态接收逻辑和 `agenticState` 已经完备，UI 层的核心工作在于**消费已有状态**并利用 `framer-motion` + Tailwind 完成高质量的可视化动画与交互布局。
- **Topo UI (拓扑图) 策略**：
  - 需要将新设计的 `DynamicTopoGraph.tsx` 替换或升级现有的 `AgenticTopology.tsx`。
  - 从 `useStore` 读取 `agenticState.topologyNodes`，映射为带动画的卡片。可使用 `framer-motion` 的 `<AnimatePresence>` 及 `layout` 属性管理节点的入场（`opacity: 0, scale: 0.8` -> `opacity: 1, scale: 1`）、状态跃迁（Active 时发光高亮）、完成时的过渡动画。
  - 动态连线（Edges）：利用 CSS 或 SVG `<motion.path>` 将 `topologyEdges` 转化为线条，通过 `strokeDasharray` 和 `strokeDashoffset` 实现流动的管线动画。
  - 交互：节点点击展示右侧面板（已在原型中有体现，需要完善），实时显示节点的详细日志内容（`node.content`）。
- **PiP Window (画中画窗口) 策略**：
  - 由于当前的 `DocumentPreview.tsx` 设计为占据全画幅的常规区块，需要将其逻辑（Markdown 渲染、Auto-scroll、中英文 Tab）迁移整合至类似 `DraftingPiP.tsx` 的设计中，彻底重构或重命名组件以符合需求。
  - PiP UI 需具备两套形态：**折叠态**（右下角悬浮悬停小窗，利用 `framer-motion` 实现发光、呼吸灯效果以指示流生成状态）、**展开态**（居中大尺寸模态框或可拖拽窗口）。
  - 使用 `framer-motion` 的 `layoutId` 绑定外层容器，实现从折叠小窗平滑弹射变大为完整预览窗口的神奇位移（Magic Motion）动画。
- **App.tsx 组装策略**：
  - 保证在 `step === 'THINKING'` 或 `step === 'PAUSED'` 时主渲染区全屏居中展示 `DynamicTopoGraph`。
  - 根层级底部固定 `<DocumentPreview />` (PiP 版本)，保证即使拓扑图切换也能全局悬浮查看流式草案。

# 3. Caveats
- `framer-motion` 的 `layoutId` 如果滥用或组件层级变化过快，可能导致 DOM 渲染抖动，建议在 PiP 的两种状态切换时确保 DOM 树结构相似。
- SVG 动态连线如与纯 Flex 布局强耦合，在节点数量激增出现滚动条时可能错位。可以考虑直接在 flex 元素间插入动画 divider，或使用 `ReactFlow`，但为了轻量和定制化，当前横向 Flex + Spacer 的方案较为可控，只需强化动画效果。
- 没有实际修改代码，相关组件需交由后续实现阶段。

# 4. Conclusion
**推荐实现策略如下：**
1. **重构/创建 `DynamicTopoGraph.tsx`**：全面接管 `AgenticTopology.tsx`。使用 `flex-row` 水平容器，内部用 `<AnimatePresence>` 挂载所有节点。使用 Tailwind 实现节点发光 (`pulse-glow-active`) 和基于 Agent 角色的彩色边框。
2. **改造 `DocumentPreview.tsx` 为 PiP**：融合 `DraftingPiP` 与 `DocumentPreview` 的功能。默认呈现右下角吸附小卡片（包含生成进度指示），点击触发 `framer-motion` 的 `layout` 动画，展开为带有完整 Markdown 渲染和中英文 Tab 切换的大窗。
3. **状态绑定**：直接从 `useStore` 解构出 `topologyNodes`, `topologyEdges`, `documentChunks`。
4. **组装**：清理 `App.tsx`，确认不再使用 Split 布局，保持顶部居中展示拓扑，右下角展示 PiP。

# 5. Verification Method
- 实施后执行 `npm run build` 和 `npm run dev`。
- 在页面中上传或提交测试内容触发 `THINKING` 状态。
- **验证拓扑图**：观察是否有节点随 SSE 数据逐个弹出，并且有清晰的入场动画；连线是否依次连接；点击节点是否展示右侧面板。
- **验证画中画**：右下角应有悬浮的指示器卡片；点击指示器卡片是否使用丝滑的补间动画（Motion）放大成为阅读窗口；文本是否继续在窗口内流式输出且自动滚动。
