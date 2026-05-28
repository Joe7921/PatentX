# 水平树状 SVG 拓扑布局算法设计报告

> **类型**: Hard Handoff  
> **日期**: 2026-05-26T21:26:00+08:00  
> **角色**: Explorer（只读分析，不实施代码）

---

## 核心摘要

将 `DynamicTopoGraph.tsx` 从垂直缩进 div 目录树改造为水平 SVG 拓扑网络图。设计基于 **Reingold-Tilford 算法的水平变体**，纯 TypeScript 实现，零外部依赖。方向从左到右（根节点最左），同父子节点垂直居中排列，通过水平贝塞尔曲线连接。

---

## 1. Observation — 现有代码分析

### 1.1 现有组件结构

**`DynamicTopoGraph.tsx`**（140行）：
- 从 Zustand store 取 `agenticState.topologyNodes`（第12行）
- 通过 `parentId` 递归渲染树结构（第22-111行 `renderNode`）
- 根节点查找：`nodes.find(n => n.parentId === undefined)`（第115行）
- 子节点查找：`nodes.filter(n => n.parentId === node.id)`（第24行）
- 垂直缩进布局，使用 `pl-6 ml-[22px] border-l` CSS 实现嵌套
- 每个 active 节点下嵌入 `<LiveInterventionInput />`（第92-98行）
- 无 props，数据完全来自 store

**`agenticTypes.ts`**（第147-165行）：
```typescript
interface TopologyNode {
  id: string;
  type: 'system' | 'phase' | 'agent' | 'tool';
  status: 'pending' | 'active' | 'completed';
  label: string;
  agentId?: string;
  toolName?: string;
  content?: string;
  parentId?: string;   // 树关系的唯一方式
  timestamp: number;
}

interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  status: 'active' | 'completed';
}
```

### 1.2 使用场景

| 位置 | 文件 | 容器约束 |
|------|------|----------|
| 左侧栏 | `App.tsx:68-70` | `w-[40%]` ≈ 500-600px，全高，`overflow-y-auto` |
| Dashboard折叠 | `DiagnosticDashboard.tsx:82-84` | `max-h-[600px]`，`overflow-y-auto` |

### 1.3 树构建时序（`useStore.ts`）

节点通过 SSE 事件动态追加：
- `phase_start` → 创建 `phase_*` 节点，parentId = `root_system`（第145-154行）
- `agent_think` → 创建 `agent_*` 节点，parentId = `phase_*`（第193-211行）
- `agent_act` → 创建 `tool_*` 节点，parentId = 最近的 agent（第214-233行）
- `agent_observe` → 更新最近 tool 节点内容（第235-240行）

典型树结构：
```
root_system (system)
├── phase_1 (phase)
│   ├── agent_first_examiner_xxx (agent)
│   │   ├── tool_search_patent_xxx (tool)
│   │   └── tool_analyze_xxx (tool)
│   └── agent_second_examiner_xxx (agent)
│       └── tool_compare_xxx (tool)
├── phase_2 (phase)
│   └── agent_chairman_xxx (agent)
└── phase_3 (phase)
    └── ...
```

---

## 2. Logic Chain — 布局算法设计

### 2.1 常量配置对象

