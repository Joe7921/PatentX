# SVG 节点渲染方案设计报告

> **核心结论**：使用 SVG `<foreignObject>` 在水平拓扑图中嵌入 HTML/Tailwind 渲染的节点卡片是最佳方案，可完全复用现有 AGENT_THEMES 配色体系。LiveInterventionInput 推荐使用 CSS absolute 浮层方式集成，避免 foreignObject 内嵌入复杂表单控件的跨浏览器问题。

---

## 一、现有代码结构分析

### 1.1 现有 renderNode 逻辑（DynamicTopoGraph.tsx:22-112）

现有组件采用**递归 HTML div** 方式渲染垂直目录树：
- 通过 `node.type` 判断节点类型，设置 `Icon/bgColor/borderColor/iconColor/titleColor`
- `phase` → `bg-indigo-50/50` + `border-indigo-200/50` + `Network` 图标
- `agent` → 从 `getAgentTheme(node.agentId)` 获取动态主题色 + `User` 图标
- `tool` → `bg-emerald-50/50` + `border-emerald-200/50` + `Wrench` 图标
- `system` → 默认 `bg-slate-100` + `border-slate-200` + `Server` 图标
- active 节点有 `shadow-gemini-md ring-2 ring-blue-500/20` 高亮和蓝色脉冲点
- completed 节点显示绿色 `CheckCircle2` 图标
- 使用 `framer-motion` 的 `initial={{ opacity: 0, y: 10 }}` 进入动画
- active 节点内嵌 `<LiveInterventionInput>` 组件

### 1.2 容器上下文

**THINKING/PAUSED 模式**（App.tsx:68）：
```
w-[40%] bg-white/90 backdrop-blur-md border border-gemini-outline/50 rounded-card p-5
overflow-y-auto overflow-x-hidden custom-scrollbar
```
→ 左侧面板占 40% 宽度，约 **~560px**（在 1400px 屏幕上），有 `p-5`（20px 内边距），实际可用宽度约 **520px**。
→ 改为水平拓扑图后，应改为 `overflow-x-auto overflow-y-hidden`。

**DASHBOARD 模式**（DiagnosticDashboard.tsx:82-84）：
```
border border-slate-200 rounded-2xl p-4 bg-slate-50/50 max-h-[600px] overflow-y-auto
```
→ 嵌在 `max-w-5xl`（1024px）容器的 3/3 列内，实际可用宽度约 **~960px**。

### 1.3 数据结构

```typescript
interface TopologyNode {
  id: string;
  type: 'system' | 'phase' | 'agent' | 'tool';
  status: 'pending' | 'active' | 'completed';
  label: string;
  agentId?: string;    // 仅 agent 类型
  toolName?: string;   // 仅 tool 类型
  content?: string;    // 详细日志（可选）
  parentId?: string;   // 父节点 ID
  timestamp: number;
}

interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  status: 'active' | 'completed';
}
```

### 1.4 AGENT_THEMES 配色映射

| agentId | color (hex) | bgClass | borderClass | textClass |
|---|---|---|---|---|
| `first_examiner` | `#3B82F6` | `bg-blue-500/10` | `border-blue-500/30` | `text-blue-600` |
| `second_examiner` | `#F59E0B` | `bg-amber-500/10` | `border-amber-500/30` | `text-amber-600` |
| `chairman` | `#8B5CF6` | `bg-purple-500/10` | `border-purple-500/30` | `text-purple-600` |
| `applicant_representative` | `#06B6D4` | `bg-cyan-500/10` | `border-cyan-500/30` | `text-cyan-600` |
| `legal_examiner` | `#F43F5E` | `bg-rose-500/10` | `border-rose-500/30` | `text-rose-600` |
| **默认回退** | `#64748B` | `bg-slate-500/10` | `border-slate-500/30` | `text-slate-600` |

关键：`AgentTheme.color` 提供的是 **hex 颜色值**，可直接用于 SVG 的 `stroke`/`fill` 属性以及 CSS `style`，而 Tailwind 类名（`bgClass`/`borderClass`/`textClass`）用于 foreignObject 内的 HTML 元素。

---

## 二、四种节点类型的视觉设计

### 2.1 节点尺寸规格

