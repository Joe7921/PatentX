import React, { useState } from 'react';
import { Layers } from 'lucide-react';
import { motion } from 'framer-motion';
import { useStore } from '../../store/useStore';
import { AlignmentFeature, RetrievedPatent } from '../../store/agenticTypes';

interface Particle {
  id: string;
  startX: number;
  startY: number;
  endX: number;
  endY: number;
  onComplete: () => void;
}

interface AlignmentMatrixProps {
  patents: RetrievedPatent[];
  matrices: Record<string, AlignmentFeature[]>;
  activeFeatureId: string | null;
}

export default function AlignmentMatrix({ patents, matrices, activeFeatureId }: AlignmentMatrixProps) {
  const { step } = useStore();
  
  const [localAnnotations, setLocalAnnotations] = useState<Record<string, string>>({});
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [tempAnnotation, setTempAnnotation] = useState<string>('');
  const [particles, setParticles] = useState<Particle[]>([]);

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

  const renderStatusTag = (status: string, rowKey: string) => {
    const hasAnnotation = !!localAnnotations[rowKey];
    if (hasAnnotation) {
      return (
        <span 
          id={`badge-${rowKey}`}
          className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-cyan-500/10 text-cyan-500 border border-cyan-500/40 backdrop-blur-sm shadow-[0_0_8px_rgba(6,182,212,0.15)] whitespace-nowrap"
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
            className={`px-2.5 py-1 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-500 border border-rose-500/30 backdrop-blur-sm shadow-[0_0_8px_rgba(244,63,94,0.05)] whitespace-nowrap ${
              step === 'PAUSED' ? 'animate-pulse ring-2 ring-rose-500/20' : ''
            }`}
          >
            完全公开 (Conflict)
          </span>
        );
      case 'Partially_Disclosed':
        return (
          <span 
            id={`badge-${rowKey}`}
            className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-600 border border-amber-500/30 backdrop-blur-sm whitespace-nowrap"
          >
            部分公开
          </span>
        );
      default:
        return (
          <span 
            id={`badge-${rowKey}`}
            className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/30 backdrop-blur-sm whitespace-nowrap"
          >
            未公开 (Unique)
          </span>
        );
    }
  };

  return (
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
            {patents.map(pat => (
              <div key={pat.id} className="rounded-xl border border-slate-200 bg-slate-50/50 p-4 hover:border-slate-300 transition-colors duration-300 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-blue-600 font-mono text-sm font-bold">{pat.id}</span>
                  <span className="text-slate-400 text-xs font-mono">{pat.patent_family}</span>
                </div>
                <h4 className="text-slate-800 text-sm font-bold line-clamp-1 mb-2">{pat.title}</h4>
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
              <div key={priorId} className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
                <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex justify-between items-center">
                  <span className="text-sm font-bold text-slate-800">对比文献：<span className="text-blue-500 font-mono">{priorId}</span></span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-white text-slate-500 font-semibold border-b border-slate-200">
                        <th className="px-4 py-3 w-1/4">国内申请特征</th>
                        <th className="px-4 py-3 w-1/4">对比特征 ({priorId})</th>
                        <th className="px-4 py-3 w-12 text-center">状态</th>
                        <th className="px-4 py-3 w-1/3">分析说明</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {alignments.map((item, index) => {
                        const featureId = item.domestic_feature_id || `DF_${index}`;
                        const rowKey = `${featureId}_${priorId}_${item.prior_art_feature_id}`;
                        const isPaused = step === 'PAUSED';
                        const hasAnnotation = !!localAnnotations[rowKey];
                        const isConflict = item.status === 'Fully_Disclosed';
                        const isEditing = editingKey === rowKey;
                        const isHighlighted = isConflict || isEditing || (isPaused && hasAnnotation);
                        const isRowActive = featureId === activeFeatureId;

                        let trClass = "transition-all duration-500 ";
                        if (isPaused) {
                          if (isHighlighted) {
                            trClass += "opacity-100 relative z-10 cursor-pointer ";
                            if (isConflict) {
                              trClass += "bg-rose-50/50 ";
                            } else {
                              trClass += "bg-cyan-50/50 ";
                            }
                          } else {
                            trClass += "opacity-30 blur-[0.5px] pointer-events-none ";
                          }
                        } else {
                          if (isRowActive) {
                            trClass += "bg-blue-50/50 relative z-10 ";
                          } else if (activeFeatureId && !isRowActive) {
                            trClass += "opacity-40 blur-[0.3px] ";
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
                            <tr className={trClass} onClick={handleRowClick}>
                              <td className="px-4 py-3 text-slate-700 align-top leading-relaxed relative">
                                {isRowActive && (
                                  <div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-400" />
                                )}
                                <div className="flex flex-col gap-1.5">
                                  <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded text-[9px] font-bold bg-blue-50 text-blue-600 border border-blue-100 font-mono w-fit">
                                    {featureId}
                                  </span>
                                  <span>{item.domestic_feature}</span>
                                </div>
                              </td>
                              <td className="px-4 py-3 text-slate-600 align-top leading-relaxed font-mono">
                                <span className="text-slate-400 font-bold block mb-1 text-[10px]">{item.prior_art_feature_id}</span>
                                {item.prior_art_feature_text}
                              </td>
                              <td className="px-4 py-3 text-center align-top whitespace-nowrap">
                                {renderStatusTag(item.status, rowKey)}
                              </td>
                              <td className="px-4 py-3 text-slate-600 align-top leading-relaxed bg-slate-50/30">
                                {item.explanation}
                              </td>
                            </tr>
                            {editingKey === rowKey && (
                              <tr className="bg-slate-50/80 border-y border-slate-200 shadow-inner" onClick={(e) => e.stopPropagation()}>
                                <td colSpan={4} className="px-4 py-4">
                                  <div className="flex flex-col space-y-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
                                    <textarea
                                      className="w-full bg-slate-50 border border-slate-200 text-slate-800 rounded-lg px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 transition resize-none placeholder-slate-400"
                                      rows={2}
                                      placeholder="请输入对此冲突特征的专家修正意见..."
                                      value={tempAnnotation}
                                      onChange={(e) => setTempAnnotation(e.target.value)}
                                    />
                                    <div className="flex justify-end space-x-2">
                                      <button
                                        onClick={() => setEditingKey(null)}
                                        className="px-3 py-1.5 bg-white text-slate-600 text-xs font-semibold rounded-lg hover:bg-slate-50 transition-all border border-slate-200 shadow-sm"
                                      >
                                        取消
                                      </button>
                                      <button
                                        id={`save-btn-${rowKey}`}
                                        onClick={(e) => handleSaveAnnotation(rowKey, tempAnnotation, e.currentTarget)}
                                        className="px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 transition-all shadow-sm"
                                      >
                                        保存批注
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

      {/* 渲染粒子动画 */}
      {particles.map(p => (
        <motion.div
          key={p.id}
          initial={{ x: p.startX, y: p.startY, scale: 1, opacity: 1 }}
          animate={{
            x: p.endX,
            y: [p.startY, Math.min(p.startY, p.endY) - 100, p.endY],
            scale: [1, 1.2, 0.8],
            opacity: [1, 1, 0]
          }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          onAnimationComplete={p.onComplete}
          className="fixed top-0 left-0 w-2.5 h-2.5 bg-blue-400 rounded-full shadow-[0_0_8px_#60a5fa] z-50 pointer-events-none"
        />
      ))}
    </div>
  );
}