```typescript
/** 拓扑图布局常量配置 */
export const TOPO_LAYOUT_CONFIG = {
  /** 节点尺寸（宽 × 高），单位: px */
  nodeSize: {
    system: { width: 160, height: 52 },
    phase:  { width: 150, height: 48 },
    agent:  { width: 140, height: 44 },
    tool:   { width: 120, height: 36 },
  },

  /** 间距配置 */
  spacing: {
    /** 相邻层级之间的水平间距（父→子） */
    levelGap: 80,
    /** 同一父节点下相邻兄弟之间的垂直间距 */
    siblingGap: 16,
    /** 不同子树之间的额外垂直间距 */
    subtreeGap: 24,
  },

  /** 画布内边距 */
  padding: {
    top: 30,
    right: 40,
    bottom: 30,
    left: 30,
  },

  /** 连线配置 */
  edge: {
    /** 贝塞尔曲线的水平控制点偏移比例 (0-1, 相对于源目标水平距离) */
    bezierControlRatio: 0.5,
    /** 线宽 */
    strokeWidth: 1.5,
    /** active 状态连线颜色 */
    activeColor: '#3B82F6',
    /** completed 状态连线颜色 */
    completedColor: '#CBD5E1',
  },

  /** 节点圆角半径 */
  borderRadius: 12,

  /** 节点状态色配 */
  statusColors: {
    active:    { fill: '#EFF6FF', stroke: '#3B82F6', text: '#1E40AF' },
    completed: { fill: '#F8FAFC', stroke: '#CBD5E1', text: '#64748B' },
    pending:   { fill: '#FAFAFA', stroke: '#E2E8F0', text: '#94A3B8' },
  },
} as const;

/** 布局配置类型 */
export type TopoLayoutConfig = typeof TOPO_LAYOUT_CONFIG;
```

### 2.2 内部数据结构

```typescript
/** 布局计算所需的内部树节点 */
interface LayoutTreeNode {
  /** 原始拓扑节点引用 */
  node: TopologyNode;
  /** 子节点 */
  children: LayoutTreeNode[];
  /** 层级深度（根 = 0） */
  depth: number;
  /** 布局计算后的坐标（节点左上角） */
  x: number;
  y: number;
  /** 基于类型的节点尺寸 */
  width: number;
  height: number;
  /** 以此节点为根的子树的高度占用（含所有后代节点 + 间距） */
  subtreeHeight: number;
}

/** 布局结果：每个节点的定位信息 */
export interface NodeLayout {
  nodeId: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

/** 连线路径 */
export interface EdgePath {
  edgeId: string;
  sourceId: string;
  targetId: string;
  path: string;        // SVG path d 属性值
  status: 'active' | 'completed';
}

/** 布局计算完整结果 */
export interface LayoutResult {
  nodes: NodeLayout[];
  edges: EdgePath[];
  /** 画布总宽度 (包含 padding) */
  canvasWidth: number;
  /** 画布总高度 (包含 padding) */
  canvasHeight: number;
}
```

### 2.3 布局算法详细设计

算法分为 4 个步骤：**构建树 → 计算子树高度 → 分配坐标 → 生成连线**。

#### 步骤 1：从扁平数组构建树

```typescript
/**
 * 从扁平 TopologyNode[] 构建树结构
 * 时间复杂度 O(n)，空间复杂度 O(n)
 */
function buildTree(
  nodes: TopologyNode[],
  config: TopoLayoutConfig
): LayoutTreeNode | null {
  if (nodes.length === 0) return null;

  // 构建 id → LayoutTreeNode 映射
  const nodeMap = new Map<string, LayoutTreeNode>();

  for (const node of nodes) {
    const size = config.nodeSize[node.type];
    nodeMap.set(node.id, {
      node,
      children: [],
      depth: 0,
      x: 0,
      y: 0,
      width: size.width,
      height: size.height,
      subtreeHeight: 0,
    });
  }

  // 寻找根节点，建立父子关系
  let root: LayoutTreeNode | null = null;

  for (const node of nodes) {
    const layoutNode = nodeMap.get(node.id)!;
    if (node.parentId === undefined || node.parentId === null) {
      root = layoutNode;
    } else {
      const parent = nodeMap.get(node.parentId);
      if (parent) {
        parent.children.push(layoutNode);
      } else {
        // parentId 指向不存在的节点，作为额外根处理
        // 实际场景中应该不会发生，但做防御性处理
        if (!root) root = layoutNode;
      }
    }
  }

  // 如果没找到根节点（所有节点都有 parentId），取第一个
  if (!root && nodes.length > 0) {
    root = nodeMap.get(nodes[0].id)!;
  }

  // 计算深度
  function setDepth(treeNode: LayoutTreeNode, depth: number) {
    treeNode.depth = depth;
    for (const child of treeNode.children) {
      setDepth(child, depth + 1);
    }
  }
  if (root) setDepth(root, 0);

  return root;
}
```