| 类型 | 宽度(px) | 高度(px) | 说明 |
|------|----------|----------|------|
| `system` | 180 | 60 | 起始锚点，紧凑 |
| `phase` | 240 | 80 | 最大尺寸，含左侧竖条 |
| `agent` | 200 | 70 | 中等尺寸，粗边框 |
| `tool` | 160 | 56 | 最小尺寸，虚线边框 |

定义常量映射：

```typescript
// 节点尺寸常量
const NODE_SIZES: Record<TopologyNode['type'], { w: number; h: number }> = {
  system: { w: 180, h: 60 },
  phase:  { w: 240, h: 80 },
  agent:  { w: 200, h: 70 },
  tool:   { w: 160, h: 56 },
};
```

### 2.2 system 节点 — 深色实心背景

```tsx
{/* system 节点 foreignObject */}
<foreignObject x={node.x} y={node.y} width={180} height={60}>
  <div xmlns="http://www.w3.org/1999/xhtml"
    className="w-full h-full flex items-center gap-2.5 px-4 rounded-xl
               bg-slate-800 text-white shadow-lg"
  >
    <div className="p-1.5 rounded-lg bg-white/15">
      <Server className="w-4 h-4 text-white/90" />
    </div>
    <span className="text-xs font-bold tracking-wide truncate">
      {node.label}
    </span>
  </div>
</foreignObject>
```

**设计要点**：
- 深色 `bg-slate-800` 实心背景，与其他浅色节点形成鲜明对比
- 白色文字 + 半透明图标容器 `bg-white/15`
- `rounded-xl` 圆角，`shadow-lg` 投影增强锚点感
- 无状态变化（system 始终 active）

### 2.3 phase 节点 — 最大尺寸，左侧竖条色带

```tsx
{/* phase 节点 foreignObject */}
<foreignObject x={node.x} y={node.y} width={240} height={80}>
  <div xmlns="http://www.w3.org/1999/xhtml"
    className="w-full h-full flex rounded-2xl border border-indigo-200/50
               bg-indigo-50/50 shadow-sm overflow-hidden"
  >
    {/* 左侧竖条色带 */}
    <div className="w-1.5 flex-shrink-0 bg-indigo-500 rounded-l-2xl" />
    <div className="flex-1 flex items-center gap-3 px-4">
      <div className="p-2 rounded-xl bg-white shadow-sm border border-indigo-200/50">
        <Network className="w-4 h-4 text-indigo-500" />
      </div>
      <div className="min-w-0">
        <span className="font-semibold text-sm text-indigo-800 truncate block">
          {node.label}
        </span>
        {node.status === 'completed' && (
          <span className="text-[10px] text-indigo-400 font-medium">已完成</span>
        )}
      </div>
      {/* 状态指示 */}
      {node.status === 'active' && (
        <span className="ml-auto flex h-2.5 w-2.5 rounded-full bg-indigo-500 relative">
          <span className="absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75 animate-ping" />
        </span>
      )}
      {node.status === 'completed' && (
        <CheckCircle2 className="ml-auto w-4 h-4 text-emerald-500 opacity-60" />
      )}
    </div>
  </div>
</foreignObject>
```

**设计要点**：
- 左侧 `w-1.5` 竖条色带使用 `bg-indigo-500`，作为阶段标识
- `rounded-2xl` 大圆角，视觉上最醒目
- active 状态有脉冲点，completed 有 ✅ 图标

### 2.4 agent 节点 — AGENT_THEMES 主题色粗边框

```tsx
{/* agent 节点 foreignObject */}
{(() => {
  const theme = getAgentTheme(node.agentId || '');
  return (
    <foreignObject x={node.x} y={node.y} width={200} height={70}>
      <div xmlns="http://www.w3.org/1999/xhtml"
        className={`w-full h-full flex items-center gap-3 px-4 rounded-xl
                    border-2 ${theme.bgClass} shadow-sm`}
        style={{ borderColor: theme.color }}
      >
        <div className={`p-1.5 rounded-lg bg-white shadow-sm border ${theme.borderClass}`}>
          <User className={`w-4 h-4 ${theme.textClass}`} />
        </div>
        <div className="min-w-0 flex-1">
          <span className={`font-semibold text-sm truncate block ${theme.textClass}`}>
            {node.label}
          </span>
        </div>
        {node.status === 'active' && (
          <span className="flex h-2 w-2 rounded-full relative" style={{ backgroundColor: theme.color }}>
            <span className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
                  style={{ backgroundColor: theme.color }} />
          </span>
        )}
        {node.status === 'completed' && (
          <CheckCircle2 className="w-4 h-4 text-emerald-500 opacity-50" />
        )}
      </div>
    </foreignObject>
  );
})()}
```

