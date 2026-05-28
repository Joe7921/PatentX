/**
 * TopoNode.tsx — 拓扑节点渲染组件
 * 使用 foreignObject + motion.div 实现节点卡片渲染
 * 支持四种节点类型视觉区分：system / phase / agent / tool
 */

import React from 'react';
import { motion } from 'framer-motion';
import { Network, Server, User, Wrench, CheckCircle2 } from 'lucide-react';
import { getAgentTheme, type TopologyNode } from '../../store/agenticTypes';
import type { NodeLayout } from './topoTypes';

interface TopoNodeProps {
  /** 原始拓扑节点数据 */
  node: TopologyNode;
  /** 节点布局定位信息 */
  layout: NodeLayout;
}

/** 节点出现的过渡动画配置 */
const nodeTransition = { duration: 0.35, ease: [0.32, 0.72, 0, 1] as const };

/**
 * system 节点 — 深色 bg-slate-800 白文字
 */
function SystemNodeCard({ node }: { node: TopologyNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={nodeTransition}
      className="w-full h-full flex items-center gap-2.5 px-4 rounded-xl bg-slate-800 text-white shadow-lg"
    >
      <div className="p-1.5 rounded-lg bg-white/15 flex-shrink-0">
        <Server className="w-4 h-4 text-white/90" />
      </div>
      <span className="text-xs font-bold tracking-wide truncate">
        {node.label}
      </span>
    </motion.div>
  );
}

/**
 * phase 节点 — 左侧竖条 bg-indigo-500 色带
 */
function PhaseNodeCard({ node }: { node: TopologyNode }) {
  const isActive = node.status === 'active';
  const isCompleted = node.status === 'completed';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={nodeTransition}
      className="w-full h-full flex rounded-2xl border border-indigo-200/50 bg-indigo-50/50 shadow-sm overflow-hidden"
    >
      {/* 左侧竖条色带 */}
      <div className="w-1.5 flex-shrink-0 bg-indigo-500 rounded-l-2xl" />
      <div className="flex-1 flex items-center gap-3 px-4 min-w-0">
        <div className="p-1.5 rounded-xl bg-white shadow-sm border border-indigo-200/50 flex-shrink-0">
          <Network className="w-4 h-4 text-indigo-500" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="font-semibold text-sm text-indigo-800 truncate block">
            {node.label}
          </span>
          {isCompleted && (
            <span className="text-[10px] text-indigo-400 font-medium">
              已完成
            </span>
          )}
        </div>
        {/* 状态指示 */}
        {isActive && (
          <span className="flex h-2.5 w-2.5 rounded-full bg-indigo-500 relative flex-shrink-0">
            <span className="absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75 animate-ping" />
          </span>
        )}
        {isCompleted && (
          <CheckCircle2 className="w-4 h-4 text-emerald-500 opacity-60 flex-shrink-0" />
        )}
      </div>
    </motion.div>
  );
}

/**
 * agent 节点 — border-2 使用 getAgentTheme().color + 呼吸发光动画
 */
function AgentNodeCard({ node }: { node: TopologyNode }) {
  const theme = getAgentTheme(node.agentId || '');
  const isActive = node.status === 'active';
  const isCompleted = node.status === 'completed';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{
        opacity: 1,
        scale: 1,
        // active 时使用 framer-motion 实现呼吸发光（不修改 CSS 文件）
        boxShadow: isActive
          ? [
              `0 0 0 0 ${theme.color}40`,
              `0 0 16px 4px ${theme.color}40`,
              `0 0 0 0 ${theme.color}40`,
            ]
          : `0 1px 2px 0 rgb(0 0 0 / 0.05)`,
      }}
      transition={{
        ...nodeTransition,
        // 呼吸发光循环动画配置
        boxShadow: isActive
          ? { duration: 2.5, repeat: Infinity, ease: 'easeInOut' }
          : { duration: 0.35 },
      }}
      className={`w-full h-full flex items-center gap-3 px-4 rounded-xl border-2 ${theme.bgClass} shadow-sm`}
      style={{ borderColor: theme.color }}
    >
      <div
        className={`p-1.5 rounded-lg bg-white shadow-sm border ${theme.borderClass} flex-shrink-0`}
      >
        <User className={`w-4 h-4 ${theme.textClass}`} />
      </div>
      <div className="min-w-0 flex-1">
        <span
          className={`font-semibold text-sm truncate block ${theme.textClass}`}
        >
          {node.label}
        </span>
      </div>
      {isActive && (
        <span
          className="flex h-2 w-2 rounded-full relative flex-shrink-0"
          style={{ backgroundColor: theme.color }}
        >
          <span
            className="absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping"
            style={{ backgroundColor: theme.color }}
          />
        </span>
      )}
      {isCompleted && (
        <CheckCircle2 className="w-4 h-4 text-emerald-500 opacity-50 flex-shrink-0" />
      )}
    </motion.div>
  );
}

/**
 * tool 节点 — 虚线 1.5px dashed 边框
 */
function ToolNodeCard({ node }: { node: TopologyNode }) {
  const isCompleted = node.status === 'completed';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={nodeTransition}
      className="w-full h-full flex items-center gap-2.5 px-3 rounded-lg bg-emerald-50/30"
      style={{ border: '1.5px dashed rgba(16, 185, 129, 0.35)' }}
    >
      <div className="p-1 rounded-md bg-white/80 border border-emerald-200/40 flex-shrink-0">
        <Wrench className="w-3.5 h-3.5 text-emerald-500" />
      </div>
      <span className="text-xs font-medium text-emerald-700 truncate flex-1">
        {node.label}
      </span>
      {isCompleted && (
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 opacity-40 flex-shrink-0" />
      )}
    </motion.div>
  );
}

/**
 * 拓扑节点渲染组件
 * 使用原生 <foreignObject>（framer-motion v10 不支持 motion.foreignObject）
 * 内部用 motion.div 做入场动画和呼吸发光
 */
const TopoNode: React.FC<TopoNodeProps> = React.memo(({ node, layout }) => {
  const { x, y, width, height } = layout;

  // 根据节点类型选择渲染卡片
  let card: React.ReactNode;
  switch (node.type) {
    case 'system':
      card = <SystemNodeCard node={node} />;
      break;
    case 'phase':
      card = <PhaseNodeCard node={node} />;
      break;
    case 'agent':
      card = <AgentNodeCard node={node} />;
      break;
    case 'tool':
      card = <ToolNodeCard node={node} />;
      break;
    default:
      card = <SystemNodeCard node={node} />;
  }

  return (
    <foreignObject
      x={x}
      y={y}
      width={width}
      height={height}
      overflow="visible"
    >
      {card}
    </foreignObject>
  );
});

TopoNode.displayName = 'TopoNode';

export default TopoNode;