#### 步骤 2：自底向上计算子树高度

```typescript
/**
 * 自底向上计算每个节点的子树高度占用
 * 
 * 叶子节点的 subtreeHeight = 自身 height
 * 有子节点时 subtreeHeight = max(自身 height, 所有子节点 subtreeHeight 之和 + (n-1) * siblingGap)
 * 
 * 这确保了任何子树的空间分配足以容纳所有后代而不重叠
 */
function computeSubtreeHeights(
  treeNode: LayoutTreeNode,
  config: TopoLayoutConfig
): void {
  if (treeNode.children.length === 0) {
    // 叶子节点：子树高度就是自身高度
    treeNode.subtreeHeight = treeNode.height;
    return;
  }

  // 递归处理所有子节点
  for (const child of treeNode.children) {
    computeSubtreeHeights(child, config);
  }

  // 子节点子树高度总和 + 兄弟间距
  const childrenTotalHeight = treeNode.children.reduce(
    (sum, child) => sum + child.subtreeHeight,
    0
  ) + (treeNode.children.length - 1) * config.spacing.siblingGap;

  // 子树高度取子节点总高和自身高度的最大值
  treeNode.subtreeHeight = Math.max(treeNode.height, childrenTotalHeight);
}
```

#### 步骤 3：自顶向下分配坐标

```typescript
/**
 * 自顶向下分配每个节点的 (x, y) 坐标
 * 
 * X 坐标：由层级深度决定
 *   x = padding.left + depth * (maxNodeWidthAtThisLevel + levelGap)
 *   简化实现：x = padding.left + depth * (maxNodeWidth + levelGap)
 *   
 * Y 坐标：在分配的子树空间内居中
 *   父节点将其子树总空间按子节点的 subtreeHeight 分配
 *   每个子节点在其分配空间内垂直居中
 */
function assignPositions(
  treeNode: LayoutTreeNode,
  startY: number,
  config: TopoLayoutConfig
): void {
  const { levelGap } = config.spacing;
  const { left } = config.padding;

  // X 坐标：深度 * (该节点宽度对应层级的水平推进)
  // 为保持对齐美观，使用每层最大宽度来统一列位置
  // 但更简洁的做法：直接用 depth * (固定列宽 + levelGap)
  // 固定列宽取所有节点类型的最大宽度（system=160）
  const columnWidth = Math.max(
    ...Object.values(config.nodeSize).map(s => s.width)
  );
  treeNode.x = left + treeNode.depth * (columnWidth + levelGap);

  // Y 坐标：在分配区间 [startY, startY + subtreeHeight) 内居中
  treeNode.y = startY + (treeNode.subtreeHeight - treeNode.height) / 2;

  // 为子节点分配垂直空间
  if (treeNode.children.length > 0) {
    // 子节点总高度（含间距）
    const childrenTotalHeight = treeNode.children.reduce(
      (sum, child) => sum + child.subtreeHeight,
      0
    ) + (treeNode.children.length - 1) * config.spacing.siblingGap;

    // 子节点组在父节点子树空间内居中
    let currentY = startY + (treeNode.subtreeHeight - childrenTotalHeight) / 2;

    for (const child of treeNode.children) {
      assignPositions(child, currentY, config);
      currentY += child.subtreeHeight + config.spacing.siblingGap;
    }
  }
}
```

#### 步骤 4：收集布局结果并生成连线

