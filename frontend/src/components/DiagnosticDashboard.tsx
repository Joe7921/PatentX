import React from 'react';
import { useStore } from '../store/useStore';
import { RefreshCw, Shield, Award, Eye, ChevronDown, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DynamicTopoGraph from './DynamicTopoGraph';
import DebateLogPanel from './dashboard/DebateLogPanel';
import AlignmentMatrix from './dashboard/AlignmentMatrix';

export default function DiagnosticDashboard() {
  const { blackboard, evalId, resetAnalysis, step, showReasoningTimeline, toggleReasoningTimeline } = useStore();

  const prob = blackboard?.overall_probability !== undefined && blackboard.overall_probability !== null 
    ? blackboard.overall_probability 
    : 0;
  const conclusion = blackboard?.overall_conclusion || '评估结论生成中...';
  const debateLogs = blackboard?.debate_logs || [];
  const patents = blackboard?.retrieved_patents || [];
  const matrices = blackboard?.feature_alignment_matrices || {};

  // 提取当前活动的特征 ID（最新辩论提及）
  const getActiveFeatureId = () => {
    if (step !== 'THINKING' && step !== 'PAUSED') return null;
    for (let i = debateLogs.length - 1; i >= 0; i--) {
      const match = debateLogs[i].match(/DF_(\d+)/);
      if (match) return `DF_${match[1]}`;
    }
    return null;
  };

  const activeFeatureId = getActiveFeatureId();

  // 根据授权概率确定颜色
  const getProbColor = (p: number) => {
    if (p >= 0.8) return { text: 'text-emerald-500', border: 'border-emerald-200', bg: 'bg-emerald-50', glow: 'shadow-emerald-500/10' };
    if (p >= 0.5) return { text: 'text-amber-500', border: 'border-amber-200', bg: 'bg-amber-50', glow: 'shadow-amber-500/10' };
    return { text: 'text-rose-500', border: 'border-rose-200', bg: 'bg-rose-50', glow: 'shadow-rose-500/10' };
  };

  const probStyle = getProbColor(prob);

  return (
    <div className="space-y-8 py-2">
      {/* 头部标题与重置 */}
      <div className={`flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-200 pb-5 gap-4 transition-all duration-500 ${
        step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
      }`}>
        <div>
          <h2 className="text-2xl font-bold text-slate-800 font-outfit flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-500" />
            PatentX 专利新颖性诊断看板
          </h2>
          <p className="text-slate-500 text-sm mt-1">评估流水号: <span className="text-slate-600 font-mono">{evalId || 'N/A'}</span></p>
        </div>
        <button
          onClick={resetAnalysis}
          className="flex items-center gap-2 px-4 py-2 bg-white text-slate-600 hover:text-blue-600 rounded-xl hover:bg-slate-50 transition-all border border-slate-200 shadow-sm active:scale-95 text-sm font-semibold"
        >
          <RefreshCw className="w-4 h-4" />
          重新分析
        </button>
      </div>

      {/* 查看推理过程折叠区 */}
      <div className="border-b border-slate-200 pb-4">
        <button
          onClick={toggleReasoningTimeline}
          className="flex items-center gap-2 px-4 py-2.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-xl transition-all border border-blue-200/50 text-sm font-semibold w-full justify-center"
        >
          <Eye className="w-4 h-4" />
          {showReasoningTimeline ? '收起完整评估拓扑' : '展开完整评估拓扑'}
          {showReasoningTimeline ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </button>
        <AnimatePresence>
          {showReasoningTimeline && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.35, ease: 'easeInOut' }}
              className="overflow-hidden mt-4"
            >
              <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50/50 max-h-[600px] overflow-y-auto">
                <DynamicTopoGraph />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 核心结论及通过概率 */}
      <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 transition-all duration-500 ${
        step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
      }`}>
        <div className={`col-span-1 rounded-2xl border p-6 flex flex-col justify-center items-center text-center shadow-sm ${probStyle.border} ${probStyle.bg} ${probStyle.glow} transition-all duration-500`}>
          <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider mb-2">授权预估概率</span>
          <span className={`text-5xl font-extrabold font-outfit ${probStyle.text}`}>
            {(prob * 100).toFixed(1)}%
          </span>
          <div className="mt-4 w-full bg-slate-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-1000 ${
                prob >= 0.8 ? 'bg-emerald-500' : prob >= 0.5 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${prob * 100}%` }}
            />
          </div>
        </div>

        <div className="col-span-1 md:col-span-2 rounded-2xl border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between">
          <div>
            <span className="text-slate-500 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <Award className="w-4 h-4 text-blue-500" />
              裁决意见卡片
            </span>
            <p className="text-slate-700 text-sm leading-relaxed font-medium">
              {conclusion}
            </p>
          </div>
          <div className="border-t border-slate-200 pt-3 mt-4 text-xs text-slate-400 flex justify-between">
            <span>分析引擎：PatentX Nested-Multi-Agent v2.0</span>
            <span>合规审查：欧洲专利公约 (EPC) 标准</span>
          </div>
        </div>
      </div>

      {/* 左右分栏布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左侧：辩论日志 */}
        <DebateLogPanel 
          debateLogs={debateLogs} 
          activeFeatureId={activeFeatureId} 
        />
        
        {/* 右侧：比对矩阵与特征分析 */}
        <AlignmentMatrix 
          patents={patents} 
          matrices={matrices} 
          activeFeatureId={activeFeatureId} 
        />
      </div>
    </div>
  );
}