**设计要点**：
- 使用 `border-2`（2px 粗边框）+ `style={{ borderColor: theme.color }}` 直接引用 hex 色值
- 背景使用 Tailwind 的 `theme.bgClass`（如 `bg-blue-500/10`），保持与现有设计一致
- active 状态的呼吸发光动画使用 SVG `<filter>` 实现（见第五节动画设计）
- 脉冲点颜色也使用 `theme.color` 保持一致

### 2.5 tool 节点 — 虚线细边框

```tsx
{/* tool 节点 foreignObject */}
<foreignObject x={node.x} y={node.y} width={160} height={56}>
  <div xmlns="http://www.w3.org/1999/xhtml"
    className="w-full h-full flex items-center gap-2.5 px-3 rounded-lg
               bg-emerald-50/30 shadow-none"
    style={{ border: '1.5px dashed rgba(16, 185, 129, 0.35)' }}
  >
    <div className="p-1 rounded-md bg-white/80 border border-emerald-200/40">
      <Wrench className="w-3.5 h-3.5 text-emerald-500" />
    </div>
    <span className="text-xs font-medium text-emerald-700 truncate">
      {node.label}
    </span>
    {node.status === 'completed' && (
      <CheckCircle2 className="ml-auto w-3.5 h-3.5 text-emerald-500 opacity-40" />
    )}
  </div>
</foreignObject>
```

**设计要点**：
- 使用 `style={{ border: '1.5px dashed ...' }}` 实现虚线效果（Tailwind 没有原生 dashed 虚线变体）
- 中性灰绿色调 `bg-emerald-50/30`，低饱和度
- 无 shadow，视觉最轻量
- 较小尺寸（160×56），与 phase 形成明显层级对比

---

## 三、SVG foreignObject 嵌入方案

### 3.1 基本结构

```tsx
export default function DynamicTopoGraph() {
  const { agenticState, interruptAnalysis } = useStore();
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const nodes = agenticState.topologyNodes || [];
  const edges = agenticState.topologyEdges || [];

  // 布局计算（返回每个节点的 x, y 坐标）
  const layout = useMemo(() => computeLayout(nodes, edges), [nodes, edges]);

  // 计算 SVG 视口尺寸
  const svgWidth = useMemo(() => {
    if (layout.length === 0) return 600;
    return Math.max(...layout.map(n => n.x + NODE_SIZES[n.type].w)) + 100;
  }, [layout]);

  const svgHeight = useMemo(() => {
    if (layout.length === 0) return 400;
    return Math.max(...layout.map(n => n.y + NODE_SIZES[n.type].h)) + 100;
  }, [layout]);

  return (
    <div ref={containerRef}
         className="w-full h-full overflow-auto custom-scrollbar relative">
      {/* 标题栏 - 固定在容器顶部 */}
      <div className="sticky top-0 left-0 bg-white/90 backdrop-blur-xl z-30 pb-4 border-b border-slate-200 mb-4">
        <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
          <Network className="w-4 h-4 text-blue-500" />
          动态评估拓扑流
        </h2>
        <p className="text-xs text-slate-500 mt-1.5 font-medium">
          实时观测 Agent 协作与工具调用图谱
        </p>
      </div>

      {/* SVG 画布 */}
      <svg ref={svgRef}
           width={svgWidth}
           height={svgHeight}
           className="block"
           xmlns="http://www.w3.org/2000/svg">
        {/* SVG filter 定义（呼吸发光） */}
        <defs>
          {/* 见第五节动画设计 */}
        </defs>

        {/* 连线层 */}
        <g className="edges">
          {edges.map(edge => (
            <EdgeLine key={edge.id} edge={edge} layout={layout} />
          ))}
        </g>

        {/* 节点层 */}
        <g className="nodes">
          {layout.map(nodeLayout => (
            <NodeForeignObject key={nodeLayout.id} node={nodeLayout} />
          ))}
        </g>
      </svg>

      {/* LiveInterventionInput 浮层 - 见第四节 */}
      {activeNode && <InterventionOverlay ... />}
    </div>
  );
}
```

