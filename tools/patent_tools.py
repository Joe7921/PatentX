# patent_tools.py
# 仿真专利数据库与 Layer 2 Agent-as-Tool 评估工具 (支持 Parent-Child RAG 与特征对齐矩阵)

from typing import List, Dict, Any, Tuple

# 仿真 EPO 专利库 (Parent-Child 嵌套结构)
# 父表: Patent Details & Claims
# 子表: Features (Technical Limitations)
SIMULATED_EPO_DATABASE = {
    "EP3812049A1": {
        "title": "Distributed Status Streaming for Automated Agents",
        "patent_family": "US11029482B2, CN112938472A",
        "claim_1": "A system for orchestrating automated agents, comprising: a server interface configured to transmit analysis state changes as a text/event-stream; a pause coordinator to detect a hitl_interrupt signal and suspend execution; and a resume hook to resume stream transmission upon receiving an authentication token.",
        "features": [
            {
                "id": "EP3812049A1_F1",
                "text": "a server interface configured to transmit analysis state changes as a text/event-stream",
                "focus": "SSE流式传输"
            },
            {
                "id": "EP3812049A1_F2",
                "text": "a pause coordinator to detect a hitl_interrupt signal and suspend execution",
                "focus": "HITL中断与挂起"
            },
            {
                "id": "EP3812049A1_F3",
                "text": "a resume hook to resume stream transmission upon receiving an authentication token",
                "focus": "鉴权恢复机制"
            }
        ]
    },
    "EP4012055A2": {
        "title": "Multi-Agent Hierarchical Debate System",
        "patent_family": "US11582912B1",
        "claim_1": "A method for coordinating multiple specialized agents in a patent debate, including: routing requests through a layer-1 judge agent; delegating claim analysis to a layer-2 novelty examiner agent; and compiling local feature discrepancies into a unified dispute matrix.",
        "features": [
            {
                "id": "EP4012055A2_F1",
                "text": "routing requests through a layer-1 judge agent",
                "focus": "法官协调代理"
            },
            {
                "id": "EP4012055A2_F2",
                "text": "delegating claim analysis to a layer-2 novelty examiner agent",
                "focus": "审查员专精分析"
            },
            {
                "id": "EP4012055A2_F3",
                "text": "compiling local feature discrepancies into a unified dispute matrix",
                "focus": "特征差异矩阵合并"
            }
        ]
    }
}

class PatentDatabase:
    @staticmethod
    def recursive_retrieve(claim_text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parent-Child Recursive Retrieval 仿真:
        解析输入的国内权利要求 claim_text 中的关键词，匹配子特征，并召回整个父权利要求。
        """
        results = []
        claim_lower = claim_text.lower()
        
        # 简单关键字检索
        keywords_to_patents = {
            "流": "EP3812049A1",
            "stream": "EP3812049A1",
            "中断": "EP3812049A1",
            "pause": "EP3812049A1",
            "辩论": "EP4012055A2",
            "debate": "EP4012055A2",
            "法官": "EP4012055A2",
            "judge": "EP4012055A2",
            "矩阵": "EP4012055A2",
            "matrix": "EP4012055A2"
        }
        
        matched_ids = set()
        for kw, pid in keywords_to_patents.items():
            if kw in claim_lower:
                matched_ids.add(pid)
                
        # 兜底：如果没匹配到，默认全部拉回作为评估候选
        if not matched_ids:
            matched_ids = set(SIMULATED_EPO_DATABASE.keys())
            
        for pid in matched_ids:
            results.append((pid, SIMULATED_EPO_DATABASE[pid]))
            
        return results

def search_patent_db(query: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    检索专利库，召回嵌套的 EP 专利父块与子特征
    """
    return PatentDatabase.recursive_retrieve(query)

def search_academic_db(query: str) -> str:
    """
    Mock: 模拟学术文献检索 (非专利文献 NPL)
    """
    return f"[MOCK NPL] 找到与 '{query}' 相关的学术引文：IEEE Transactions on AI, Vol. 12 (2025)。"

def generate_feature_alignment_matrix(
    domestic_feature_id: str,
    domestic_feature: str, 
    prior_art_id: str, 
    prior_art_feature: Dict[str, Any],
    expert_annotations: Dict[str, Any]
) -> Dict[str, Any]:
    """
    模拟 L2 epo_examiner 对特征进行逐案对齐比对，并引入专家批注覆盖。
    """
    annotation_key = f"{domestic_feature_id}_{prior_art_id}_{prior_art_feature['id']}"
    
    # 默认对比逻辑 (基于文本包含或语义猜测)
    default_status = "Not_Disclosed"
    default_impact = "Low"
    default_expl = "未在对比文件中发现对应披露。"
    
    focus_kw = prior_art_feature.get("focus", "").lower()
    df_lower = domestic_feature.lower()
    
    if focus_kw in df_lower or any(word in df_lower for word in focus_kw.split(" ")):
        default_status = "Fully_Disclosed"
        default_impact = "High"
        default_expl = f"对比特征 '{prior_art_feature['text']}' 完全公开了该国内技术特征。"
    
    # 专家批注覆盖机制 (HITL)
    if annotation_key in expert_annotations:
        expert_data = expert_annotations[annotation_key]
        return {
            "domestic_feature_id": domestic_feature_id,
            "domestic_feature": domestic_feature,
            "prior_art_feature_id": prior_art_feature["id"],
            "prior_art_feature_text": prior_art_feature["text"],
            "status": expert_data.get("status", default_status),
            "novelty_impact": expert_data.get("novelty_impact", default_impact),
            "explanation": f"[专家修正] {expert_data.get('details', default_expl)}"
        }
        
    return {
        "domestic_feature_id": domestic_feature_id,
        "domestic_feature": domestic_feature,
        "prior_art_feature_id": prior_art_feature["id"],
        "prior_art_feature_text": prior_art_feature["text"],
        "status": default_status,
        "novelty_impact": default_impact,
        "explanation": default_expl
    }
