import { create } from './zustand';
import type {
  AgenticTimelineState,
  ReactStep,
  PhaseState,
  VoteRecord,
} from './agenticTypes';
import { createInitialTimelineState } from './agenticTypes';

export type Step = 'UPLOAD' | 'THINKING' | 'PAUSED' | 'DASHBOARD';

export interface BlackboardState {
  eval_id: string | null;
  current_step: string;
  claim_features: string[];
  feature_alignment_matrices: Record<string, any[]>;
  expert_annotations: Record<string, any>;
  debate_logs: string[];
  overall_probability: number | null;
  overall_conclusion: string | null;
  retrieved_patents: any[];
}

interface StoreState {
  // 状态变量
  step: Step;
  evalId: string | null;
  claim: string;
  currentAction: string;
  blackboard: BlackboardState | null;
  isConnected: boolean;
  error: string | null;
  reconnectCount: number;

  // 时间线状态
  agenticState: AgenticTimelineState;
  // 仪表盘中是否展开推理时间线
  showReasoningTimeline: boolean;

  // 动作函数
  setStep: (step: Step) => void;
  setClaim: (claim: string) => void;
  startAnalysis: (claim: string) => void;
  resumeAnalysis: (action: 'Approve' | 'Revise', details: string) => Promise<boolean>;
  resetAnalysis: () => void;
  disconnect: () => void;
  toggleReasoningTimeline: () => void;
}

let eventSource: EventSource | null = null;
let reconnectTimer: any = null;

// 获取真实的后端 API 地址，实现动态跨域直连，彻底杜绝本地 502 代理阻断
const getApiUrl = (path: string) => {
  const host = window.location.hostname || 'localhost';
  return `http://${host}:8000${path}`;
};