### 3.2 foreignObject 的 width/height 与布局算法协调

**关键原则**：foreignObject 的 `width`/`height` 必须**精确匹配**内部 HTML 内容的尺寸，否则内容会被裁切或溢出。

**方案：固定尺寸映射**

```typescript
// 布局函数接收节点列表，返回带坐标的节点列表
interface LayoutNode extends TopologyNode {
  x: number;  // foreignObject 左上角 x
  y: number;  // foreignObject 左上角 y
}

function computeLayout(nodes: TopologyNode[], edges: TopologyEdge[]): LayoutNode[] {
  // 按层级分组（BFS 从 root 开始）
  const levels = buildLevelMap(nodes, edges);
  const H_GAP = 60;  // 节点间水平间距
  const V_GAP = 30;  // 同层节点垂直间距

  const result: LayoutNode[] = [];
  let xOffset = 40; // 起始 x 偏移

  for (const level of levels) {
    const maxWidth = Math.max(...level.map(n => NODE_SIZES[n.type].w));
    const totalHeight = level.reduce((sum, n) => sum + NODE_SIZES[n.type].h, 0)
                       + (level.length - 1) * V_GAP;
    let yOffset = Math.max(20, (svgHeight - totalHeight) / 2); // 垂直居中

    for (const node of level) {
      const size = NODE_SIZES[node.type];
      result.push({
        ...node,
        x: xOffset + (maxWidth - size.w) / 2, // 同层水平居中对齐
        y: yOffset,
      });
      yOffset += size.h + V_GAP;
    }
    xOffset += maxWidth + H_GAP;
  }

  return result;
}
```

**foreignObject 渲染**：
```tsx
function NodeForeignObject({ node }: { node: LayoutNode }) {
  const size = NODE_SIZES[node.type];
  return (
    <foreignObject
      x={node.x}
      y={node.y}
      width={size.w}
      height={size.h}
      // 关键：允许内容溢出（用于 active 状态的光晕效果）
      overflow="visible"
    >
      {/* 根据 node.type 渲染对应的 HTML 卡片 */}
      {renderNodeCard(node)}
    </foreignObject>
  );
}
```

### 3.3 Tailwind 样式在 foreignObject 内的工作状况

**结论：完全正常工作**。原因：

1. `foreignObject` 内部是一个完整的 HTML 命名空间（`xmlns="http://www.w3.org/1999/xhtml"`），与普通 HTML DOM 无异
2. Tailwind 的 CSS 类通过全局 `<style>` 标签注入，对 SVG 内的 HTML 元素同样生效
3. `backdrop-blur`、`shadow`、`border-radius` 等现代 CSS 属性在 foreignObject 内均受支持
4. **注意事项**：
   - `overflow` 属性：foreignObject 默认 `overflow: hidden`。若节点有 box-shadow 或呼吸光晕，需设 `overflow="visible"`
   - 事件冒泡：foreignObject 内的 HTML 事件正常冒泡，`onClick`/`onChange`/`onSubmit` 均可正常使用
   - 字体继承：foreignObject 继承 SVG 的字体设置，需在 div 上显式重设 `font-family` 或依赖 Tailwind 的 `font-inter` 类

### 3.4 连线渲染

```tsx
function EdgeLine({ edge, layout }: { edge: TopologyEdge; layout: LayoutNode[] }) {
  const source = layout.find(n => n.id === edge.source);
  const target = layout.find(n => n.id === edge.target);
  if (!source || !target) return null;

  const srcSize = NODE_SIZES[source.type];
  const tgtSize = NODE_SIZES[target.type];

  // 起点：source 节点右侧中点
  const x1 = source.x + srcSize.w;
  const y1 = source.y + srcSize.h / 2;
  // 终点：target 节点左侧中点
  const x2 = target.x;
  const y2 = target.y + tgtSize.h / 2;

  // 使用三次贝塞尔曲线
  const midX = (x1 + x2) / 2;
  const d = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;

  return (
    <path
      d={d}
      fill="none"
      stroke={edge.status === 'completed' ? '#94a3b8' : '#3b82f6'}
      strokeWidth={edge.status === 'active' ? 2 : 1.5}
      strokeDasharray={edge.status === 'active' ? '6 3' : 'none'}
      className="transition-all duration-500"
      opacity={edge.status === 'completed' ? 0.4 : 0.8}
    />
  );
}
```

