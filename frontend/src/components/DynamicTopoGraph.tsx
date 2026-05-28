/**
 * DynamicTopoGraph.tsx — 水平 SVG 拓扑网络图主组件
 * 将 TopologyNode[] 扁平数据通过 Reingold-Tilford 水平变体布局为 SVG 拓扑图
 *
 * 技术方案：
 * - SVG 不设 viewBox，1:1 像素映射，容器 overflow-auto 滚动
 * - foreignObject + motion.div 渲染节点卡片
 * - motion.path + pathLength 绘制连线动画
 * - LiveInterventionInput 使用 CSS absolute 浮层定位（不在 foreignObject 内嵌入）
 * - 新节点出现时自动滚动到 active 节点，3 秒用户滚动冷却
 */

import React, { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { useStore } from '../store/useStore';
import type { TopologyNode } from '../store/agenticTypes';
import LiveInterventionInput from './timeline/LiveInterventionInput';
import { Network, MoreHorizontal } from 'lucide-react';

import { computeTopoLayout } from './topo/topoLayoutEngine';
import { TOPO_LAYOUT_CONFIG } from './topo/topoConfig';
import type { NodeLayout } from './topo/topoTypes';
import TopoNode from './topo/TopoNode';
import TopoEdge, { TopoEdgeDefs } from './topo/TopoEdge';

export default function DynamicTopoGraph() {
  const { agenticState, interruptAnalysis } = useStore();
  const [isInterrupting, setIsInterrupting] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  /** 用户是否在主动滚动（3 秒冷却期内为 true） */
  const userScrolledRef = useRef(false);
  const scrollTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  /** 标记是否由程序触发的滚动（避免将程序滚动误判为用户滚动） */
  const programmaticScrollRef = useRef(false);

  const nodes = agenticState.topologyNodes || [];
  const edges = agenticState.topologyEdges || [];

  // 计算布局（节点/连线变化时自动重算，O(n) 复杂度）
  const layout = useMemo(
    () => computeTopoLayout(nodes, edges),
    [nodes, edges]
  );

  // 打断处理
  const handleInterrupt = useCallback(async (msg: string) => {
    setIsInterrupting(true);
    const res = await interruptAnalysis(msg);
    setIsInterrupting(false);
    return res;
  }, [interruptAnalysis]);

  // 找到最后一个 active 节点（用于显示 LiveInterventionInput 浮层）
  const activeNode: TopologyNode | undefined = useMemo(() => {
    // 从后往前找最后一个 active 节点
    for (let i = nodes.length - 1; i >= 0; i--) {
      if (nodes[i].status === 'active') return nodes[i];
    }
    return undefined;
  }, [nodes]);

  // 获取 active 节点的布局信息（用于浮层定位）
  const activeNodeLayout: NodeLayout | undefined = useMemo(() => {
    if (!activeNode) return undefined;
    return layout.nodes.find((nl) => nl.nodeId === activeNode.id);
  }, [activeNode, layout.nodes]);

  // ============================================================
  // 自动滚动逻辑
  // ============================================================

  // 监听用户主动滚动
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      // 如果是程序触发的滚动，不标记为用户滚动
      if (programmaticScrollRef.current) return;

      userScrolledRef.current = true;
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
      // 3 秒后恢复自动跟踪
      scrollTimeoutRef.current = setTimeout(() => {
        userScrolledRef.current = false;
      }, 3000);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (scrollTimeoutRef.current) clearTimeout(scrollTimeoutRef.current);
    };
  }, []);

  // 新节点出现时自动滚动到 active 节点
  useEffect(() => {
    if (userScrolledRef.current || !activeNodeLayout || !containerRef.current) return;

    const container = containerRef.current;
    const { x, y, width, height } = activeNodeLayout;

    // 将 active 节点滚动到容器可视区域中心
    const targetScrollLeft = x + width / 2 - container.clientWidth / 2;
    const targetScrollTop = y + height / 2 - container.clientHeight / 2;

    // 标记为程序滚动，避免触发用户滚动冷却
    programmaticScrollRef.current = true;
    container.scrollTo({
      left: Math.max(0, targetScrollLeft),
      top: Math.max(0, targetScrollTop),
      behavior: 'smooth',
    });
    // 延迟重置标记（smooth 滚动有动画时间）
    setTimeout(() => {
      programmaticScrollRef.current = false;
    }, 600);
  }, [activeNodeLayout]);

  // ============================================================
  // 画布尺寸计算
  // ============================================================

  // SVG 画布尺寸取布局计算值和容器最小尺寸的较大值
  const svgWidth = Math.max(layout.canvasWidth, 400);
  const svgHeight = Math.max(layout.canvasHeight, 200);

  // ============================================================
  // 渲染
  // ============================================================

  // 空状态
  if (nodes.length === 0) {
    return (
      <div className="w-full h-full pb-20 pt-2 px-1">
        <div className="sticky top-0 bg-white/90 backdrop-blur-xl z-30 pb-4 border-b border-gemini-outline mb-6">
          <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
            <Network className="w-4 h-4 text-blue-500" />
            动态评估拓扑流
          </h2>
          <p className="text-xs text-slate-500 mt-1.5 font-medium">
            实时观测 Agent 协作与工具调用图谱，点击节点下方可随时介入打断
          </p>
        </div>
        <div className="flex flex-col items-center justify-center h-40 text-slate-400">
          <MoreHorizontal className="w-6 h-6 animate-pulse mb-2" />
          <span className="text-sm">等待分析启动...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full pb-20 pt-2 px-1">
      {/* 标题栏 — 固定在容器顶部 */}
      <div className="sticky top-0 bg-white/90 backdrop-blur-xl z-30 pb-4 border-b border-gemini-outline mb-6">
        <h2 className="text-base font-semibold text-slate-800 flex items-center gap-2">
          <Network className="w-4 h-4 text-blue-500" />
          动态评估拓扑流
        </h2>
        <p className="text-xs text-slate-500 mt-1.5 font-medium">
          实时观测 Agent 协作与工具调用图谱，点击节点下方可随时介入打断
        </p>
      </div>

      {/* SVG 拓扑画布容器 — relative 定位用于 absolute 浮层 */}
      <div
        ref={containerRef}
        className="relative w-full overflow-auto custom-scrollbar"
        style={{ maxHeight: 'calc(100% - 80px)' }}
      >
        {/* SVG 画布 — 不设 viewBox，1:1 像素映射 */}
        <svg
          width={svgWidth}
          height={svgHeight}
          className="block select-none"
        >
          {/* SVG marker 箭头定义 */}
          <TopoEdgeDefs />

          {/* 连线层（先渲染，在底层） */}
          <g className="topo-edges">
            {layout.edges.map((edge) => (
              <TopoEdge key={edge.edgeId} edge={edge} />
            ))}
          </g>

          {/* 节点层（后渲染，在上层） */}
          <g className="topo-nodes">
            {layout.nodes.map((nodeLayout) => {
              const topoNode = nodes.find((n) => n.id === nodeLayout.nodeId);
              if (!topoNode) return null;
              return (
                <TopoNode
                  key={nodeLayout.nodeId}
                  node={topoNode}
                  layout={nodeLayout}
                />
              );
            })}
          </g>
        </svg>

        {/* LiveInterventionInput 浮层 — CSS absolute 定位在 SVG 外层 */}
        {/* SVG 不设 viewBox，坐标直接等于 DOM 坐标，无需转换 */}
        {activeNode && activeNodeLayout && (
          <div
            style={{
              position: 'absolute',
              left: activeNodeLayout.x,
              top: activeNodeLayout.y + activeNodeLayout.height + 8,
              zIndex: 50,
            }}
          >
            <LiveInterventionInput
              onSubmit={handleInterrupt}
              isSubmitting={isInterrupting}
            />
          </div>
        )}
      </div>
    </div>
  );
}
