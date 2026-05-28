# patent_tools.py
# 仿真专利数据库与 Layer 2 Agent-as-Tool 评估工具 (支持 Parent-Child RAG 与特征对齐矩阵)

from typing import List, Dict, Any, Tuple


import re



def search_patent_db(query: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    检索专利库，召回嵌套的 EP 专利父块与子特征
    """
    import os
    mock_module = os.getenv("MOCK_INJECTION_MODULE")
    if mock_module:
        print("[MOCK_TRANSPORT] Using mock database search")
        import importlib
        mock = importlib.import_module(mock_module)
        return mock.mock_search_patent_db(query)
    
    # 真实实现依赖系统内的 api_adapters，这里通过新建 BigQueryAdapter 实例调用
    try:
        import sys
        # Ensure we can import from server
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
        from server.adapters.bigquery_adapter import BigQueryAdapter
        adapter = BigQueryAdapter({}) 
        results = adapter.retrieve(query)
        return [(r["id"], r) for r in results]
    except Exception as e:
        raise RuntimeError(f"Failed to query real patent database: {e}")

def search_academic_db(query: str) -> str:
    """
    学术文献检索 (非专利文献 NPL)
    """
    import os
    mock_module = os.getenv("MOCK_INJECTION_MODULE")
    if mock_module:
        print("[MOCK_TRANSPORT] Using mock database search")
        import importlib
        mock = importlib.import_module(mock_module)
        return mock.mock_search_academic_db(query)
    
    raise NotImplementedError("Academic DB search not implemented in production.")

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
    import json
    if isinstance(prior_art_feature, str):
        try:
            prior_art_feature = json.loads(prior_art_feature)
        except Exception:
            prior_art_feature = {"id": f"{prior_art_id}_F", "text": prior_art_feature, "focus": ""}
            
    if not isinstance(prior_art_feature, dict):
        prior_art_feature = {"id": f"{prior_art_id}_F", "text": str(prior_art_feature), "focus": ""}
            
    if isinstance(expert_annotations, str):
        try:
            expert_annotations = json.loads(expert_annotations)
        except Exception:
            expert_annotations = {}
            
    if not isinstance(expert_annotations, dict):
        expert_annotations = {}
        
    if not isinstance(domestic_feature, str):
        domestic_feature = str(domestic_feature)

    normalized_df_id = str(domestic_feature_id)
    normalized_pa_id = str(prior_art_id)

    annotation_key = f"{normalized_df_id}_{normalized_pa_id}_{prior_art_feature.get('id', '')}"
    
    # 默认对比逻辑 (基于轻量级 NLP 词汇重合度评估)
    default_status = "Not_Disclosed"
    default_impact = "Low"
    default_expl = "未在对比文件中发现对应披露。"
    
    import re
    def get_words(text):
        # Naive space splitting as requested
        return set(str(text).lower().split())
        
    df_words = get_words(domestic_feature)
    focus_words = set()
    if prior_art_feature.get("text"):
        focus_words.update(get_words(prior_art_feature["text"]))
    focus_kw = prior_art_feature.get("focus", "")
    if focus_kw:
        focus_words.update(get_words(focus_kw))
        
    if df_words and focus_words:
        overlap = len(df_words.intersection(focus_words))
        union = len(df_words.union(focus_words))
        similarity = overlap / union if union > 0 else 0
        if similarity > 0.3: # Threshold 0.3 as requested
            default_status = "Fully_Disclosed"
            default_impact = "High"
            default_expl = f"对比特征 '{prior_art_feature.get('text', '')}' 与国内技术特征具有较高的语义重合度 (相似度: {similarity:.2f})，判定为完全公开。"
    
    # 专家批注覆盖机制 (HITL)
    if annotation_key in expert_annotations and isinstance(expert_annotations[annotation_key], dict):
        expert_data = expert_annotations[annotation_key]
        return {
            "domestic_feature_id": normalized_df_id,
            "domestic_feature": domestic_feature,
            "prior_art_feature_id": prior_art_feature.get("id", ""),
            "prior_art_feature_text": prior_art_feature.get("text", ""),
            "status": expert_data.get("status", default_status),
            "novelty_impact": expert_data.get("novelty_impact", default_impact),
            "explanation": f"[专家修正] {expert_data.get('details', default_expl)}"
        }
        
    return {
        "domestic_feature_id": normalized_df_id,
        "domestic_feature": domestic_feature,
        "prior_art_feature_id": prior_art_feature.get("id", ""),
        "prior_art_feature_text": prior_art_feature.get("text", ""),
        "status": default_status,
        "novelty_impact": default_impact,
        "explanation": default_expl
    }
