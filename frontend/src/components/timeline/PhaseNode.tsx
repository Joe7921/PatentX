/**
 * PhaseNode.tsx — 阶段节点组件
 * 展示每个阶段的状态(待处理/活跃/已完成)，可展开查看内部ReAct步骤
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ChevronDown, ChevronRight } from 'lucide-react';
import { getAgentTheme } from '../../store/agenticTypes';
import type { PhaseState } from '../../store/agenticTypes';
import ReactStepCard from './ReactStepCard';

interface PhaseNodeProps {
  /** 阶段数据 */
  phase: PhaseState;
  /** 是否默认展开 */
  isExpanded: boolean;
  /** 是否只读模式(仪表盘使用) */
  readOnly?: boolean;
  /** 内嵌子节点(如投票面板) */
  children?: React.ReactNode;
}

export default function PhaseNode({ phase, isExpanded: defaultExpanded, readOnly, children }: PhaseNodeProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  // 状态切换时同步展开状态
  React.useEffect(() => {
    if (phase.status === 'active') {
      setExpanded(true);
    }
  }, [phase.status]);

  // 根据阶段状态确定样式
  const getStatusStyle = () => {
    switch (phase.status) {
      case 'active':
        return {
          containerClass: 'border-blue-400/50 bg-white/95 shadow-[0_0_20px_rgba(59,130,246,0.15)]',
          headerClass: 'text-blue-700',
          dotClass: 'bg-blue-500 shadow-[0_0_12px_rgba(59,130,246,0.6)]',
          animate: true,
        };
      case 'completed':
        return {
          containerClass: 'border-emerald-300/50 bg-white/90',
          headerClass: 'text-emerald-700',
          dotClass: 'bg-emerald-500',
          animate: false,
        };
      case 'pending':
      default:
        return {
          containerClass: 'border-slate-200/60 bg-slate-50/60 border-dashed opacity-60',
          headerClass: 'text-slate-400',
          dotClass: 'bg-slate-300',
          animate: false,
        };
    }
  };

  const statusStyle = getStatusStyle();

  const handleToggle = () => {
    // 待处理阶段不可展开
    if (phase.status === 'pending') return;
    setExpanded(!expanded);
  };

  return (
    <motion.div
      layout
      className={`
        rounded-2xl border-2 overflow-hidden transition-shadow duration-500
        ${statusStyle.containerClass}
      `}
    >
      {/* 阶段头部 */}
      <div
        className="flex items-center gap-3 px-5 py-4 cursor-pointer select-none"
        onClick={handleToggle}
      >
        {/* 状态指示点 */}
        <div className="relative flex items-center justify-center">
          {phase.status === 'completed' ? (
            <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center">
              <Check className="w-4 h-4 text-white" />
            </div>
          ) : (
            <div className={`w-7 h-7 rounded-full ${statusStyle.dotClass} flex items-center justify-center`}>
              {statusStyle.animate && (
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-blue-400/50"
                  animate={{ scale: [1, 1.5, 1], opacity: [0.6, 0, 0.6] }}
                  transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                />
              )}
              <span className="text-white text-xs font-bold">{phase.id}</span>
            </div>
          )}
        </div>

        {/* 阶段标题 */}
        <div className="flex-1">
          <h3 className={`text-sm font-bold ${statusStyle.headerClass}`}>
            {phase.title}
          </h3>
          {phase.summary && (
            <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">{phase.summary}</p>
          )}
        </div>

        {/* 参与Agent图标 */}
        <div className="flex -space-x-1.5">
          {phase.agents.map((agentId) => {
            const theme = getAgentTheme(agentId);
            return (
              <div
                key={agentId}
                className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white border-2 border-white"
                style={{ backgroundColor: theme.color }}
                title={theme.name}
              >
                {theme.name.charAt(0)}
              </div>
            );
          })}
        </div>

        {/* 展开/折叠图标 */}
        {phase.status !== 'pending' && (
          <div className="text-slate-400">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </div>
        )}
      </div>

      {/* 展开区域：ReAct步骤列表 */}
      <AnimatePresence>
        {expanded && phase.status !== 'pending' && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 space-y-2.5">
              {phase.steps.length === 0 ? (
                <div className="text-xs text-slate-400 text-center py-3">等待步骤数据...</div>
              ) : (
                phase.steps.map((step, idx) => (
                  <ReactStepCard
                    key={`${step.agent}-${step.type}-${step.timestamp}-${idx}`}
                    step={step}
                    isLatest={idx === phase.steps.length - 1}
                    readOnly={readOnly}
                  />
                ))
              )}
              {/* 内嵌子节点(如投票面板) */}
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