```typescript
/**
 * 遍历树收集所有节点布局和连线路径
 */
function collectLayout(
  treeNode: LayoutTreeNode,
  edges: TopologyEdge[],
  config: TopoLayoutConfig
): LayoutResult {
  const nodeLayouts: NodeLayout[] = [];
  const edgePaths: EdgePath[] = [];
  
  // 建立 id → 位置映射（遍历一次收集所有节点）
  const posMap = new Map<string, LayoutTreeNode>();

  function collectNodes(tn: LayoutTreeNode) {
    nodeLayouts.push({
      nodeId: tn.node.id,
      x: tn.x,
      y: tn.y,
      width: tn.width,
      height: tn.height,
    });
    posMap.set(tn.node.id, tn);
    for (const child of tn.children) {
      collectNodes(child);
    }
  }
  collectNodes(treeNode);

  // 根据 edges 数组生成连线路径
  for (const edge of edges) {
    const src = posMap.get(edge.source);
    const tgt = posMap.get(edge.target);
    if (!src || !tgt) continue;

    const path = computeBezierPath(src, tgt, config);
    edgePaths.push({
      edgeId: edge.id,
      sourceId: edge.source,
      targetId: edge.target,
      path,
      status: edge.status,
    });
  }

  // 计算画布尺寸
  let maxX = 0;
  let maxY = 0;
  for (const nl of nodeLayouts) {
    maxX = Math.max(maxX, nl.x + nl.width);
    maxY = Math.max(maxY, nl.y + nl.height);
  }

  return {
    nodes: nodeLayouts,
    edges: edgePaths,
    canvasWidth: maxX + config.padding.right,
    canvasHeight: maxY + config.padding.bottom,
  };
}
```

### 2.4 主入口函数

```typescript
/**
 * 水平树状布局算法主入口
 * 
 * @param nodes  扁平的拓扑节点数组（通过 parentId 隐含树结构）
 * @param edges  拓扑连线数组
 * @param config 布局配置（可选，默认使用 TOPO_LAYOUT_CONFIG）
 * @returns      布局结果，包含每个节点的坐标和每条连线的 SVG path
 */
export function computeTopoLayout(
  nodes: TopologyNode[],
  edges: TopologyEdge[],
  config: TopoLayoutConfig = TOPO_LAYOUT_CONFIG
): LayoutResult {
  // 步骤 1：构建树
  const root = buildTree(nodes, config);
  if (!root) {
    return { nodes: [], edges: [], canvasWidth: 0, canvasHeight: 0 };
  }

  // 步骤 2：计算子树高度
  computeSubtreeHeights(root, config);

  // 步骤 3：分配坐标
  assignPositions(root, config.padding.top, config);

  // 步骤 4：收集结果并生成连线
  return collectLayout(root, edges, config);
}
```

### 2.5 性能优化：useMemo 缓存

```typescript
// 在 React 组件中使用
const layout = useMemo(
  () => computeTopoLayout(
    agenticState.topologyNodes,
    agenticState.topologyEdges
  ),
  [agenticState.topologyNodes, agenticState.topologyEdges]
);
```

由于 `topologyNodes` 和 `topologyEdges` 在 Zustand store 中每次事件都创建新数组引用，`useMemo` 会在每次 SSE 事件时重新计算。这是正确的行为——布局需要在新节点加入时更新。

典型场景下节点数量 < 50，算法为 O(n)，无性能隐患。

---

## 3. 贝塞尔曲线路径计算

### 3.1 连接点位置

```
源节点右侧中点 → 目标节点左侧中点

  ┌──────────┐                        ┌──────────┐
  │  source   ●─── 贝塞尔曲线 ────────●  target   │
  └──────────┘                        └──────────┘
           (sx, sy)                (tx, ty)

sx = source.x + source.width     （源节点右边缘）
sy = source.y + source.height/2  （源节点垂直中点）
tx = target.x                    （目标节点左边缘）
ty = target.y + target.height/2  （目标节点垂直中点）
```

### 3.2 路径计算函数