export const useStore = create<StoreState>()((set, get) => {
  const connectSSE = (claimText: string) => {
    if (eventSource) {
      eventSource.close();
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }

    const url = getApiUrl(`/api/v1/analyze/stream?claim=${encodeURIComponent(claimText)}`);
    const es = new EventSource(url);
    eventSource = es;

    es.onopen = () => {
      set({ isConnected: true, error: null, reconnectCount: 0 });
      console.log('SSE connection established');
    };

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`SSE Event received [${event.type}]:`, data);

        if (data.state) {
          set({ blackboard: data.state });
        }

        if (event.type === 'node_start') {
          set({
            step: 'THINKING',
            currentAction: data.message || 'Processing...',
            evalId: data.state?.eval_id || get().evalId,
          });
        } else if (event.type === 'node_complete') {
          set({
            currentAction: data.message || 'Node complete',
          });
        } else if (event.type === 'hitl_interrupt') {
          // 同时更新主状态机和时间线的HITL状态
          // 后端发送: {id, reason, phase}，优先使用 reason 字段
          const agSt = get().agenticState;
          set({
            step: 'PAUSED',
            evalId: data.id,
            currentAction: data.reason || data.message || 'Human intervention required',
            agenticState: {
              ...agSt,
              hitlActive: true,
              hitlReason: data.reason || data.message || '智能体评估遭遇争议，需要人类专家介入决策。',
            },
          });
        } else if (event.type === 'completed') {
          const agSt = get().agenticState;
          set({
            step: 'DASHBOARD',
            currentAction: 'Evaluation Completed',
            agenticState: { ...agSt, isCompleted: true },
          });
          es.close();
          eventSource = null;
        } else if (event.type === 'error') {
          set({ error: data.message || 'Unknown stream error' });
        }
      } catch (err) {
        console.error('Failed to parse SSE event data:', err);
      }
    };

    /** 处理时间线相关SSE事件 */
    const handleTimelineEvent = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        console.log(`SSE Timeline Event [${event.type}]:`, data);
        const agSt = get().agenticState;

        if (event.type === 'phase_start') {
          // 更新phases数组，设置当前阶段为active
          // 后端发送的字段名是 phase，不是 phase_id
          const phaseId = data.phase as number;
          const updatedPhases = agSt.phases.map((p: PhaseState) => {
            if (p.id === phaseId) {
              return {
                ...p,
                status: 'active' as const,
                name: data.name || p.name,
                title: data.title || p.title,
                agents: data.agents || p.agents,
              };
            }
            return p;
          });
          set({
            agenticState: {
              ...agSt,
              phases: updatedPhases,
              currentPhase: phaseId,
            },
          });
        } else if (event.type === 'agent_think' || event.type === 'agent_act' || event.type === 'agent_observe') {
          // 向当前阶段添加步骤
          const stepType = event.type === 'agent_think' ? 'think'
            : event.type === 'agent_act' ? 'act' : 'observe';
          const newStep: ReactStep = {
            type: stepType,
            agent: data.agent || 'unknown',
            phase: agSt.currentPhase,
            round: data.round || 1,
            content: data.content || data.message || '',
            tool: data.tool,
            timestamp: Date.now(),
          };
          const updatedPhases = agSt.phases.map((p: PhaseState) => {
            if (p.id === agSt.currentPhase) {
              return { ...p, steps: [...p.steps, newStep] };
            }
            return p;
          });
          set({ agenticState: { ...agSt, phases: updatedPhases } });
        } else if (event.type === 'phase_complete') {
          // 设置当前阶段为completed
          // 后端发送的字段名是 phase，不是 phase_id
          const phaseId = data.phase as number;
          const updatedPhases = agSt.phases.map((p: PhaseState) => {
            if (p.id === phaseId) {
              return {
                ...p,
                status: 'completed' as const,
                summary: data.summary || p.summary,
              };
            }
            return p;
          });
          set({ agenticState: { ...agSt, phases: updatedPhases } });
        } else if (event.type === 'vote_cast') {
          // 添加投票记录
          const newVote: VoteRecord = {
            agent: data.agent || 'unknown',
            vote: data.vote || 'Grant',
            reasoning: data.reasoning || '',
            revealed: false,
          };
          set({
            agenticState: {
              ...agSt,
              votes: [...agSt.votes, newVote],
            },
          });
        } else if (event.type === 'agent_summon') {
          // 法律审查员被召唤
          set({
            agenticState: {
              ...agSt,
              legalExaminerSummoned: true,
            },
          });
        }
      } catch (err) {
        console.error('Failed to parse timeline SSE event:', err);
      }
    };

    // 注册原有事件监听
    es.addEventListener('node_start', handleMessage);
    es.addEventListener('node_complete', handleMessage);
    es.addEventListener('hitl_interrupt', handleMessage);
    es.addEventListener('completed', handleMessage);
    es.addEventListener('error', handleMessage);

    // 注册时间线新事件监听
    es.addEventListener('phase_start', handleTimelineEvent);
    es.addEventListener('agent_think', handleTimelineEvent);
    es.addEventListener('agent_act', handleTimelineEvent);
    es.addEventListener('agent_observe', handleTimelineEvent);
    es.addEventListener('phase_complete', handleTimelineEvent);
    es.addEventListener('vote_cast', handleTimelineEvent);
    es.addEventListener('agent_summon', handleTimelineEvent);

    es.onerror = (err) => {
      console.error('SSE connection error:', err);
      set({ isConnected: false });
      es.close();
      eventSource = null;

      // 如果当前不是 UPLOAD，也不是已完成的 DASHBOARD，我们执行退避重连
      const currentStep = get().step;
      if (currentStep === 'THINKING' || currentStep === 'PAUSED') {
        const count = get().reconnectCount;
        const delay = Math.min(1000 * Math.pow(2, count), 10000);
        console.log(`Attempting to reconnect SSE in ${delay}ms (attempt ${count + 1})...`);
        set({ reconnectCount: count + 1, error: '连接断开，正在尝试自动重连...' });
        
        reconnectTimer = setTimeout(() => {
          connectSSE(claimText);
        }, delay);
      }
    };
  };

  return {
    step: 'UPLOAD',
    evalId: null,
    claim: '',
    currentAction: 'Initializing...',
    blackboard: null,
    isConnected: false,
    error: null,
    reconnectCount: 0,

    // 时间线初始状态
    agenticState: createInitialTimelineState(),
    showReasoningTimeline: false,

    setStep: (step: Step) => set({ step }),
    setClaim: (claim: string) => set({ claim }),

    startAnalysis: (claimText: string) => {
      set({
        claim: claimText,
        step: 'THINKING',
        evalId: null,
        blackboard: null,
        currentAction: 'Starting analysis...',
        error: null,
        reconnectCount: 0,
        agenticState: createInitialTimelineState(),
        showReasoningTimeline: false,
      });
      connectSSE(claimText);
    },

    resumeAnalysis: async (action: 'Approve' | 'Revise', details: string) => {
      const evalId = get().evalId;
      if (!evalId) {
        console.error('No evaluation ID found to resume');
        return false;
      }
      try {
        const response = await fetch(getApiUrl(`/api/v1/evaluation/${evalId}/resume`), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ action, details }),
        });

        if (response.ok) {
          // 恢复后关闭HITL状态
          const agSt = get().agenticState;
          set({
            step: 'THINKING',
            error: null,
            agenticState: { ...agSt, hitlActive: false },
          });
          return true;
        } else {
          const errData = await response.json();
          set({ error: errData.detail || 'Resume request failed' });
          return false;
        }
      } catch (err: any) {
        console.error('Error during resume request:', err);
        set({ error: err.message || 'Failed to send resume request' });
        return false;
      }
    },

    resetAnalysis: () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      set({
        step: 'UPLOAD',
        evalId: null,
        claim: '',
        currentAction: 'Initializing...',
        blackboard: null,
        isConnected: false,
        error: null,
        reconnectCount: 0,
        agenticState: createInitialTimelineState(),
        showReasoningTimeline: false,
      });
    },

    disconnect: () => {
      if (eventSource) {
        eventSource.close();
        eventSource = null;
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
      set({ isConnected: false });
    },

    toggleReasoningTimeline: () => {
      set({ showReasoningTimeline: !get().showReasoningTimeline });
    },
  };
});

