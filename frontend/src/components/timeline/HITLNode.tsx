/**
 * HITLNode.tsx — HITL(人机交互)内联节点
 * 嵌入时间线中，提供人类专家审查和修正交互界面
 */
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, Check } from 'lucide-react';

interface HITLNodeProps {
  /** 暂停原因 */
  reason: string;
  /** 恢复回调 */
  onResume: (action: 'Approve' | 'Revise', details: string) => void;
  /** 是否已解决 */
  isResolved: boolean;
  /** 是否只读模式 */
  readOnly?: boolean;
}

export default function HITLNode({ reason, onResume, isResolved, readOnly }: HITLNodeProps) {
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (action: 'Approve' | 'Revise') => {
    if (isSubmitting) return;
    setIsSubmitting(true);
    onResume(action, details);
  };

  return (
    <motion.div
      layout
      className={`
        rounded-2xl border-2 overflow-hidden transition-all duration-500
        ${isResolved
          ? 'border-emerald-300/50 bg-emerald-50/30'
          : 'border-amber-400/50 bg-gradient-to-br from-amber-50/80 to-orange-50/60 shadow-[0_0_25px_rgba(245,158,11,0.15)]'
        }
      `}
    >
      {/* 节点头部 */}
      <div className="flex items-center gap-3 px-5 py-4">
        {isResolved ? (
          <div className="w-7 h-7 rounded-full bg-emerald-500 flex items-center justify-center">
            <Check className="w-4 h-4 text-white" />
          </div>
        ) : (
          <div className="w-7 h-7 rounded-full bg-amber-500 flex items-center justify-center">
            <AlertCircle className="w-4 h-4 text-white" />
          </div>
        )}
        <div className="flex-1">
          <h3 className={`text-sm font-bold ${isResolved ? 'text-emerald-700' : 'text-amber-700'}`}>
            {isResolved ? '人类审查已完成' : '需要人类专家审查 (HITL)'}
          </h3>
          {isResolved && (
            <p className="text-xs text-emerald-600 mt-0.5">专家意见已纳入后续分析</p>
          )}
        </div>
      </div>

      {/* 展开区域：审查交互 */}
      <AnimatePresence>
        {!isResolved && !readOnly && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 space-y-3">
              {/* 暂停原因 */}
              <p className="text-sm text-slate-600 leading-relaxed bg-white/70 rounded-lg p-3 border border-amber-200/50">
                {reason || '智能体评估遭遇争议，需要人类专家介入决策。'}
              </p>

              {/* 文本输入区 */}
              <textarea
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="在此输入专家修正意见或裁决理由..."
                rows={3}
                className="w-full bg-white/90 border border-slate-200 text-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 transition resize-none placeholder-slate-400"
                disabled={isSubmitting}
              />

              {/* 操作按钮 */}
              <div className="flex space-x-3 justify-end">
                <button
                  onClick={() => handleSubmit('Revise')}
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-slate-100 text-slate-700 text-sm font-semibold rounded-xl hover:bg-slate-200 transition-all border border-slate-200 active:scale-95 disabled:opacity-50"
                >
                  专家修正
                </button>
                <button
                  onClick={() => handleSubmit('Approve')}
                  disabled={isSubmitting}
                  className="px-5 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-sm font-bold rounded-xl hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/20 active:scale-95 disabled:opacity-50"
                >
                  批准通过
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
