/**
 * TopoEdge.tsx — 拓扑连线渲染组件
 * 使用 motion.path 实现 pathLength 绘制动画 + SVG marker 箭头
 */

import React from 'react';
import { motion } from 'framer-motion';
import { TOPO_LAYOUT_CONFIG } from './topoConfig';
import type { EdgePath } from './topoTypes';

interface TopoEdgeProps {
  /** 连线路径数据 */
  edge: EdgePath;
}

/** 箭头 marker 的唯一 ID（全局共用） */
export const ARROW_MARKER_ACTIVE_ID = 'topo-arrow-active';
export const ARROW_MARKER_COMPLETED_ID = 'topo-arrow-completed';

/**
 * SVG marker 箭头定义（放在 <defs> 中）
 * 需要在 SVG 画布中渲染一次
 */
export function TopoEdgeDefs() {
  return (
    <defs>
      {/* active 状态箭头 */}
      <marker
        id={ARROW_MARKER_ACTIVE_ID}
        viewBox="0 0 10 7"
        refX="9"
        refY="3.5"
        markerWidth="8"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path
          d="M 0 0 L 10 3.5 L 0 7 Z"
          fill={TOPO_LAYOUT_CONFIG.edge.activeColor}
        />
      </marker>
      {/* completed 状态箭头 */}
      <marker
        id={ARROW_MARKER_COMPLETED_ID}
        viewBox="0 0 10 7"
        refX="9"
        refY="3.5"
        markerWidth="8"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path
          d="M 0 0 L 10 3.5 L 0 7 Z"
          fill={TOPO_LAYOUT_CONFIG.edge.completedColor}
          opacity={0.4}
        />
      </marker>
    </defs>
  );
}

/**
 * 单条连线渲染组件
 * 使用 motion.path 实现线条从 0 到 1 的"画出来"动画
 */
const TopoEdge: React.FC<TopoEdgeProps> = React.memo(({ edge }) => {
  const isActive = edge.status === 'active';
  const color = isActive
    ? TOPO_LAYOUT_CONFIG.edge.activeColor
    : TOPO_LAYOUT_CONFIG.edge.completedColor;
  const markerId = isActive
    ? ARROW_MARKER_ACTIVE_ID
    : ARROW_MARKER_COMPLETED_ID;

  return (
    <motion.path
      d={edge.path}
      fill="none"
      stroke={color}
      strokeWidth={TOPO_LAYOUT_CONFIG.edge.strokeWidth}
      opacity={isActive ? 0.8 : 0.4}
      markerEnd={`url(#${markerId})`}
      initial={{ pathLength: 0, opacity: 0 }}
      animate={{ pathLength: 1, opacity: isActive ? 0.8 : 0.4 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    />
  );
});

TopoEdge.displayName = 'TopoEdge';

export default TopoEdge;