---

## 四、LiveInterventionInput 集成方案

### 4.1 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| **A. foreignObject 内嵌入** | 位置跟随节点自然移动；无需额外定位计算 | foreignObject 内的表单控件在某些浏览器有 focus/z-index 问题；需要增大 foreignObject 高度导致布局变形 |
| **B. CSS absolute 定位浮层** ⭐ | 表单控件在正常 HTML 流中渲染，输入体验最佳；不影响 SVG 布局；z-index 可控 | 需要在 SVG 坐标和容器 DOM 坐标间做转换 |

### 4.2 推荐方案：B — CSS absolute 定位浮层

**理由**：
1. `LiveInterventionInput` 包含 `<input>` 表单、`<AnimatePresence>` 动画、framer-motion `<motion.form>` — 这些在 foreignObject 内存在已知的跨浏览器问题（Firefox 的 foreignObject input focus bug）
2. 浮层方案不改变 foreignObject 的固定尺寸，布局算法无需动态调整
3. 组件已有 `max-w-sm`（384px）宽度限制，与节点宽度无关

**实现**：

```tsx
function InterventionOverlay({
  activeNode,
  containerRef,
  svgRef,
}: {
  activeNode: LayoutNode;
  containerRef: React.RefObject<HTMLDivElement>;
  svgRef: React.RefObject<SVGSVGElement>;
}) {
  const [isInterrupting, setIsInterrupting] = useState(false);
  const { interruptAnalysis } = useStore();

  const handleInterrupt = async (msg: string) => {
    setIsInterrupting(true);
    const res = await interruptAnalysis(msg);
    setIsInterrupting(false);
    return res;
  };

  const size = NODE_SIZES[activeNode.type];

  // 浮层定位：节点正下方，与节点左对齐
  // 因为 SVG 在 scrollable 容器中，位置直接使用 SVG 内坐标即可
  const style: React.CSSProperties = {
    position: 'absolute',
    left: activeNode.x,
    top: activeNode.y + size.h + 8, // 节点底部 + 8px 间距
    zIndex: 50,
  };

  return (
    <div style={style}>
      <LiveInterventionInput
        onSubmit={handleInterrupt}
        isSubmitting={isInterrupting}
      />
    </div>
  );
}
```

**容器调整**：外层 `<div>` 需要 `position: relative` 使 absolute 定位生效：

```tsx
<div ref={containerRef}
     className="w-full h-full overflow-auto custom-scrollbar relative">
  <svg ...>...</svg>
  {activeNode && <InterventionOverlay ... />}
</div>
```

**注意**：因为 `<svg>` 和 `InterventionOverlay` 同在一个 relative 容器中，且 SVG 不设 `viewBox`（1:1 像素映射），SVG 坐标直接等于 DOM 坐标，无需额外转换。

---

## 五、framer-motion 动画设计

### 5.1 节点出现动画（opacity + scale）

**重要限制**：framer-motion v10 **不支持**直接在 SVG `<foreignObject>` 上使用 `<motion.foreignObject>`，因为 `foreignObject` 不是 framer-motion 内置的 SVG motion 元素。

**解决方案**：用 `<motion.g>` 包裹 `<foreignObject>`，或在 foreignObject 内部的 `<div>` 上使用 `<motion.div>`。

**推荐方案：foreignObject 内部 motion.div**

```tsx
<foreignObject x={node.x} y={node.y} width={size.w} height={size.h} overflow="visible">
  <motion.div
    xmlns="http://www.w3.org/1999/xhtml"
    initial={{ opacity: 0, scale: 0.85 }}
    animate={{ opacity: 1, scale: 1 }}
    transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
    className="w-full h-full origin-center ..."
  >
    {/* 节点内容 */}
  </motion.div>
</foreignObject>
```

**兼容性说明**：
- `motion.div` 在 foreignObject 内部使用 CSS transforms（`transform: scale()`），完全兼容
- `origin-center` 确保缩放从中心开始
- ease 曲线 `[0.32, 0.72, 0, 1]` 与项目中 App.tsx:59 保持一致

