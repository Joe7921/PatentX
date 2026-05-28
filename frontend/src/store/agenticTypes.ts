/**
 * agenticTypes.ts — Agent时间线核心类型定义
 * 包含Agent主题配色、ReAct步骤、阶段状态、投票记录等
 */

/** 特征对齐项定义 */
export interface AlignmentFeature {
  domestic_feature_id?: string;
  prior_art_feature_id?: string;
  domestic_feature?: string;
  prior_art_feature_text?: string;
  status: string;
  explanation?: string;
  [key: string]: unknown;
}

/** 检索到的专利项定义 */
export interface RetrievedPatent {
  id: string;
  patent_family?: string;
  title?: string;
  claim_1?: string;
  [key: string]: unknown;
}

/** 专家注释定义 */
export interface ExpertAnnotation {
  [key: string]: unknown;
}

export interface BlackboardState {
  eval_id: string | null;
  current_step: string;
  claim_features: string[];
  feature_alignment_matrices: Record<string, AlignmentFeature[]>;
  expert_annotations: Record<string, ExpertAnnotation>;
  debate_logs: string[];
  overall_probability: number | null;
  overall_conclusion: string | null;
  retrieved_patents: RetrievedPatent[];
}

/** Agent主题配色定义 */
export interface AgentTheme {
  id: string;           // first_examiner, second_examiner, chairman, applicant_representative, legal_examiner
  name: string;         // 显示名称(简体中文)
  color: string;        // 主题色
  bgClass: string;      // TailwindCSS 背景类
  borderClass: string;  // TailwindCSS 边框类
  textClass: string;    // TailwindCSS 文字类
  iconName: string;     // lucide-react 图标名
}

/** Agent主题映射表 */
export const AGENT_THEMES: Record<string, AgentTheme> = {
  first_examiner: {
    id: 'first_examiner',
    name: '第一审查员',
    color: '#3B82F6',
    bgClass: 'bg-blue-500/10',
    borderClass: 'border-blue-500/30',
    textClass: 'text-blue-600',
    iconName: 'Search',
  },
  second_examiner: {
    id: 'second_examiner',
    name: '第二审查员',
    color: '#F59E0B',
    bgClass: 'bg-amber-500/10',
    borderClass: 'border-amber-500/30',
    textClass: 'text-amber-600',
    iconName: 'FileSearch',
  },
  chairman: {
    id: 'chairman',
    name: '主席',
    color: '#8B5CF6',
    bgClass: 'bg-purple-500/10',
    borderClass: 'border-purple-500/30',
    textClass: 'text-purple-600',
    iconName: 'Crown',
  },
  applicant_representative: {
    id: 'applicant_representative',
    name: '申请人代表',
    color: '#06B6D4',
    bgClass: 'bg-cyan-500/10',
    borderClass: 'border-cyan-500/30',
    textClass: 'text-cyan-600',
    iconName: 'Shield',
  },
  legal_examiner: {
    id: 'legal_examiner',
    name: '法律审查员',
    color: '#F43F5E',
    bgClass: 'bg-rose-500/10',
    borderClass: 'border-rose-500/30',
    textClass: 'text-rose-600',
    iconName: 'Activity',
  },
};

/** 获取Agent主题，支持回退到默认主题 */
export function getAgentTheme(agentId: string): AgentTheme {
  return AGENT_THEMES[agentId] || {
    id: agentId,
    name: agentId,
    color: '#64748B',
    bgClass: 'bg-slate-500/10',
    borderClass: 'border-slate-500/30',
    textClass: 'text-slate-600',
    iconName: 'HelpCircle',
  };
}

/** ReAct步骤 */
export interface ReactStep {
  type: 'think' | 'act' | 'observe';
  agent: string;
  phase: number;
  round: number;
  content: string;
  tool?: string;  // act步骤的工具名
  timestamp: number;
}

/** 阶段状态 */
export interface PhaseState {
  id: number;        // 1-4
  name: string;      // 英文标识
  title: string;     // 中文标题
  status: 'pending' | 'active' | 'completed';
  agents: string[];  // 参与的agent列表
  steps: ReactStep[];  // 该阶段的ReAct步骤
  summary?: string;
}

/** 投票记录 */
export interface VoteRecord {
  agent: string;
  vote: 'Grant' | 'Reject' | 'Conditional Grant';
  reasoning: string;
  revealed: boolean;  // 是否已翻开
}

/** 动态拓扑节点 */
export interface TopologyNode {
  id: string;          // 唯一ID
  type: 'system' | 'phase' | 'agent' | 'tool'; 
  status: 'pending' | 'active' | 'completed';
  label: string;       // 展示名称
  agentId?: string;    // 关联的 Agent ID
  toolName?: string;   // 关联的 Tool 名称
  content?: string;    // 用于抽屉展开显示的详细日志内容
  parentId?: string;   // 来源父节点ID，用于画线
  timestamp: number;
}

/** 动态拓扑连线 */
export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  status: 'active' | 'completed';
}

/** Agentic时间线总状态 */
export interface AgenticTimelineState {
  phases: PhaseState[];
  votes: VoteRecord[];
  topologyNodes: TopologyNode[]; // 拓扑节点
  topologyEdges: TopologyEdge[]; // 拓扑连线
  currentPhase: number;  // 当前活跃阶段(1-4), 0表示未开始
  hitlAfterPhase?: number; // 在此阶段之后触发 HITL
  votingPhaseId?: number;  // 发生投票的阶段 ID
  legalExaminerSummoned: boolean;
  hitlActive: boolean;
  hitlReason: string;
  isCompleted: boolean;
}

/** 创建初始时间线状态 */
export function createInitialTimelineState(): AgenticTimelineState {
  return {
    phases: [],
    votes: [],
    topologyNodes: [{
      id: 'root_system',
      type: 'system',
      status: 'active',
      label: 'PatentX 决策中枢',
      timestamp: Date.now()
    }],
    topologyEdges: [],
    currentPhase: 0,
    legalExaminerSummoned: false,
    hitlActive: false,
    hitlReason: '',
    isCompleted: false,
  };
}
