import React, { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';
import { RefreshCw, Shield, Award, Layers, MessageSquare, ChevronDown, ChevronRight, Eye } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ThinkingIndicator from './ThinkingIndicator';
import AgenticPauseCard from './AgenticPauseCard';
import AgenticTimeline from './AgenticTimeline';

interface Particle {
  id: string;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  onComplete: () => void;
}

export default function DiagnosticDashboard() {
  const { blackboard, evalId, resetAnalysis, step, currentAction, resumeAnalysis, showReasoningTimeline, toggleReasoningTimeline } = useStore();

  const [localAnnotations, setLocalAnnotations] = useState<Record<string, string>>({});
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [tempAnnotation, setTempAnnotation] = useState<string>('');
  const [isClosing, setIsClosing] = useState<boolean>(false);
  const [particles, setParticles] = useState<Particle[]>([]);

  const prob = blackboard?.overall_probability !== undefined && blackboard.overall_probability !== null 
    ? blackboard.overall_probability 
    : 0;
  const conclusion = blackboard?.overall_conclusion || '评估结论生成中...';
  const debateLogs = blackboard?.debate_logs || [];
  const patents = blackboard?.retrieved_patents || [];
  const matrices = blackboard?.feature_alignment_matrices || {};

  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSaveAnnotation = (rowKey: string, annotation: string, buttonEl: HTMLElement) => {
    const badgeEl = document.getElementById(`badge-${rowKey}`);
    if (!badgeEl) {
      setLocalAnnotations(prev => ({ ...prev, [rowKey]: annotation }));
      setEditingKey(null);
      return;
    }
    
    const buttonRect = buttonEl.getBoundingClientRect();
    const badgeRect = badgeEl.getBoundingClientRect();
    
    const startX = buttonRect.left + buttonRect.width / 2 - 6;
    const startY = buttonRect.top + buttonRect.height / 2 - 6;
    const endX = badgeRect.left + badgeRect.width / 2 - 6;
    const endY = badgeRect.top + badgeRect.height / 2 - 6;
    
    const newParticle: Particle = {
      id: `p-${Date.now()}-${Math.random()}`,
      startX,
      startY,
      endX,
      endY,
      onComplete: () => {
        setLocalAnnotations(prev => ({ ...prev, [rowKey]: annotation }));
        setEditingKey(null);
        setParticles(prev => prev.filter(p => p.id !== newParticle.id));
      }
    };
    
    setParticles(prev => [...prev, newParticle]);
  };

  const getConflictKeys = () => {
    const keys: string[] = [];
    Object.entries(matrices).forEach(([priorId, alignments]) => {
      (alignments as any[]).forEach((item, index) => {
        if (item.status === 'Fully_Disclosed') {
          const key = `${item.domestic_feature_id || `DF_${index}`}_${priorId}_${item.prior_art_feature_id}`;
          keys.push(key);
        }
      });
    });
    return keys;
  };

  const handleGlobalResume = async (action: 'Approve' | 'Revise', details: string) => {
    if (action === 'Approve') {
      setIsClosing(true);
      setTimeout(async () => {
        await resumeAnalysis('Approve', details);
        setIsClosing(false);
      }, 500);
      return;
    }
    
    if (Object.keys(localAnnotations).length > 0) {
      setIsClosing(true);
      setTimeout(async () => {
        await resumeAnalysis('Revise', JSON.stringify(localAnnotations));
        setIsClosing(false);
      }, 500);
    } else {
      const conflictKeys = getConflictKeys();
      if (conflictKeys.length === 0) {
        setIsClosing(true);
        setTimeout(async () => {
          await resumeAnalysis('Revise', JSON.stringify({}));
          setIsClosing(false);
        }, 500);
        return;
      }
      
      const textareaEl = document.getElementById('global-pause-textarea');
      const textRect = textareaEl ? textareaEl.getBoundingClientRect() : null;
      const startX = textRect ? textRect.left + textRect.width / 2 - 6 : window.innerWidth / 2 - 6;
      const startY = textRect ? textRect.bottom - 6 : window.innerHeight / 2 - 6;
      
      const mergedAnnotations: Record<string, string> = {};
      conflictKeys.forEach(k => {
        mergedAnnotations[k] = details || '专家修正意见';
      });
      
      let completedCount = 0;
      const totalParticles = conflictKeys.length;
      
      conflictKeys.forEach((k, idx) => {
        const badgeEl = document.getElementById(`badge-${k}`);
        const badgeRect = badgeEl ? badgeEl.getBoundingClientRect() : null;
        const endX = badgeRect ? badgeRect.left + badgeRect.width / 2 - 6 : window.innerWidth / 2 - 6;
        const endY = badgeRect ? badgeRect.top + badgeRect.height / 2 - 6 : window.innerHeight / 2 - 6;
        
        const newParticle: Particle = {
          id: `p-global-${idx}-${Date.now()}-${Math.random()}`,
          startX,
          startY,
          endX,
          endY,
          onComplete: () => {
            setLocalAnnotations(prev => ({ ...prev, [k]: details || '专家修正意见' }));
            setParticles(prev => prev.filter(p => p.id !== newParticle.id));
            
            completedCount++;
            if (completedCount === totalParticles) {
              setIsClosing(true);
              setTimeout(async () => {
                await resumeAnalysis('Revise', JSON.stringify(mergedAnnotations));
                setIsClosing(false);
              }, 500);
            }
          }
        };
        
        setParticles(prev => [...prev, newParticle]);
      });
    }
  };

  // 自动滚动到日志底部
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [debateLogs.length]);

  // 根据授权概率确定颜色
  const getProbColor = (p: number) => {
    if (p >= 0.8) return { text: 'text-emerald-400', border: 'border-emerald-500/30', bg: 'bg-emerald-500/10', glow: 'shadow-emerald-500/20' };
    if (p >= 0.5) return { text: 'text-amber-400', border: 'border-amber-500/30', bg: 'bg-amber-500/10', glow: 'shadow-amber-500/20' };
    return { text: 'text-rose-400', border: 'border-rose-500/30', bg: 'bg-rose-500/10', glow: 'shadow-rose-500/20' };
  };

  const probStyle = getProbColor(prob);

  // 特征状态映射标签：微光玻璃拟态，微渐变发光
  const renderStatusTag = (status: string, rowKey: string) => {
    const hasAnnotation = !!localAnnotations[rowKey];
    if (hasAnnotation) {
      return (
        <span 
          id={`badge-${rowKey}`}
          className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-300 border border-cyan-500/40 backdrop-blur-sm shadow-[0_0_8px_rgba(6,182,212,0.25)] whitespace-nowrap"
        >
          [专家修正]
        </span>
      );
    }
    switch (status) {
      case 'Fully_Disclosed':
        return (
          <span 
            id={`badge-${rowKey}`}
            className={`px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-300 border border-rose-500/30 backdrop-blur-sm shadow-[0_0_8px_rgba(244,63,94,0.15)] whitespace-nowrap ${
              step === 'PAUSED' ? 'pulse-glow-active' : ''
            }`}
          >
            完全公开 (Conflict)
          </span>
        );
      case 'Partially_Disclosed':
        return (
          <span 
            id={`badge-${rowKey}`}
            className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30 backdrop-blur-sm shadow-[0_0_8px_rgba(245,158,11,0.15)] whitespace-nowrap"
          >
            部分公开
          </span>
        );
      default:
        return (
          <span 
            id={`badge-${rowKey}`}
            className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 backdrop-blur-sm shadow-[0_0_8px_rgba(16,185,129,0.15)] whitespace-nowrap"
          >
            未公开 (Unique)
          </span>
        );
    }
  };

  // 提取当前活动的特征 ID（最新辩论提及）
  const getActiveFeatureId = () => {
    if (step !== 'THINKING' && step !== 'PAUSED') return null;
    for (let i = debateLogs.length - 1; i >= 0; i--) {
      const match = debateLogs[i].match(/DF_(\d+)/);
      if (match) {
        return `DF_${match[1]}`;
      }
    }
    return null;
  };

  const activeFeatureId = getActiveFeatureId();

  // 解析辩论日志，获取发言角色、模型标签和内容正文
  const parseDebateLog = (log: string) => {
    let role = "系统/专家";
    let model = "";
    let content = log;
    let isSystem = true;

    // 提取模型标签，如 [MOCK xxx] 或 [epo_examiner (xxx)]
    const modelRegex = /\[(?:MOCK\s+)?([a-zA-Z0-9.\-_]+)(?:\s+\([^)]+\))?\]|\[[a-zA-Z0-9.\-_]+\s+\(([^)]+)\)\]/;
    const modelMatch = log.match(modelRegex);
    if (modelMatch) {
      model = modelMatch[1] || modelMatch[2];
    }

    // 判定发言角色
    if (log.includes("法官")) {
      role = "法官 Agent";
      isSystem = false;
    } else if (log.includes("审查员") || log.includes("examiner")) {
      role = "新颖性审查员";
      isSystem = false;
    } else if (log.includes("申请人") || log.includes("applicant")) {
      role = "申请人代理";
      isSystem = false;
    } else if (log.includes("专家") || log.includes("expert")) {
      role = "人类专家";
      isSystem = false;
      model = "Expert";
    }

    // 清除中括号包围的物理标签内容
    let cleanContent = log.replace(/\[[^\]]+\]\s*/g, '');

    // 提取真实发言文本
    const colonIndex = Math.max(
      cleanContent.indexOf("判定："),
      cleanContent.indexOf("判定:"),
      cleanContent.indexOf("发言："),
      cleanContent.indexOf("发言:"),
      cleanContent.indexOf("意见："),
      cleanContent.indexOf("意见:"),
      cleanContent.indexOf("裁定："),
      cleanContent.indexOf("裁定:"),
      cleanContent.indexOf("："),
      cleanContent.indexOf(":")
    );

    if (colonIndex !== -1) {
      let offset = 1;
      if (cleanContent.indexOf("判定：") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("判定:") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("发言：") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("发言:") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("意见：") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("意见:") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("裁定：") === colonIndex) offset = 3;
      else if (cleanContent.indexOf("裁定:") === colonIndex) offset = 3;

      const candidateContent = cleanContent.slice(colonIndex + offset).trim();
      if (candidateContent.length > 0) {
        content = candidateContent;
      } else {
        content = cleanContent.trim();
      }
    } else {
      content = cleanContent.trim();
    }

    // 系统通知/大纲性日志归类
    if (log.includes("启动评估议程") || log.includes("唤醒决策流") || log.includes("遵从专家决策更新了")) {
      isSystem = true;
      role = "系统通知";
      content = log.replace(/\[[^\]]+\]\s*/g, '').trim();
    }

    return { role, model, content, isSystem };
  };

  return (
    <div className="space-y-8 py-2">
      {/* 头部标题与重置 */}
      <div className={`flex flex-col sm:flex-row justify-between items-start sm:items-center border-b border-slate-200 pb-5 gap-4 transition-all duration-500 ${
        step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
      }`}>
        <div>
          <h2 className="text-2xl font-bold text-slate-850 font-outfit flex items-center gap-2">
            <Shield className="w-6 h-6 text-blue-400" />
            PatentX 专利新颖性诊断看板
          </h2>
          <p className="text-slate-600 text-sm mt-1">评估流水号: <span className="text-slate-700 font-mono">{evalId || 'N/A'}</span></p>
        </div>
        <button
          onClick={resetAnalysis}
          className="flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-700 hover:text-slate-850 rounded-xl hover:bg-slate-200 transition-all border border-slate-200 active:scale-95 text-sm font-semibold"
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
          {showReasoningTimeline ? '收起推理过程' : '查看推理过程'}
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
              <div className="border border-slate-200 rounded-2xl p-4 bg-slate-50/50 max-h-[500px] overflow-y-auto">
                <AgenticTimeline readOnly />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* 核心结论及通过概率 */}
      <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 transition-all duration-500 ${
        step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
      }`}>
        <div className={`col-span-1 rounded-2xl border p-6 flex flex-col justify-center items-center text-center shadow-lg ${probStyle.border} ${probStyle.bg} ${probStyle.glow} transition-all duration-500`}>
          <span className="text-slate-600 text-xs font-semibold uppercase tracking-wider mb-2">授权预估概率</span>
          <span className={`text-5xl font-extrabold font-outfit ${probStyle.text}`}>
            {(prob * 100).toFixed(1)}%
          </span>
          <div className="mt-4 w-full bg-slate-950/40 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-1000 ${
                prob >= 0.8 ? 'bg-emerald-500' : prob >= 0.5 ? 'bg-amber-500' : 'bg-rose-500'
              }`}
              style={{ width: `${prob * 100}%` }}
            />
          </div>
        </div>

        <div className="col-span-1 md:col-span-2 rounded-2xl border border-slate-200 bg-slate-900/30 p-6 flex flex-col justify-between">
          <div>
            <span className="text-slate-600 text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 mb-2">
              <Award className="w-4 h-4 text-amber-400" />
              裁决意见卡片
            </span>
            <p className="text-slate-800 text-sm leading-relaxed font-medium">
              {conclusion}
            </p>
          </div>
          <div className="border-t border-slate-200 pt-3 mt-4 text-xs text-slate-500 flex justify-between">
            <span>分析引擎：PatentX Nested-Multi-Agent v2.0</span>
            <span>合规审查：欧洲专利公约 (EPC) 标准</span>
          </div>
        </div>
      </div>

      {/* 左右分栏布局 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* 左侧：多智能体嵌套辩论日志面板 */}
        <div className={`lg:col-span-1 space-y-4 flex flex-col transition-all duration-500 ${
          step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
        }`}>
          <h3 className="text-lg font-bold text-slate-850 font-outfit flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-cyan-400" />
            多智能体嵌套辩论日志
          </h3>
          
          <div 
            ref={scrollRef}
            className="flex-1 rounded-2xl border border-slate-200 bg-white/90 p-4 space-y-4 max-h-[550px] overflow-y-auto custom-scrollbar shadow-inner"
          >
            {debateLogs.length === 0 ? (
              <div className="text-slate-500 text-xs text-center py-8">暂无辩论日志</div>
            ) : (
              debateLogs.map((log: string, idx: number) => {
                const { role, model, content, isSystem } = parseDebateLog(log);
                const hasActiveFeature = activeFeatureId ? log.includes(activeFeatureId) : false;
                const isDimmed = activeFeatureId && !hasActiveFeature;
                
                if (isSystem) {
                  return (
                    <motion.div 
                      key={idx} 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: isDimmed ? 0.35 : 1, y: 0 }}
                      transition={{ duration: 0.25 }}
                      className="text-center py-2 px-3 rounded-xl bg-slate-900/30 border border-slate-200 text-slate-500 text-[11px] font-mono leading-relaxed"
                    >
                      {content}
                    </motion.div>
                  );
                }

                // 分配身份配色与样式
                let bubbleColor = "bg-slate-50/50 border-slate-200 text-slate-800";
                let avatarColor = "bg-slate-800 text-slate-700 border-slate-700";
                
                if (role === "法官 Agent") {
                  bubbleColor = "bg-purple-500/5 border-purple-500/20 text-purple-800";
                  avatarColor = "bg-purple-500/20 text-purple-300 border-purple-500/30";
                } else if (role === "新颖性审查员") {
                  bubbleColor = "bg-amber-500/5 border-amber-500/20 text-amber-800";
                  avatarColor = "bg-amber-500/20 text-amber-300 border-amber-500/30";
                } else if (role === "申请人代理") {
                  bubbleColor = "bg-blue-500/5 border-blue-500/20 text-blue-800";
                  avatarColor = "bg-blue-500/20 text-blue-300 border-blue-500/30";
                } else if (role === "人类专家") {
                  bubbleColor = "bg-emerald-500/5 border-emerald-500/20 text-emerald-800";
                  avatarColor = "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
                }

                const activeStyle = hasActiveFeature 
                  ? "shadow-[0_0_15px_rgba(56,189,248,0.2)] border-blue-500/40 bg-blue-950/20 scale-[1.01]" 
                  : "";

                return (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: isDimmed ? 0.35 : 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`flex items-start gap-3 p-3.5 rounded-2xl border transition-all duration-300 ${bubbleColor} ${activeStyle}`}
                  >
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border shrink-0 ${avatarColor}`}>
                      {role.charAt(0)}
                    </div>
                    <div className="flex-1 space-y-1.5 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold text-slate-700">{role}</span>
                        {model && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-950/60 text-slate-600 font-mono border border-slate-200">
                            {model}
                          </span>
                        )}
                      </div>
                      <p className="text-xs leading-relaxed text-slate-800 break-words">{content}</p>
                    </div>
                  </motion.div>
                );
              })
            )}
          </div>
        </div>

        {/* 右侧：特征比对映射矩阵与对比文献列表 */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* 对比文献列表部分 */}
          {patents.length > 0 && (
            <div className={`space-y-4 transition-all duration-500 ${
              step === 'PAUSED' ? 'opacity-30 blur-[0.5px] pointer-events-none' : ''
            }`}>
              <h3 className="text-lg font-bold text-slate-850 font-outfit flex items-center gap-2">
                <Layers className="w-5 h-5 text-blue-400" />
                检索召回现有技术 ({patents.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {patents.map((pat: any) => (
                  <div key={pat.id} className="rounded-xl border border-slate-700/40 bg-slate-950/20 p-4 hover:border-slate-600 transition-colors duration-300">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-blue-400 font-mono text-sm font-bold">{pat.id}</span>
                      <span className="text-slate-500 text-xs font-mono">{pat.patent_family}</span>
                    </div>
                    <h4 className="text-slate-850 text-sm font-bold line-clamp-1 mb-2">{pat.title}</h4>
                    <p className="text-slate-600 text-xs line-clamp-2 leading-relaxed">
                      <strong className="text-slate-700">独立权利要求 1: </strong> {pat.claim_1}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 特征比对矩阵 */}
          {Object.keys(matrices).length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-slate-850 font-outfit flex items-center gap-2">
                <Layers className="w-5 h-5 text-purple-400" />
                特征对齐决策矩阵
              </h3>
              <div className="space-y-6">
                {Object.entries(matrices).map(([priorId, alignments]) => (
                  <div key={priorId} className="rounded-xl border border-slate-200 bg-white/90 border border-slate-200 overflow-hidden shadow-[0_4px_20px_rgba(0,0,0,0.02)]">
                    <div className="bg-slate-50/90 px-4 py-3 border-b border-slate-150 flex justify-between items-center">
                      <span className="text-sm font-bold text-slate-800">对比文献：<span className="text-blue-400 font-mono">{priorId}</span></span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-100/55 text-slate-600 font-semibold border-b border-slate-200">
                            <th className="px-4 py-3 w-1/4">国内申请特征</th>
                            <th className="px-4 py-3 w-1/4">对比特征 ({priorId})</th>
                            <th className="px-4 py-3 w-12 text-center">状态</th>
                            <th className="px-4 py-3 w-1/3">分析说明</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200">
                          {(alignments as any[]).map((item, index) => {
                            const featureId = item.domestic_feature_id || `DF_${index}`;
                            const rowKey = `${featureId}_${priorId}_${item.prior_art_feature_id}`;
                            const isPaused = step === 'PAUSED';
                            const hasAnnotation = !!localAnnotations[rowKey];
                            const isConflict = item.status === 'Fully_Disclosed';
                            const isEditing = editingKey === rowKey;
                            const isHighlighted = isConflict || isEditing || (isPaused && hasAnnotation);

                            const isRowActive = featureId === activeFeatureId;

                            let trClass = "transition-all duration-500 border-b border-slate-200 ";
                            if (isPaused) {
                              if (isHighlighted) {
                                trClass += "opacity-100 scale-[1.005] z-10 shadow-[0_0_15px_rgba(244,63,94,0.15)] cursor-pointer ";
                                if (isConflict) {
                                  trClass += "bg-rose-50/80 border-y border-rose-200 ";
                                } else {
                                  trClass += "bg-cyan-50/80 border-y border-cyan-200 ";
                                }
                              } else {
                                trClass += "opacity-30 blur-[0.5px] pointer-events-none ";
                              }
                            } else {
                              if (isRowActive) {
                                trClass += "bg-blue-50/80 border-y border-blue-200 shadow-[inset_0_0_12px_rgba(56,189,248,0.1)] relative z-10 scale-[1.01] ";
                              } else if (activeFeatureId && !isRowActive) {
                                trClass += "opacity-35 blur-[0.3px] ";
                              } else {
                                trClass += "hover:bg-slate-50 ";
                              }
                            }

                            const handleRowClick = () => {
                              if (!isPaused) return;
                              if (isHighlighted) {
                                if (editingKey === rowKey) {
                                  setEditingKey(null);
                                } else {
                                  setEditingKey(rowKey);
                                  setTempAnnotation(localAnnotations[rowKey] || '');
                                }
                              }
                            };

                            return (
                              <React.Fragment key={rowKey}>
                                <tr 
                                  className={trClass}
                                  onClick={handleRowClick}
                                >
                                  <td className="px-4 py-3 text-slate-650 align-top leading-relaxed relative">
                                    {isRowActive && (
                                      <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-gradient-to-b from-blue-400 to-indigo-400" />
                                    )}
                                    <div className="flex flex-col gap-1.5">
                                      <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono w-fit">
                                        {featureId}
                                      </span>
                                      <span className="text-slate-800">{item.domestic_feature}</span>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3 text-slate-600 align-top leading-relaxed font-mono">
                                    <span className="text-slate-500 font-bold block mb-1 text-[10px]">{item.prior_art_feature_id}</span>
                                    {item.prior_art_feature_text}
                                  </td>
                                  <td className="px-4 py-3 text-center align-top whitespace-nowrap">
                                    {renderStatusTag(item.status, rowKey)}
                                  </td>
                                  <td className="px-4 py-3 text-slate-700 align-top leading-relaxed bg-slate-50/30">{item.explanation}</td>
                                </tr>
                                {editingKey === rowKey && (
                                  <tr className="bg-slate-50/50 border-b border-slate-200" onClick={(e) => e.stopPropagation()}>
                                    <td colSpan={4} className="px-4 py-3">
                                      <div className="flex flex-col space-y-3 bg-slate-950/40 p-4 rounded-xl border border-slate-200">
                                        <textarea
                                          className="w-full bg-white border border-slate-200 text-slate-850 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500 transition resize-none placeholder-slate-500"
                                          rows={2}
                                          placeholder="请输入对此冲突特征的专家修正意见..."
                                          value={tempAnnotation}
                                          onChange={(e) => setTempAnnotation(e.target.value)}
                                        />
                                        <div className="flex justify-end space-x-2">
                                          <button
                                            onClick={() => setEditingKey(null)}
                                            className="px-3 py-1.5 bg-slate-800 text-slate-700 text-xs font-semibold rounded-lg hover:bg-slate-200 transition-all border border-slate-200"
                                          >
                                            取消
                                          </button>
                                          <button
                                            id={`save-btn-${rowKey}`}
                                            onClick={(e) => handleSaveAnnotation(rowKey, tempAnnotation, e.currentTarget)}
                                            className="px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-blue-500 text-slate-950 text-xs font-bold rounded-lg hover:from-cyan-600 hover:to-blue-600 transition-all shadow-md shadow-cyan-500/20"
                                          >
                                            确认修改 (Save)
                                          </button>
                                        </div>
                                      </div>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 渲染粒子动画 */}
      {particles.map(p => (
        <motion.div
          key={p.id}
          initial={{ x: p.startX, y: p.startY, scale: 1, opacity: 1 }}
          animate={{
            x: p.endX,
            y: [p.startY, Math.min(p.startY, p.endY) - 120, p.endY],
            scale: [1, 1.2, 0.8],
            opacity: [1, 1, 0]
          }}
          transition={{
            duration: 0.8,
            ease: "easeOut"
          }}
          onAnimationComplete={p.onComplete}
          className="fixed top-0 left-0 w-3 h-3 bg-cyan-400 rounded-full shadow-[0_0_10px_#22d3ee] z-50 pointer-events-none"
        />
      ))}
      
      {/* 呼吸发光动画样式样式注入 */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 0 4px rgba(244, 63, 94, 0.4);
            border-color: rgba(244, 63, 94, 0.5);
          }
          50% {
            box-shadow: 0 0 16px rgba(244, 63, 94, 0.85);
            border-color: rgba(244, 63, 94, 0.85);
          }
        }
        .pulse-glow-active {
          animation: pulse-glow 2s infinite ease-in-out;
        }
      `}} />
    </div>
  );
}