### 5.2 agent active 状态的呼吸发光动画

**方案 A：CSS box-shadow 动画（推荐）**

在 `index.css` 中添加 keyframe：

```css
@keyframes agent-glow-breath {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--glow-color, rgba(59, 130, 246, 0.3));
  }
  50% {
    box-shadow: 0 0 16px 4px var(--glow-color, rgba(59, 130, 246, 0.3));
  }
}

.agent-glow-active {
  animation: agent-glow-breath 2.5s infinite ease-in-out;
}
```

使用时通过 CSS 变量注入主题色：

```tsx
<motion.div
  className={`... ${isActive ? 'agent-glow-active' : ''}`}
  style={isActive ? { '--glow-color': `${theme.color}40` } as React.CSSProperties : undefined}
>
```

**方案 B：SVG filter 发光（备选）**

```tsx
<defs>
  {/* 为每个活跃 agent 生成动态 filter */}
  {activeAgentNodes.map(node => {
    const theme = getAgentTheme(node.agentId || '');
    return (
      <filter key={`glow-${node.id}`} id={`glow-${node.id}`} x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="4" result="blur" />
        <feFlood floodColor={theme.color} floodOpacity="0.3" />
        <feComposite in2="blur" operator="in" />
        <feMerge>
          <feMergeNode />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    );
  })}
</defs>
```

**推荐方案 A**，因为：
1. CSS box-shadow 动画性能好（GPU 加速）
2. 项目已有类似模式（`index.css:12-23` 的 `gemini-glow-breath` 动画）
3. SVG filter 动画需要 JS 定时器或 `<animate>` 标签控制 `stdDeviation`，复杂度更高

### 5.3 连线动画

新连线出现时使用 `stroke-dashoffset` 动画模拟"画线"效果：

```tsx
<motion.path
  d={d}
  fill="none"
  stroke={color}
  strokeWidth={width}
  initial={{ pathLength: 0, opacity: 0 }}
  animate={{ pathLength: 1, opacity: 1 }}
  transition={{ duration: 0.5, ease: 'easeOut' }}
/>
```

framer-motion v10 的 `pathLength` 动画在 SVG `<path>` 上有原生支持。

---

## 六、自动滚动实现方案

### 6.1 方案对比

| 方案 | 优点 | 缺点 |
|------|------|------|
| `scrollIntoView` | API 简单 | 滚动整个页面而非容器；无法精确控制对齐位置 |
| `container.scrollTo` ⭐ | 精确控制滚动容器；可控制对齐方式 | 需要手动计算目标坐标 |

### 6.2 推荐方案：container.scrollTo

```typescript
// 当有新的 active 节点时，自动滚动到该节点
useEffect(() => {
  const activeNode = layout.find(n => n.status === 'active');
  if (!activeNode || !containerRef.current) return;

  const container = containerRef.current;
  const size = NODE_SIZES[activeNode.type];

  // 将 active 节点滚动到容器的水平中心位置
  const targetScrollLeft = activeNode.x + size.w / 2 - container.clientWidth / 2;
  // 垂直方向也居中
  const targetScrollTop = activeNode.y + size.h / 2 - container.clientHeight / 2;

  container.scrollTo({
    left: Math.max(0, targetScrollLeft),
    top: Math.max(0, targetScrollTop),
    behavior: 'smooth',
  });
}, [layout]); // layout 变化时触发
```

**优化：避免用户手动滚动后被自动覆盖**

```typescript
const userScrolledRef = useRef(false);
const scrollTimeoutRef = useRef<NodeJS.Timeout>();

// 监听用户主动滚动
useEffect(() => {
  const container = containerRef.current;
  if (!container) return;

  const handleScroll = () => {
    userScrolledRef.current = true;
    if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    // 3 秒后恢复自动跟踪
    scrollTimeoutRef.current = setTimeout(() => {
      userScrolledRef.current = false;
    }, 3000);
  };

  container.addEventListener('scroll', handleScroll, { passive: true });
  return () => container.removeEventListener('scroll', handleScroll);
}, []);

// 自动滚动（仅在用户未主动滚动时触发）
useEffect(() => {
  if (userScrolledRef.current) return;
  // ... scrollTo 逻辑
}, [layout]);
```

