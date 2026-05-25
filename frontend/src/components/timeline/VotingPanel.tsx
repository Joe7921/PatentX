/**
 * VotingPanel.tsx — 投票面板组件
 * 水平排列投票卡片，支持3D翻转动画依次揭晓投票结果
 */
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { HelpCircle } from 'lucide-react';
import { getAgentTheme } from '../../store/agenticTypes';
import type { VoteRecord } from '../../store/agenticTypes';

interface VotingPanelProps {
  /** 投票记录列表 */
  votes: VoteRecord[];
  /** 是否只读模式 */
  readOnly?: boolean;
}

/** 获取投票结果的颜色样式 */
function getVoteColor(vote: string) {
  switch (vote) {
    case 'Grant':
      return {
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/40',
        text: 'text-emerald-600',
        label: '授权',
      };
    case 'Reject':
      return {
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/40',
        text: 'text-rose-600',
        label: '驳回',
      };
    case 'Conditional Grant':
      return {
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/40',
        text: 'text-amber-600',
        label: '有条件授权',
      };
    default:
      return {
        bg: 'bg-slate-500/10',
        border: 'border-slate-500/40',
        text: 'text-slate-600',
        label: vote,
      };
  }
}

export default function VotingPanel({ votes, readOnly }: VotingPanelProps) {
  const [revealedIndices, setRevealedIndices] = useState<Set<number>>(new Set());
  const [allRevealed, setAllRevealed] = useState(false);

  // 按间隔依次翻转投票卡片
  useEffect(() => {
    if (votes.length === 0) return;

    // 只读模式直接全部显示
    if (readOnly) {
      const allIndices = new Set(votes.map((_, i) => i));
      setRevealedIndices(allIndices);
      setAllRevealed(true);
      return;
    }

    let currentIndex = 0;
    const timer = setInterval(() => {
      if (currentIndex < votes.length) {
        setRevealedIndices(prev => {
          const next = new Set(prev);
          next.add(currentIndex);
          return next;
        });
        currentIndex++;
        if (currentIndex >= votes.length) {
          setAllRevealed(true);
          clearInterval(timer);
        }
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [votes.length, readOnly]);

  if (votes.length === 0) return null;

  // 计算最终结果(多数票)
  const voteCounts: Record<string, number> = {};
  votes.forEach(v => {
    voteCounts[v.vote] = (voteCounts[v.vote] || 0) + 1;
  });
  const finalDecision = Object.entries(voteCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || '待定';
  const finalColor = getVoteColor(finalDecision);

  return (
    <div className="mt-4 space-y-4">
      {/* 投票标题 */}
      <div className="text-center">
        <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          智能体投票环节
        </span>
      </div>

      {/* 投票卡片网格 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {votes.map((vote, index) => {
          const isRevealed = revealedIndices.has(index);
          const theme = getAgentTheme(vote.agent);
          const voteColor = getVoteColor(vote.vote);

          return (
            <div
              key={`${vote.agent}-${index}`}
              className="relative"
              style={{ perspective: '1000px' }}
            >
              <motion.div
                className="relative w-full"
                style={{
                  transformStyle: 'preserve-3d',
                }}
                animate={{
                  rotateY: isRevealed ? 180 : 0,
                }}
                transition={{ duration: 0.8, ease: 'easeInOut' }}
              >
                {/* 正面(未翻转) — "?" */}
                <div
                  className="w-full rounded-xl border-2 border-slate-300/50 bg-slate-800/90 p-4 flex flex-col items-center justify-center min-h-[100px]"
                  style={{
                    backfaceVisibility: 'hidden',
                  }}
                >
                  <HelpCircle className="w-8 h-8 text-slate-400 mb-2" />
                  <span className="text-xs text-slate-400 font-semibold">{theme.name}</span>
                </div>

                {/* 背面(翻转后) — 显示投票结果 */}
                <div
                  className={`absolute inset-0 w-full rounded-xl border-2 ${voteColor.border} ${voteColor.bg} p-4 flex flex-col items-center justify-center min-h-[100px]`}
                  style={{
                    backfaceVisibility: 'hidden',
                    transform: 'rotateY(180deg)',
                  }}
                >
                  {/* Agent标识 */}
                  <div
                    className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white mb-2"
                    style={{ backgroundColor: theme.color }}
                  >
                    {theme.name.charAt(0)}
                  </div>
                  {/* 投票结果 */}
                  <span className={`text-sm font-bold ${voteColor.text} mb-1`}>
                    {voteColor.label}
                  </span>
                  {/* 理由摘要 */}
                  <p className="text-[10px] text-slate-500 text-center line-clamp-2 leading-relaxed">
                    {vote.reasoning}
                  </p>
                </div>
              </motion.div>
            </div>
          );
        })}
      </div>

      {/* 最终决定(全部翻转后显示) */}
      {allRevealed && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className={`
            text-center py-3 px-6 rounded-xl border-2
            ${finalColor.border} ${finalColor.bg}
            shadow-[0_0_20px_rgba(234,179,8,0.2)]
          `}
        >
          <span className="text-xs text-slate-500 font-semibold">最终裁决：</span>
          <span className={`text-lg font-bold ml-2 ${finalColor.text}`}>
            {finalColor.label}
          </span>
        </motion.div>
      )}
    </div>
  );
}
