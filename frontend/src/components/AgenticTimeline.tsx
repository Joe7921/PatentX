/**
 * AgenticTimeline.tsx — 主时间线容器组件
 * 垂直排列阶段节点、连接器、HITL节点和投票面板
 * 自动滚动到最新活跃阶段
 */
import React, { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import PhaseNode from './timeline/PhaseNode';
import TimelineConnector from './timeline/TimelineConnector';
import HITLNode from './timeline/HITLNode';
import VotingPanel from './timeline/VotingPanel';

interface AgenticTimelineProps {
  /** 只读模式：不播放打字机动画(仪表盘中使用) */
  readOnly?: boolean;
}

/** 获取两个相邻阶段之间连接器的状态 */
function getConnectorStatus(
  prevPhaseStatus: string,
  nextPhaseStatus: string
): 'completed' | 'active' | 'pending' {
  if (prevPhaseStatus === 'completed' && nextPhaseStatus === 'completed') return 'completed';
  if (prevPhaseStatus === 'completed' || prevPhaseStatus === 'active') return 'active';
  return 'pending';
}

export default function AgenticTimeline({ readOnly }: AgenticTimelineProps) {
  const { agenticState, resumeAnalysis } = useStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const activeRef = useRef<HTMLDivElement>(null);

  // 自动滚动到最新活跃阶段
  useEffect(() => {
    if (!readOnly && activeRef.current) {
      activeRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [agenticState.currentPhase, readOnly]);

  const { phases, votes, hitlActive, hitlReason } = agenticState;

  // HITL恢复处理
  const handleHITLResume = (action: 'Approve' | 'Revise', details: string) => {
    resumeAnalysis(action, details);
  };

  // 判断HITL节点是否已解决(已经离开PAUSED状态)
  const hitlResolved = !hitlActive && hitlReason !== '';

  return (
    <div ref={containerRef} className="w-full max-w-2xl mx-auto py-4 space-y-0">
      {/* 时间线标题 */}
      <div className="text-center mb-6">
        <h2 className="text-lg font-bold text-slate-700 font-outfit">
          智能体推理时间线
        </h2>
        <p className="text-xs text-slate-500 mt-1">
          多Agent协作评估进度
        </p>
      </div>

      {/* 依次渲染阶段节点和连接器 */}
      {phases.map((phase, index) => {
        const isActive = phase.status === 'active';
        const isLastPhase = index === phases.length - 1;

        // 判断是否在此阶段后插入HITL节点(Phase 2之后)
        const showHITLAfter = index === 1 && (hitlActive || hitlResolved);

        return (
          <React.Fragment key={phase.id}>
            {/* 阶段节点 */}
            <div ref={isActive ? activeRef : undefined}>
              <PhaseNode
                phase={phase}
                isExpanded={phase.status === 'active'}
                readOnly={readOnly}
              >
                {/* Phase 4 内嵌投票面板 */}
                {phase.id === 4 && votes.length > 0 && (
                  <VotingPanel votes={votes} readOnly={readOnly} />
                )}
              </PhaseNode>
            </div>

            {/* HITL节点(Phase 2之后插入) */}
            {showHITLAfter && (
              <>
                <TimelineConnector
                  status={hitlActive ? 'active' : 'completed'}
                />
                <HITLNode
                  reason={hitlReason}
                  onResume={handleHITLResume}
                  isResolved={hitlResolved}
                  readOnly={readOnly}
                />
              </>
            )}

            {/* 阶段间连接器 */}
            {!isLastPhase && (
              <TimelineConnector
                status={getConnectorStatus(
                  phase.status,
                  phases[index + 1]?.status || 'pending'
                )}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}