```typescript
/**
 * 计算两节点之间的水平贝塞尔曲线 SVG path 字符串
 * 
 * 使用三次贝塞尔曲线(C)，两个控制点在水平方向偏移，
 * 形成流畅的 S 型连线，垂直方向不引入抖动
 */
function computeBezierPath(
  source: LayoutTreeNode,
  target: LayoutTreeNode,
  config: TopoLayoutConfig
): string {
  // 源节点右侧中点
  const sx = source.x + source.width;
  const sy = source.y + source.height / 2;

  // 目标节点左侧中点
  const tx = target.x;
  const ty = target.y + target.height / 2;

  // 水平距离
  const dx = tx - sx;

  // 控制点水平偏移量
  const cpOffset = dx * config.edge.bezierControlRatio;

  // 两个控制点：
  // CP1: (sx + cpOffset, sy)  —— 从源出发，先水平延伸
  // CP2: (tx - cpOffset, ty)  —— 到达目标前，水平收回
  const cp1x = sx + cpOffset;
  const cp1y = sy;
  const cp2x = tx - cpOffset;
  const cp2y = ty;

  return `M ${sx} ${sy} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${tx} ${ty}`;
}
```

### 3.3 曲线效果说明

```
当 source 和 target 在同一水平线时（sy === ty）：
  曲线退化为直线（CP1和CP2的y坐标相同）→ 视觉上是平滑直线

当 source 和 target 有垂直偏移时：
  M ─→ CP1 (水平) ─→ CP2 (水平) ─→ T
  形成 优雅的 S 型曲线

bezierControlRatio = 0.5 时示意:

  source ●─────╮
                │  ← 控制点在中间，形成对称 S
                ╰─────● target
```

### 3.4 framer-motion 连线动画

```tsx
// 在 SVG 中使用 motion.path 实现 pathLength 动画
<motion.path
  d={edgePath.path}
  fill="none"
  stroke={
    edgePath.status === 'active'
      ? config.edge.activeColor
      : config.edge.completedColor
  }
  strokeWidth={config.edge.strokeWidth}
  // pathLength 动画：线条从 0 到 1 "画出来"
  initial={{ pathLength: 0, opacity: 0 }}
  animate={{ pathLength: 1, opacity: 1 }}
  transition={{ duration: 0.5, ease: 'easeOut' }}
/>
```

---

## 4. 文件组织建议

### 4.1 新增文件结构

```
frontend/src/
├── components/
│   ├── DynamicTopoGraph.tsx        ← 主组件（重写：SVG + foreignObject）
│   └── topo/                       ← 新建文件夹
│       ├── topoLayoutEngine.ts     ← 布局算法（纯逻辑，无 React 依赖）
│       ├── topoTypes.ts            ← 布局专用类型（NodeLayout, EdgePath, LayoutResult 等）
│       ├── topoConfig.ts           ← TOPO_LAYOUT_CONFIG 常量配置对象
│       ├── TopoNode.tsx            ← 单个节点的 SVG 渲染组件（foreignObject 内含 HTML）
│       ├── TopoEdge.tsx            ← 单条连线的 SVG 渲染组件（motion.path）
│       └── TopoCanvas.tsx          ← SVG 画布容器（缩放、平移、viewBox 管理）
└── ...（其他文件不变）
```

### 4.2 各文件职责

| 文件 | 职责 | 大约行数 |
|------|------|----------|
| `topoConfig.ts` | 常量配置对象，节点尺寸/间距/颜色 | ~60 |
| `topoTypes.ts` | `LayoutTreeNode`, `NodeLayout`, `EdgePath`, `LayoutResult` 类型 | ~50 |
| `topoLayoutEngine.ts` | `computeTopoLayout()` 主入口 + 4个步骤函数 | ~180 |
| `TopoNode.tsx` | 单节点渲染：圆角矩形 + 图标 + label + 状态指示 + LiveInterventionInput | ~120 |
| `TopoEdge.tsx` | 单连线渲染：`<motion.path>` + 动画 | ~40 |
| `TopoCanvas.tsx` | SVG 容器，管理 viewBox、鼠标滚轮缩放、拖拽平移 | ~100 |
| `DynamicTopoGraph.tsx` | 主组件（重写），整合 Canvas + Node + Edge + 布局 | ~100 |

### 4.3 主组件集成伪代码