---

## 七、潜在问题与解决方案

### 7.1 foreignObject 跨浏览器兼容性

| 问题 | 影响范围 | 解决方案 |
|------|----------|----------|
| Firefox 中 foreignObject 内 input 的 focus 行为异常 | Firefox | LiveInterventionInput 使用 CSS absolute 浮层（已在第四节采用） |
| Safari 中 foreignObject 的 `overflow: visible` 不生效 | Safari | 在 foreignObject 外包一层 `<g>` 用 SVG `<filter>` 做光晕，不依赖 CSS overflow |
| foreignObject 内 `position: fixed` 无效 | 全浏览器 | 不在 foreignObject 内使用 fixed 定位，所有 fixed 元素放在 SVG 外层 |

### 7.2 性能考量

| 问题 | 解决方案 |
|------|----------|
| 大量节点（>100）导致 DOM 膨胀 | 实现视口裁剪：在 `computeLayout` 后，只渲染 `x` 坐标落在 `[scrollLeft - buffer, scrollLeft + containerWidth + buffer]` 范围内的节点 |
| `useMemo` 依赖 `nodes` 数组引用频繁变化 | 在 store 中使用 `immer` 或结构化更新，确保 `topologyNodes` 引用只在内容变化时更新 |
| framer-motion re-render 开销 | 给每个 `NodeForeignObject` 加 `React.memo`，依赖 `node.status` 和 `node.id` |

### 7.3 容器尺寸适配

**问题**：App.tsx 中容器 `w-[40%]` 在不同屏幕尺寸下可用宽度差异大（900px 屏幕 → ~320px，1400px → ~520px）。

**解决方案**：
- SVG 使用实际像素坐标（非 viewBox 缩放），宽度动态计算
- 容器使用 `overflow-x: auto`，允许水平滚动
- 考虑在窄屏时缩小节点尺寸（通过 CSS `transform: scale()` 或调整 `NODE_SIZES`）

### 7.4 DiagnosticDashboard 中的复用

DynamicTopoGraph 在两处被使用（App.tsx:69, DiagnosticDashboard.tsx:83），容器尺寸不同：
- App.tsx: 面板 40% 宽度，无高度限制
- DiagnosticDashboard.tsx: `max-h-[600px]` 限制

**解决方案**：组件无需接收 props（要求保持 `default export function DynamicTopoGraph()` 无参数），内部通过 `containerRef.current.clientWidth/clientHeight` 动态获取可用空间来自适应。

### 7.5 自定义 Tailwind 类名

项目中使用的 `border-gemini-outline`、`shadow-gemini-md`、`shadow-gemini-xs`、`rounded-card`、`custom-scrollbar` 等类名在 `tailwind.config.js` 和 `index.css` 中均未找到定义。

**分析**：这些可能是：
1. 通过某个未追踪的 Tailwind 插件/preset 定义
2. 或作为约定名称直接使用（JIT 模式下不会报错，只是不生成样式）

**建议**：在新组件中继续使用这些类名保持一致性，但若需要实际生效的自定义样式（如 `custom-scrollbar`），需在 `index.css` 中补充定义。

---

## 八、完整节点渲染函数设计

