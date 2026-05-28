import { create } from './zustand';
import type {
  AgenticTimelineState,
  ReactStep,
  PhaseState,
  VoteRecord,
  BlackboardState,
} from './agenticTypes';
import { createInitialTimelineState } from './agenticTypes';

export type Step = 'UPLOAD' | 'THINKING' | 'PAUSED' | 'DASHBOARD';

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
  interruptAnalysis: (message: string) => Promise<boolean>;
  resetAnalysis: () => void;
  disconnect: () => void;
  toggleReasoningTimeline: () => void;
}

let eventSource: EventSource | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

// 获取真实的后端 API 地址，实现动态跨域直连，彻底杜绝本地 502 代理阻断
const getApiUrl = (path: string) => {
  const host = window.location.hostname || 'localhost';
  return `http://${host}:8000${path}`;
};

const createHandleMessage = (set: (partial: Partial<StoreState> | ((state: StoreState) => Partial<StoreState>)) => void, get: () => StoreState, es: EventSource) => (event: MessageEvent) => {
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
  } catch (err: unknown) {
    console.error('Failed to parse SSE event data:', err);
    set({ error: '解析事件数据失败' });
  }
};

const createHandleTimelineEvent = (set: (partial: Partial<StoreState> | ((state: StoreState) => Partial<StoreState>)) => void, get: () => StoreState) => (event: MessageEvent) => {
  try {
    const data = JSON.parse(event.data);
    console.log(`SSE Timeline Event [${event.type}]:`, data);
    const agSt = get().agenticState;

    if (event.type === 'workflow_init') {
      const initPhases = (data.phases || []).map((p: any) => ({
        ...p,
        status: p.status || 'pending',
        steps: p.steps || [],
      }));
      set({
        agenticState: {
          ...agSt,
          phases: initPhases,
          hitlAfterPhase: data.hitlAfterPhase ?? data.hitl_after_phase,
          votingPhaseId: data.votingPhaseId ?? data.voting_phase_id,
        },
      });
    } else if (event.type === 'phase_start') {
      const phaseId = data.phase as number;
      let phaseExists = false;
      const updatedPhases = agSt.phases.map((p: PhaseState) => {
        if (p.id === phaseId) {
          phaseExists = true;
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
      if (!phaseExists) {
        updatedPhases.push({
          id: phaseId,
          name: data.name || `phase_${phaseId}`,
          title: data.title || `阶段 ${phaseId}`,
          status: 'active' as const,
          agents: data.agents || [],
          steps: [],
        });
      }

      const parentId = 'root_system';
      const nodeId = `phase_${phaseId}`;
      const newNodes = [...agSt.topologyNodes, {
         id: nodeId,
         type: 'phase' as const,
         status: 'active' as const,
         label: data.title || `Phase ${phaseId}`,
         parentId,
         timestamp: Date.now()
      }];
      const newEdges = [...agSt.topologyEdges, {
         id: `edge_${parentId}_${nodeId}`,
         source: parentId,
         target: nodeId,
         status: 'active' as const
      }];

      set({
        agenticState: {
          ...agSt,
          phases: updatedPhases,
          currentPhase: phaseId,
          topologyNodes: newNodes,
          topologyEdges: newEdges,
        },
      });
    } else if (event.type === 'agent_think' || event.type === 'agent_act' || event.type === 'agent_observe') {
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

      let newNodes = [...agSt.topologyNodes];
      let newEdges = [...agSt.topologyEdges];
      
      if (stepType === 'think') {
        const parentId = `phase_${agSt.currentPhase}`;
        const nodeId = `agent_${data.agent}_${Date.now()}`;
        newNodes.push({
          id: nodeId,
          type: 'agent',
          status: 'active',
          label: data.agent || 'Agent',
          agentId: data.agent,
          content: data.content || data.message || '',
          parentId,
          timestamp: Date.now(),
        });
        newEdges.push({
          id: `edge_${parentId}_${nodeId}`,
          source: parentId,
          target: nodeId,
          status: 'active'
        });
        newNodes = newNodes.map(n => (n.type === 'agent' && n.id !== nodeId) ? { ...n, status: 'completed' } : n);
        newEdges = newEdges.map(e => (e.id !== `edge_${parentId}_${nodeId}`) ? { ...e, status: 'completed' } : e);
      } else if (stepType === 'act') {
        const parentAgent = newNodes.slice().reverse().find(n => n.type === 'agent');
        const parentId = parentAgent ? parentAgent.id : `phase_${agSt.currentPhase}`;
        const nodeId = `tool_${data.tool || 'unknown'}_${Date.now()}`;
        newNodes.push({
          id: nodeId,
          type: 'tool',
          status: 'active',
          label: data.tool || 'Action',
          toolName: data.tool,
          content: data.content || data.message || '',
          parentId,
          timestamp: Date.now(),
        });
        newEdges.push({
          id: `edge_${parentId}_${nodeId}`,
          source: parentId,
          target: nodeId,
          status: 'active'
        });
        newNodes = newNodes.map(n => (n.type === 'tool' && n.id !== nodeId) ? { ...n, status: 'completed' } : n);
      } else if (stepType === 'observe') {
        const lastTool = newNodes.slice().reverse().find(n => n.type === 'tool');
        if (lastTool) {
           lastTool.status = 'completed';
           lastTool.content += '\n\n[Observe]\n' + (data.content || data.message || '');
        }
      }

      set({ agenticState: { ...agSt, phases: updatedPhases, topologyNodes: newNodes, topologyEdges: newEdges } });
    } else if (event.type === 'phase_complete') {
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
      set({
        agenticState: {
          ...agSt,
          legalExaminerSummoned: true,
        },
      });
    }
  } catch (err: unknown) {
    console.error('Failed to parse timeline SSE event:', err);
    set({ error: '解析时间线事件数据失败' });
  }
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

    const msgHandler = createHandleMessage(set, get, es);
    const timelineHandler = createHandleTimelineEvent(set, get);

    // 注册原有事件监听
    es.addEventListener('node_start', msgHandler);
    es.addEventListener('node_complete', msgHandler);
    es.addEventListener('hitl_interrupt', msgHandler);
    es.addEventListener('completed', msgHandler);
    es.addEventListener('error', msgHandler);

    // 注册时间线新事件监听
    es.addEventListener('workflow_init', timelineHandler);
    es.addEventListener('phase_start', timelineHandler);
    es.addEventListener('agent_think', timelineHandler);
    es.addEventListener('agent_act', timelineHandler);
    es.addEventListener('agent_observe', timelineHandler);
    es.addEventListener('phase_complete', timelineHandler);
    es.addEventListener('vote_cast', timelineHandler);
    es.addEventListener('agent_summon', timelineHandler);

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

    interruptAnalysis: async (message: string) => {
      const evalId = get().evalId;
      if (!evalId) return false;
      try {
        const response = await fetch(getApiUrl(`/api/v1/evaluation/${evalId}/interrupt`), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ comment: message }),
        });
        if (!response.ok) {
          let errData;
          try {
            errData = await response.json();
          } catch {
            errData = { detail: 'Interrupt failed' };
          }
          set({ error: errData.detail || 'Interrupt request failed' });
          return false;
        }
        return true;
      } catch (err: unknown) {
        console.error('Error during interrupt request:', err);
        set({ error: 'Failed to send interrupt request' });
        return false;
      }
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
          let errData;
          try {
            errData = await response.json();
          } catch (e) {
            errData = { detail: await response.text() };
          }
          set({ error: errData.detail || 'Resume request failed' });
          return false;
        }
      } catch (err: unknown) {
        console.error('Error during resume request:', err);
        const errorMessage = err instanceof Error ? err.message : String(err);
        set({ error: errorMessage || 'Failed to send resume request' });
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