```tsx
// DynamicTopoGraph.tsx（重写后）
export default function DynamicTopoGraph() {
  const { agenticState, interruptAnalysis } = useStore();
  const [isInterrupting, setIsInterrupting] = useState(false);

  const nodes = agenticState.topologyNodes || [];
  const edges = agenticState.topologyEdges || [];

  // 计算布局（SSE 事件触发节点变化时自动重算）
  const layout = useMemo(
    () => computeTopoLayout(nodes, edges),
    [nodes, edges]
  );

  const handleInterrupt = async (msg: string) => {
    setIsInterrupting(true);
    const res = await interruptAnalysis(msg);
    setIsInterrupting(false);
    return res;
  };

  if (nodes.length === 0) {
    return <EmptyState />;  // 等待分析启动提示
  }

  return (
    <div className="w-full h-full">
      {/* 标题栏（保持不变） */}
      <div className="sticky top-0 ...">
        <h2>动态评估拓扑流</h2>
        <p>实时观测 Agent 协作与工具调用图谱...</p>
      </div>

      {/* SVG 拓扑画布 */}
      <TopoCanvas
        width={layout.canvasWidth}
        height={layout.canvasHeight}
      >
        {/* 先渲染连线（在底层） */}
        {layout.edges.map(edge => (
          <TopoEdge key={edge.edgeId} edge={edge} />
        ))}

        {/* 再渲染节点（在上层） */}
        {layout.nodes.map(nodeLayout => {
          const topoNode = nodes.find(n => n.id === nodeLayout.nodeId)!;
          return (
            <TopoNode
              key={nodeLayout.nodeId}
              node={topoNode}
              layout={nodeLayout}
              onInterrupt={handleInterrupt}
              isInterrupting={isInterrupting}
            />
          );
        })}
      </TopoCanvas>
    </div>
  );
}
```

### 4.4 TopoNode 组件关键设计

SVG 中使用 `<foreignObject>` 来渲染 HTML 内容（保留 Tailwind 样式能力）：

```tsx
function TopoNode({ node, layout, onInterrupt, isInterrupting }: TopoNodeProps) {
  const { x, y, width, height } = layout;
  const isActive = node.status === 'active';

  return (
    <motion.g
      initial={{ opacity: 0, x: x - 20 }}
      animate={{ opacity: 1, x }}
    >
      {/* 节点背景矩形 */}
      <rect
        x={x} y={y}
        width={width} height={height}
        rx={TOPO_LAYOUT_CONFIG.borderRadius}
        fill={statusColors[node.status].fill}
        stroke={statusColors[node.status].stroke}
        strokeWidth={isActive ? 2 : 1}
      />

      {/* 使用 foreignObject 嵌入 HTML 内容 */}
      <foreignObject x={x} y={y} width={width} height={height}>
        <div className="flex items-center gap-2 px-3 h-full">
          <Icon className="w-4 h-4 flex-shrink-0" />
          <span className="text-xs font-semibold truncate">{node.label}</span>
          {isActive && <PulsingDot />}
        </div>
      </foreignObject>

      {/* active 节点展示 LiveInterventionInput（在节点下方） */}
      {isActive && (
        <foreignObject
          x={x} y={y + height + 4}
          width={Math.max(width, 240)} height={40}
        >
          <LiveInterventionInput
            onSubmit={onInterrupt}
            isSubmitting={isInterrupting}
          />
        </foreignObject>
      )}
    </motion.g>
  );
}
```

### 4.5 TopoCanvas 组件关键设计

```tsx
function TopoCanvas({ width, height, children }: TopoCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  return (
    <div
      ref={containerRef}
      className="w-full h-full overflow-auto custom-scrollbar"
    >
      <svg
        width={Math.max(width, containerRef.current?.clientWidth ?? 600)}
        height={Math.max(height, containerRef.current?.clientHeight ?? 400)}
        className="select-none"
      >
        {children}
      </svg>
    </div>
  );
}
```

> **注意**: 初版不做缩放/平移功能，仅通过容器的 `overflow-auto` 实现滚动。如果后续需要，可添加 `transform` 和鼠标事件处理。

