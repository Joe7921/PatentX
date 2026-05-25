/**
 * ReactStepCard.tsx — ReAct步骤卡片组件
 * 用于展示Think/Act/Observe三种步骤，支持滑入动画和打字机效果
 */
import React from 'react';
import { motion } from 'framer-motion';
import { Lightbulb, Zap, Eye } from 'lucide-react';
import { getAgentTheme } from '../../store/agenticTypes';
import type { ReactStep } from '../../store/agenticTypes';
import TypewriterText from './TypewriterText';

interface ReactStepCardProps {
  /** 步骤数据 */
  step: ReactStep;
  /** 是否为最新的步骤(使用打字机效果) */
  isLatest: boolean;
  /** 是否为只读模式(仪表盘中不播放打字机) */
  readOnly?: boolean;
}

export default function ReactStepCard({ step, isLatest, readOnly }: ReactStepCardProps) {
  const theme = getAgentTheme(step.agent);

  // 根据步骤类型确定样式和图标
  const getStepStyle = () => {
    switch (step.type) {
      case 'think':
        return {
          bgClass: 'bg-slate-100/80 border-slate-200/60',
          icon: <Lightbulb className="w-4 h-4 text-slate-500" />,
          label: '思考',
          labelClass: 'text-slate-500 bg-slate-200/60',
          contentClass: 'italic text-slate-600',
          pulse: isLatest && !readOnly,
        };
      case 'act':
        return {
          bgClass: `${theme.bgClass} ${theme.borderClass}`,
          icon: <Zap className="w-4 h-4" style={{ color: theme.color }} />,
          label: step.tool ? `执行: ${step.tool}` : '执行',
          labelClass: `${theme.textClass} ${theme.bgClass}`,
          contentClass: 'text-slate-700',
          pulse: false,
        };
      case 'observe':
        return {
          bgClass: 'bg-white/90 border-slate-200/60',
          icon: <Eye className="w-4 h-4 text-emerald-500" />,
          label: '观察',
          labelClass: 'text-emerald-600 bg-emerald-50/80',
          contentClass: 'text-slate-600 font-mono text-xs',
          pulse: false,
        };
    }
  };

  const style = getStepStyle();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`
        relative p-3.5 rounded-xl border backdrop-blur-sm
        ${style.bgClass}
        ${style.pulse ? 'animate-pulse' : ''}
      `}
    >
      <div className="flex items-start gap-3">
        {/* Agent头像 */}
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 shadow-sm"
          style={{ backgroundColor: theme.color }}
        >
          {theme.name.charAt(0)}
        </div>

        <div className="flex-1 min-w-0">
          {/* 头部：Agent名 + 步骤标签 */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-xs font-semibold text-slate-700">{theme.name}</span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${style.labelClass}`}>
              {style.label}
            </span>
            {/* 步骤类型图标 */}
            <span className="ml-auto">{style.icon}</span>
          </div>

          {/* 内容区 */}
          <div className={`text-sm leading-relaxed ${style.contentClass}`}>
            {isLatest && !readOnly ? (
              <TypewriterText text={step.content} speed={25} />
            ) : (
              step.content
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
