# Worker 实施指南 — DynamicTopoGraph SVG 拓扑网络图重写

## 任务总览
将 `frontend/src/components/DynamicTopoGraph.tsx` 从垂直缩进目录树改造为水平 SVG 拓扑网络图。

## 综合设计方案（3 位 Explorer 分析成果汇总）

### 文件组织
新建 `frontend/src/components/topo/` 目录，创建以下文件：

1. `topoConfig.ts` — 布局常量配置（节点尺寸、间距、颜色）
2. `topoTypes.ts` — 布局专用类型（NodeLayout, EdgePath, LayoutResult）
3. `topoLayoutEngine.ts` — 纯 TypeScript 布局算法（零 React 依赖）
4. `TopoEdge.tsx` — 连线渲染组件（motion.path + pathLength 动画）
5. `TopoNode.tsx` — 节点渲染组件（foreignObject + motion.div）
6. 重写 `DynamicTopoGraph.tsx` — 主组件集成

### 关键技术决策（已确认）

1. **布局算法**: Reingold-Tilford 水平变体，O(n) 复杂度
   - 步骤: 扁平数组→树 → 计算子树高度 → 分配坐标 → 收集结果+连线
   - X坐标: depth * (columnWidth + levelGap)
   - Y坐标: 子树空间内居中

2. **foreignObject 方案**: 
   - ✅ 使用原生 `<foreignObject>`，内部用 `<motion.div>` 做动画
   - ❌ 不能用 `motion.foreignObject`（framer-motion v10 不支持）
   - foreignObject 内 Tailwind 完全正常工作

3. **LiveInterventionInput 集成**: 使用 CSS absolute 定位浮层方案
   - 不在 foreignObject 内嵌入表单控件（Firefox focus bug）
   - 浮层放在 SVG 外层同一 relative 容器内
   - SVG 不设 viewBox（1:1 像素映射），坐标直接等于 DOM 坐标

4. **动画方案**:
   - 节点出现: foreignObject 内 motion.div 做 opacity+scale 动画
   - Agent 呼吸发光: CSS keyframes `agent-glow-breath` + CSS 变量 `--glow-color`
   - 连线绘制: motion.path + pathLength 动画

5. **自动滚动**: container.scrollTo + smooth + 3秒用户滚动冷却

6. **SVG 画布**: 不设 viewBox，宽高为实际像素，容器 overflow-auto

### 节点尺寸规格
```typescript
const NODE_SIZES = {
  system: { w: 160, h: 52 },
  phase:  { w: 200, h: 60 },
  agent:  { w: 180, h: 52 },
  tool:   { w: 140, h: 40 },
};
```

### 间距配置
```typescript
const SPACING = {
  levelGap: 80,     // 层级间水平间距
  siblingGap: 16,   // 兄弟间垂直间距
};
const PADDING = { top: 30, right: 40, bottom: 30, left: 30 };
```

### 节点视觉设计

**system**: 深色实心 bg-slate-800，白文字，Server 图标
**phase**: 左侧竖条色带 bg-indigo-500，bg-indigo-50/50 背景，Network 图标
**agent**: border-2 使用 getAgentTheme().color，bgClass 使用 theme.bgClass，User 图标
**tool**: 虚线边框 1.5px dashed rgba(16,185,129,0.35)，bg-emerald-50/30，Wrench 图标

### 连线设计
- 贝塞尔曲线: M sx sy C cp1x cp1y, cp2x cp2y, tx ty
- cp1x = sx + dx*0.5, cp1y = sy; cp2x = tx - dx*0.5, cp2y = ty
- 颜色: active=#3B82F6, completed=#CBD5E1
- SVG marker 箭头

### 接口契约（不可违反）
- 必须 `export default function DynamicTopoGraph()`，零 props
- 内部使用 `const { agenticState, interruptAnalysis } = useStore()`
- 从 `../store/agenticTypes` 导入 `getAgentTheme, TopologyNode, TopologyEdge`
- 从 `./timeline/LiveInterventionInput` 导入 LiveInterventionInput
- 构建命令: cd frontend; npm run build (tsc && vite build)

### 边界条件处理
- 空节点: 显示等待提示占位符
- 单节点: 居中显示
- parentId 孤儿: 挂载到 root 或作为额外根
- edges source/target 不存在: 跳过该 edge

### CSS 需要添加的内容
agent-glow-breath keyframe 动画不修改现有 CSS 文件，改为在组件内使用 inline style 或 framer-motion animate 实现呼吸效果。因为约束是"不能修改所有 CSS 文件"。

**⚠️ 重要**: 由于不能修改 CSS 文件，呼吸发光改用 framer-motion 的 animate 循环:
```tsx
animate={{ 
  boxShadow: [
    `0 0 0 0 ${theme.color}40`,
    `0 0 16px 4px ${theme.color}40`,
    `0 0 0 0 ${theme.color}40`
  ]
}}
transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
```

## 受保护文件（绝对不能修改）
- agenticTypes.ts
- useStore.ts
- App.tsx
- DiagnosticDashboard.tsx
- LiveInterventionInput.tsx
- 所有 CSS 文件
- 所有其他现有组件

## 实施顺序
1. 创建 `frontend/src/components/topo/topoConfig.ts`
2. 创建 `frontend/src/components/topo/topoTypes.ts`
3. 创建 `frontend/src/components/topo/topoLayoutEngine.ts`
4. 创建 `frontend/src/components/topo/TopoEdge.tsx`
5. 创建 `frontend/src/components/topo/TopoNode.tsx`
6. 重写 `frontend/src/components/DynamicTopoGraph.tsx`
7. 运行 `npm run build` 验证
8. 用 `git diff` 确认零破坏

## Explorer 报告位置（参考资料）
- 布局算法设计: `.agents/explorer_layout/handoff.md`
- 节点渲染设计: `.agents/explorer_nodes/handoff.md`
- 集成风险分析: `.agents/explorer_integration/handoff.md`