---

## 5. Caveats — 潜在问题与解决方案

### 5.1 foreignObject 兼容性

| 问题 | 影响 | 解决方案 |
|------|------|----------|
| `foreignObject` 在某些 SVG 渲染器中表现不一致 | Tailwind 类可能不生效 | 此项目为现代浏览器 Web 应用，Chrome/Edge/Firefox/Safari 均良好支持。不存在兼容性问题 |
| `foreignObject` 内的元素不参与 SVG 的 viewBox 缩放 | 如果后续加缩放，文字会模糊 | 初版不做缩放。后续如需缩放，用 CSS transform 代替 viewBox 缩放 |

### 5.2 LiveInterventionInput 在 foreignObject 中的表现

| 问题 | 解决方案 |
|------|----------|
| Input focus 在 foreignObject 中可能需要点击两次 | 为 foreignObject 添加 `pointer-events: auto` 样式 |
| 展开的表单高度超出 foreignObject | 动态计算 foreignObject height，或使用 Portal 将输入框挂载到 SVG 外层 |
| 动画（AnimatePresence）在 foreignObject 内可能有闪烁 | 考虑简化 LiveInterventionInput 在拓扑图内的动画 |

**推荐方案**: 在拓扑图中仅显示打断按钮，点击后弹出浮层（Popover）覆盖在 SVG 上方，而非在 foreignObject 内展开。

### 5.3 节点内容展开（content 字段）

当前垂直布局中 `node.content` 直接内联展示。水平布局中节点尺寸固定，无法内联展示长文本。

**推荐方案**: 
- 节点仅显示 label
- 点击/悬浮节点时，在 SVG 外层展示侧边抽屉或 Tooltip 面板
- 使用 Zustand store 管理 `selectedNodeId` 状态

### 5.4 动态节点增量布局的视觉跳动

SSE 每收到事件就追加节点，整棵树的布局会重新计算。如果新节点导致兄弟节点位移，会出现视觉跳动。

**解决方案**:
- 使用 `framer-motion` 的 `<motion.g>` 包裹每个节点，通过 `layout` 或 `animate={{ x, y }}` 让位移有过渡动画
- 连线使用 `motion.path` 的 `d` 属性动画（framer-motion v10 支持）
- 新加入的节点使用 `initial={{ opacity: 0, x: parentX }}` 从父节点位置淡入滑出

### 5.5 容器尺寸约束

| 场景 | 容器 | 问题 | 解决 |
|------|------|------|------|
| App.tsx 左侧栏 | `w-[40%]` ≈ 500-600px | 树太宽时水平溢出 | 容器 `overflow-x: auto`，SVG 宽度取 `max(layoutWidth, containerWidth)` |
| Dashboard 折叠 | `max-h-[600px]` | 树太高时垂直溢出 | 容器已有 `overflow-y: auto` |

### 5.6 空状态与单节点

- 空数组：返回等待提示（保持现有设计）
- 仅根节点：居中显示单个节点，无连线

### 5.7 节点类型样式映射

现有代码中的 `getAgentTheme()` 函数和 `AGENT_THEMES` 映射需要在 SVG 节点渲染中继续使用。建议：
- `TopoNode` 内部复用 `getAgentTheme(node.agentId)` 获取颜色
- type 为 `system`/`phase`/`tool` 时使用 `TOPO_LAYOUT_CONFIG.statusColors` 配色
- type 为 `agent` 时优先使用 `getAgentTheme` 返回的主题色

---

## 6. Conclusion — 最终评估

本设计方案的核心是一个 **O(n) 时间复杂度的三步布局算法**（构建树 → 计算子树高度 → 分配坐标），足以应对实时 SSE 流式场景下的频繁重算需求。

**关键设计决策**：
1. **纯函数布局引擎**（`topoLayoutEngine.ts`）与 React 渲染完全分离，便于测试和复用
2. **foreignObject 渲染 HTML**，保留 Tailwind + framer-motion 能力，避免纯 SVG text 的排版限制
3. **常量配置集中管理**，节点尺寸/间距/颜色全部可调
4. **水平贝塞尔曲线**参数化（controlRatio），一个参数控制曲线弧度