```tsx
// 节点渲染入口函数
function renderNodeCard(node: LayoutNode): React.ReactNode {
  const isActive = node.status === 'active';
  const isCompleted = node.status === 'completed';

  switch (node.type) {
    case 'system':
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
          className="w-full h-full flex items-center gap-2.5 px-4 rounded-xl
                     bg-slate-800 text-white shadow-lg font-inter"
        >
          <div className="p-1.5 rounded-lg bg-white/15">
            <Server className="w-4 h-4 text-white/90" />
          </div>
          <span className="text-xs font-bold tracking-wide truncate">{node.label}</span>
        </motion.div>
      );

    case 'phase':
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
          className="w-full h-full flex rounded-2xl border border-indigo-200/50
                     bg-indigo-50/50 shadow-sm overflow-hidden font-inter"
        >
          <div className="w-1.5 flex-shrink-0 bg-indigo-500 rounded-l-2xl" />
          <div className="flex-1 flex items-center gap-3 px-4">
            <div className="p-2 rounded-xl bg-white shadow-sm border border-indigo-200/50">
              <Network className="w-4 h-4 text-indigo-500" />
            </div>
            <div className="min-w-0 flex-1">
              <span className="font-semibold text-sm text-indigo-800 truncate block">{node.label}</span>
              {isCompleted && <span className="text-[10px] text-indigo-400 font-medium">已完成</span>}
            </div>
            {isActive && (
              <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-500 relative flex-shrink-0">
                <span className="absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75 animate-ping" />
              </span>
            )}
            {isCompleted && <CheckCircle2 className="w-4 h-4 text-emerald-500 opacity-60 flex-shrink-0" />}
          </div>
        </motion.div>
      );

    case 'agent': {
      const theme = getAgentTheme(node.agentId || '');
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
          className={`w-full h-full flex items-center gap-3 px-4 rounded-xl
                      border-2 ${theme.bgClass} shadow-sm font-inter
                      ${isActive ? 'agent-glow-active' : ''}`}
          style={{
            borderColor: theme.color,
            ...(isActive ? { '--glow-color': `${theme.color}40` } as React.CSSProperties : {}),
          }}
        >
          <div className={`p-1.5 rounded-lg bg-white shadow-sm border ${theme.borderClass} flex-shrink-0`}>
            <User className={`w-4 h-4 ${theme.textClass}`} />
          </div>
          <div className="min-w-0 flex-1">
            <span className={`font-semibold text-sm truncate block ${theme.textClass}`}>{node.label}</span>
          </div>
          {isActive && (
            <span className="flex h-2 w-2 rounded-full relative flex-shrink-0"
                  style={{ backgroundColor: theme.color }}>
              <span className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
                    style={{ backgroundColor: theme.color }} />
            </span>
          )}
          {isCompleted && <CheckCircle2 className="w-4 h-4 text-emerald-500 opacity-50 flex-shrink-0" />}
        </motion.div>
      );
    }

    case 'tool':
      return (
        <motion.div
          initial={{ opacity: 0, scale: 0.85 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.35, ease: [0.32, 0.72, 0, 1] }}
          className="w-full h-full flex items-center gap-2.5 px-3 rounded-lg
                     bg-emerald-50/30 font-inter"
          style={{ border: '1.5px dashed rgba(16, 185, 129, 0.35)' }}
        >
          <div className="p-1 rounded-md bg-white/80 border border-emerald-200/40 flex-shrink-0">
            <Wrench className="w-3.5 h-3.5 text-emerald-500" />
          </div>
          <span className="text-xs font-medium text-emerald-700 truncate">{node.label}</span>
          {isCompleted && <CheckCircle2 className="ml-auto w-3.5 h-3.5 text-emerald-500 opacity-40 flex-shrink-0" />}
        </motion.div>
      );

    default:
      return null;
  }
}
```

---

## 九、需要添加到 index.css 的样式

```css
/* 在现有 index.css 末尾追加 */

/* Agent 节点 active 状态呼吸发光 */
@keyframes agent-glow-breath {
  0%, 100% {
    box-shadow: 0 0 0 0 var(--glow-color, rgba(59, 130, 246, 0.3));
  }
  50% {
    box-shadow: 0 0 16px 4px var(--glow-color, rgba(59, 130, 246, 0.3));
  }
}

.agent-glow-active {
  animation: agent-glow-breath 2.5s infinite ease-in-out;
}

/* 自定义滚动条（若尚未生效则补充） */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
```

---

## 验证方法

1. **构建验证**：`cd frontend ; npm run build` 确认 TypeScript 无类型错误
2. **视觉验证**：在浏览器中启动分析流，观察：
   - system 节点是否为深色实心
   - phase 节点是否有左侧竖条
   - agent 节点边框颜色是否与 AGENT_THEMES 一致
   - tool 节点是否为虚线边框
   - active 节点是否有呼吸发光
   - 连线是否正确连接节点
3. **交互验证**：点击 active 节点下方的"随时打断补充..."按钮，验证 input 可正常 focus 和提交
4. **滚动验证**：新节点出现时是否自动滚动到可见区域；手动滚动后 3 秒内不触发自动滚动
5. **浏览器兼容性**：在 Chrome 和 Firefox 中分别验证 foreignObject 内的样式和交互
