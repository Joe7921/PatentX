# patent_tools.py
# 仿真专利数据库与 Layer 2 Agent-as-Tool 评估工具 (支持 Parent-Child RAG 与特征对齐矩阵)

from typing import List, Dict, Any, Tuple


import re

class PatentDatabase:
    @staticmethod
    def recursive_retrieve(claim_text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parent-Child Recursive Retrieval 仿真:
        解析输入的国内权利要求 claim_text 中的关键词，动态生成相关的 Mock 专利数据，完全去除硬编码关联。
        """
        results = []
        
        # 提取 claim_text 中的有效词汇用于生成 mock 专利
        words = re.findall(r'\b\w+\b', claim_text)
        if len(words) < 3:
            words.extend(["system", "method", "device", "apparatus", "processing"])
            
        import hashlib
        seed = int(hashlib.md5(claim_text.encode()).hexdigest(), 16)
        
        num_patents = (seed % 2) + 2
        for i in range(num_patents):
            pid = f"EP{(seed + i) % 9000000 + 1000000}A1"
            
            sorted_words = sorted(words)
            sample_words = []
            temp_seed = seed + i
            k = min(3, len(sorted_words))
            for _ in range(k):
                if not sorted_words: break
                idx = temp_seed % len(sorted_words)
                sample_words.append(sorted_words.pop(idx))
                temp_seed //= max(1, len(sorted_words))
            
            title = f"Dynamic system for {sample_words[0]} and {sample_words[1]}" if len(sample_words) > 1 else f"Dynamic system for {sample_words[0]}"
            if len(sample_words) >= 3:
                claim_1 = f"A method involving {sample_words[0]}, comprising: processing {sample_words[1]} to generate {sample_words[2]}."
            elif len(sample_words) == 2:
                claim_1 = f"A method involving {sample_words[0]}, comprising: processing {sample_words[1]}."
            else:
                claim_1 = f"A method involving {sample_words[0]}."
            
            features = []
            for j, w in enumerate(sample_words):
                features.append({
                    "id": f"{pid}_F{j+1}",
                    "text": f"a processing unit configured for {w}",
                    "focus": f"{w} handling"
                })
                
            mock_patent = {
                "title": title,
                "patent_family": f"US{(seed + i) % 90000000 + 10000000}B2",
                "claim_1": claim_1,
                "features": features
            }
            results.append((pid, mock_patent))
            
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
    import hashlib
    seed = int(hashlib.md5(query.encode()).hexdigest(), 16)
    
    journals = ['Nature', 'Science', 'IEEE Transactions on Quantum Computing', 'ACM Computing Surveys']
    journal = journals[seed % len(journals)]
    volume = (seed % 100) + 1
    year = (seed % 26) + 2000
    
    words = re.findall(r'\b\w+\b', query)
    words = sorted([w for w in words if len(w) > 2])
    if not words:
        words = ["system", "method", "analysis", "technology"]
    
    k = min(2, len(words))
    sample_words = []
    temp_seed = seed
    for _ in range(k):
        if not words: break
        idx = temp_seed % len(words)
        sample_words.append(words.pop(idx))
        temp_seed //= max(1, len(words))
        
    title_words = " and ".join(sample_words).title() if sample_words else "Technology"
    title = f"Advances in {title_words}"
    
    msg = f"[MOCK_TRANSPORT] 找到与 '{query}' 相关的学术引文：{title} - {journal}, Vol. {volume} ({year})。"
    print(msg)
    return msg

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