**实施建议优先级**：
1. 先实现 `topoConfig.ts` + `topoTypes.ts` + `topoLayoutEngine.ts`（纯逻辑，可单元测试）
2. 再实现 `TopoEdge.tsx` + `TopoNode.tsx`（无状态渲染组件）
3. 最后组装 `TopoCanvas.tsx` + 重写 `DynamicTopoGraph.tsx`
4. 打断输入组件的 foreignObject 集成放在最后微调

---

## 7. Verification Method

### 验证布局算法正确性

```typescript
// 可编写的单元测试用例
describe('computeTopoLayout', () => {
  it('单节点：根在左上角', () => {
    const nodes = [{ id: 'root', type: 'system', status: 'active', label: 'Root', timestamp: 0 }];
    const result = computeTopoLayout(nodes, []);
    expect(result.nodes).toHaveLength(1);
    expect(result.nodes[0].x).toBe(TOPO_LAYOUT_CONFIG.padding.left);
  });

  it('两层树：子节点在父节点右侧', () => {
    const nodes = [
      { id: 'root', type: 'system', status: 'active', label: 'R', timestamp: 0 },
      { id: 'child', type: 'phase', status: 'active', label: 'C', parentId: 'root', timestamp: 1 },
    ];
    const edges = [{ id: 'e1', source: 'root', target: 'child', status: 'active' }];
    const result = computeTopoLayout(nodes, edges);
    expect(result.nodes[1].x).toBeGreaterThan(result.nodes[0].x);
    expect(result.edges).toHaveLength(1);
    expect(result.edges[0].path).toContain('M ');
    expect(result.edges[0].path).toContain(' C ');
  });

  it('三个兄弟节点不重叠', () => {
    const nodes = [
      { id: 'root', type: 'system', status: 'active', label: 'R', timestamp: 0 },
      { id: 'c1', type: 'phase', status: 'active', label: 'C1', parentId: 'root', timestamp: 1 },
      { id: 'c2', type: 'phase', status: 'active', label: 'C2', parentId: 'root', timestamp: 2 },
      { id: 'c3', type: 'phase', status: 'active', label: 'C3', parentId: 'root', timestamp: 3 },
    ];
    const result = computeTopoLayout(nodes, []);
    const [, n1, n2, n3] = result.nodes;
    // 验证垂直方向不重叠
    expect(n2.y).toBeGreaterThanOrEqual(n1.y + n1.height);
    expect(n3.y).toBeGreaterThanOrEqual(n2.y + n2.height);
  });

  it('父节点在子节点组的垂直中心', () => {
    const nodes = [
      { id: 'root', type: 'system', status: 'active', label: 'R', timestamp: 0 },
      { id: 'c1', type: 'phase', status: 'active', label: 'C1', parentId: 'root', timestamp: 1 },
      { id: 'c2', type: 'phase', status: 'active', label: 'C2', parentId: 'root', timestamp: 2 },
    ];
    const result = computeTopoLayout(nodes, []);
    const [parent, child1, child2] = result.nodes;
    const childrenCenter = (child1.y + child1.height / 2 + child2.y + child2.height / 2) / 2;
    const parentCenter = parent.y + parent.height / 2;
    expect(Math.abs(parentCenter - childrenCenter)).toBeLessThan(1);
  });
});
```

### 验证渲染正确性

1. 在浏览器中启动应用，触发分析流
2. 打开 DevTools 检查 SVG DOM 结构
3. 验证节点不重叠
4. 验证连线端点精确连接到节点边缘
5. 验证 LiveInterventionInput 在 active 节点上可交互

### 验证命令

```bash
# 构建验证
cd frontend ; npm run build

# 如果编写了单元测试
cd frontend ; npx vitest run src/components/topo/topoLayoutEngine.test.ts
```
