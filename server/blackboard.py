import asyncio
from typing import Dict, List, Any, Optional

class Blackboard:
    """
    黑板(共享状态)管理器：
    管理4阶段EPO审查工作流中所有Agent之间的共享状态，
    包括阶段追踪、Agent状态、ReAct步骤历史、投票记录等。
    """
    def __init__(self):
        self.lock = asyncio.Lock()
        self.eval_id: Optional[str] = None
        self.claim_features: List[str] = []
        # Key: prior_art_id, Value: 对齐矩阵项列表
        self.feature_alignment_matrices: Dict[str, List[Dict[str, Any]]] = {}
        # Key: domestic_feature_index 或 prior_art_id + feature_name
        self.expert_annotations: Dict[str, Any] = {}
        self.debate_logs: List[str] = []
        self.current_step: str = "idle"
        self.overall_probability: Optional[float] = None
        self.overall_conclusion: Optional[str] = None
        self.retrieved_patents: List[Dict[str, Any]] = []

        # ====== 4阶段工作流扩展字段 ======
        # 当前阶段编号 (1-4)
        self.current_phase: int = 0
        # 当前阶段名称
        self.current_phase_name: str = ""
        # 每个Agent的状态: {"agent_name": {"status": "idle|thinking|acting|observing|voting", "last_action": "..."}}
        self.agents_state: Dict[str, Dict[str, Any]] = {}
        # ReAct步骤历史: [{"agent": "...", "phase": 1, "round": 1, "type": "think|act|observe", "content": "..."}]
        self.react_history: List[Dict[str, Any]] = []
        # 投票记录: [{"agent": "...", "vote": "Grant|Reject|Conditional Grant", "reasoning": "..."}]
        self.votes: List[Dict[str, Any]] = []
        # 是否已召唤法律审查员
        self.legal_examiner_summoned: bool = False

    async def reset(self, eval_id: str, claim_features: List[str]):
        """重置黑板所有状态到初始值"""
        async with self.lock:
            self.eval_id = eval_id
            self.claim_features = claim_features
            self.feature_alignment_matrices = {}
            self.expert_annotations = {}
            self.debate_logs = []
            self.current_step = "idle"
            self.overall_probability = None
            self.overall_conclusion = None
            self.retrieved_patents = []
            # 重置扩展字段
            self.current_phase = 0
            self.current_phase_name = ""
            self.agents_state = {}
            self.react_history = []
            self.votes = []
            self.legal_examiner_summoned = False

    async def update_matrix(self, prior_art_id: str, alignments: List[Dict[str, Any]]):
        """更新指定先有技术的特征对齐矩阵"""
        async with self.lock:
            self.feature_alignment_matrices[prior_art_id] = alignments

    async def add_expert_annotation(self, key: str, annotation: Any):
        """添加人类专家批注"""
        async with self.lock:
            self.expert_annotations[key] = annotation

    async def add_debate_log(self, log_entry: str):
        """追加辩论日志条目"""
        async with self.lock:
            self.debate_logs.append(log_entry)

    async def set_step(self, step: str):
        """设置当前工作流步骤标识"""
        async with self.lock:
            self.current_step = step

    async def set_conclusion(self, probability: float, conclusion: str):
        """设置最终裁决结论和授权概率"""
        async with self.lock:
            self.overall_probability = probability
            self.overall_conclusion = conclusion

    async def set_retrieved_patents(self, retrieved_patents: List[Dict[str, Any]]):
        """设置检索到的专利列表"""
        async with self.lock:
            self.retrieved_patents = retrieved_patents

    # ====== 4阶段工作流扩展方法 ======

    async def set_phase(self, phase: int, phase_name: str):
        """设置当前阶段编号和名称"""
        async with self.lock:
            self.current_phase = phase
            self.current_phase_name = phase_name

    async def get_phase(self) -> Dict[str, Any]:
        """获取当前阶段信息"""
        async with self.lock:
            return {
                "current_phase": self.current_phase,
                "current_phase_name": self.current_phase_name
            }

    async def set_agent_state(self, agent_name: str, status: str, last_action: str = ""):
        """设置指定Agent的当前状态"""
        async with self.lock:
            self.agents_state[agent_name] = {
                "status": status,
                "last_action": last_action
            }

    async def get_agent_state(self, agent_name: str) -> Dict[str, Any]:
        """获取指定Agent的当前状态"""
        async with self.lock:
            return self.agents_state.get(agent_name, {"status": "idle", "last_action": ""})

    async def add_react_step(self, agent: str, phase: int, round_num: int, step_type: str, content: str):
        """记录一个ReAct步骤到历史"""
        async with self.lock:
            self.react_history.append({
                "agent": agent,
                "phase": phase,
                "round": round_num,
                "type": step_type,
                "content": content
            })

    async def get_react_history(self) -> List[Dict[str, Any]]:
        """获取完整的ReAct步骤历史"""
        async with self.lock:
            return list(self.react_history)

    async def add_vote(self, agent: str, vote: str, reasoning: str):
        """记录一个Agent的投票"""
        async with self.lock:
            self.votes.append({
                "agent": agent,
                "vote": vote,
                "reasoning": reasoning
            })

    async def get_votes(self) -> List[Dict[str, Any]]:
        """获取所有投票记录"""
        async with self.lock:
            return list(self.votes)

    async def set_legal_examiner_summoned(self, summoned: bool):
        """设置是否已召唤法律审查员"""
        async with self.lock:
            self.legal_examiner_summoned = summoned

    async def is_legal_examiner_summoned(self) -> bool:
        """检查法律审查员是否已被召唤"""
        async with self.lock:
            return self.legal_examiner_summoned

    async def count_fully_disclosed(self) -> int:
        """统计特征对齐矩阵中Fully_Disclosed的数量"""
        async with self.lock:
            count = 0
            for pid, alignments in self.feature_alignment_matrices.items():
                for item in alignments:
                    if item.get("status") == "Fully_Disclosed":
                        count += 1
            return count

    async def get_state(self) -> Dict[str, Any]:
        """获取完整的黑板状态快照"""
        async with self.lock:
            return {
                "eval_id": self.eval_id,
                "current_step": self.current_step,
                "current_phase": self.current_phase,
                "current_phase_name": self.current_phase_name,
                "claim_features": self.claim_features,
                "feature_alignment_matrices": self.feature_alignment_matrices,
                "expert_annotations": self.expert_annotations,
                "debate_logs": self.debate_logs,
                "overall_probability": self.overall_probability,
                "overall_conclusion": self.overall_conclusion,
                "retrieved_patents": self.retrieved_patents,
                "agents_state": self.agents_state,
                "react_history": self.react_history,
                "votes": self.votes,
                "legal_examiner_summoned": self.legal_examiner_summoned
            }
