# Original User Request

## Initial Request — 2026-05-26T21:21:21+08:00

重写 PatentX 前端的 `DynamicTopoGraph.tsx` 组件，将其从当前的垂直缩进目录树列表彻底改造为**从左到右水平流向的 SVG 拓扑网络图**，还原用户原始草图设计。草图核心：起点"主"节点在最左侧，Agent 和 Tool 节点从左向右分叉展开，节点之间用带箭头的贝塞尔曲线连接。

Working directory: d:\Antigravity projects\PatentX
Integrity mode: development

## 关键上下文

### 数据源（已存在，不可修改）
- `frontend/src/store/agenticTypes.ts` 中定义了 `TopologyNode`（字段：id, type, status, label, agentId?, toolName?, content?, parentId?, timestamp）和 `TopologyEdge`（字段：id, source, target, status）
- `TopologyNode.type` 取值为 `'system' | 'phase' | 'agent' | 'tool'`
- `TopologyNode.parentId` 建立了树状父子关系
- `frontend/src/store/useStore.ts` 中的 SSE 事件处理器会自动向 `agenticState.topologyNodes` 和 `agenticState.topologyEdges` 推入新节点和连线
- `AGENT_THEMES` 字典（在 `agenticTypes.ts`）提供了每个 Agent 角色的主题色、bgClass、borderClass、textClass

### 现有集成点（不可修改）
- `App.tsx` 在 THINKING/PAUSED 状态的左侧面板中渲染 `<DynamicTopoGraph />`
- `DiagnosticDashboard.tsx` 在折叠区中也渲染 `<DynamicTopoGraph />`
- `LiveInterventionInput.tsx`（在 `components/timeline/`）是一个已存在的默认折叠输入组件，接口为 `{ onSubmit: (msg: string) => Promise<boolean> | void; isSubmitting?: boolean }`，必须继续挂载在当前 active 节点附近

### 技术栈约束
- 只能使用项目已有依赖：React、framer-motion、Tailwind CSS、Zustand、lucide-react
- **绝对禁止 npm install 任何新包**
- 所有代码注释和 UI 文本必须使用简体中文
- Windows PowerShell 环境，禁止用 PowerShell 修改源码文件

## Requirements

### R1. 水平自动布局引擎
实现一个纯 TypeScript 的水平树状自动布局算法。输入为 `TopologyNode[]`（通过 `parentId` 隐含的树结构），输出为每个节点的 `{ x, y, width, height }` 坐标。布局方向从左到右，子节点在父节点右侧垂直排列并居中对齐。节点尺寸和间距参数必须集中管理为常量配置对象，不能散落为魔法数字。

### R2. SVG 画布与连线渲染
使用 SVG `<path>` 绘制从源节点右侧中点到目标节点左侧中点的贝塞尔曲线连线，连线末端带箭头（SVG `<marker>`）。连线颜色根据 `TopologyEdge.status` 区分：`active` 为蓝色，`completed` 为浅灰。新连线出现时应有从起点到终点的流动绘制动画（利用 framer-motion 的 pathLength 或 SVG stroke-dasharray 动画）。

### R3. 节点渲染与类型区分
所有节点形状统一为**圆角矩形**。通过以下视觉维度区分类型：
- `system` 节点：深色实心背景，视觉起点锚
- `phase` 节点：最大尺寸，有左侧竖条色带
- `agent` 节点：使用 `AGENT_THEMES` 的主题色作为实线粗边框，active 时边框有呼吸发光动画
- `tool` 节点：较小尺寸，虚线细边框，中性灰绿色调
节点使用 SVG `foreignObject` 嵌入 HTML div，以便使用 Tailwind 样式和 framer-motion 动画。

### R4. 交互与集成
- 整个画布容器必须支持水平和垂直滚动（overflow-auto）
- 新节点出现时自动滚动到最新 active 节点
- `LiveInterventionInput` 组件必须挂载在当前 active 节点附近（CSS absolute 定位浮层或直接嵌入 foreignObject），保持其原有的折叠/展开交互

### R5. 零破坏约束
以下文件**绝对不能修改**：
- `agenticTypes.ts`
- `useStore.ts`
- `App.tsx`
- `DiagnosticDashboard.tsx`
- `LiveInterventionInput.tsx`
- 所有 CSS 文件和其他现有组件

唯一允许的修改：覆盖重写 `DynamicTopoGraph.tsx`。允许新建文件（布局算法、节点组件、连线组件等）。

## Acceptance Criteria

### 1. 构建通过
- [ ] 在 `frontend/` 目录运行 `npm run build` 必须零 TypeScript 报错

### 2. 布局正确性
- [ ] 根节点（system）位于画布最左侧
- [ ] 子节点始终位于父节点的右侧
- [ ] 同一父节点的多个子节点在垂直方向上均匀分布且不重叠
- [ ] 节点之间有贝塞尔曲线连线，连线末端有箭头指向子节点

### 3. 视觉区分
- [ ] 四种节点类型（system/phase/agent/tool）在视觉上可明确区分
- [ ] Agent 节点使用 `AGENT_THEMES` 中对应角色的主题色

### 4. 交互完整
- [ ] LiveInterventionInput 在 active 节点附近正常显示，折叠/展开/提交功能完整
- [ ] 画布可滚动，新节点出现时自动滚动到视野内

### 5. 零回归
- [ ] `agenticTypes.ts`、`useStore.ts`、`App.tsx`、`DiagnosticDashboard.tsx`、`LiveInterventionInput.tsx` 的内容与修改前完全一致（可用 git diff 验证）
