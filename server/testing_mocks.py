import json
import re
from typing import List, Dict, Any, Tuple, Optional

def mock_search_patent_db(claim_text: str) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Mock implementation extracted from patent_tools.py.
    """
    results = []
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

def mock_search_academic_db(query: str) -> str:
    """
    Mock academic literature search.
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

def mock_bigquery_retrieve(safe_query: str, focus_keywords: List[str], truncate_fn: Any) -> List[Dict[str, Any]]:
    """
    Mock bigquery retrieval logic.
    """
    raw_results = mock_search_patent_db(safe_query)
    processed_results = []
    for pid, pdata in raw_results:
        claim_text = pdata["claim_1"]
        truncated_claim = truncate_fn(claim_text, focus_keywords)
        processed_results.append({
            "id": pid,
            "title": pdata["title"],
            "patent_family": pdata["patent_family"],
            "claim_1": truncated_claim,
            "features": pdata["features"]
        })
    return processed_results

async def mock_llm_generate(messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, blackboard: Any = None) -> Dict[str, Any]:
    """
    Mock LLM fallback from llm_factory.py.
    """
    msg = "[MOCK_TRANSPORT] 检测到网络异常或熔断，当前请求已切换至本地 Mock 模板生成。"
    print(msg)
    if blackboard:
        await blackboard.add_debate_log(msg)

    # Get last user message
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = str(m.get("content", ""))
            break
    last_user_msg_truncated = (last_user_msg[:100] + "...") if len(last_user_msg) > 100 else last_user_msg

    tool_calls = None
    content_text = ""
    
    assistant_msgs = [m for m in messages if m.get("role") == "assistant" and "tool_calls" in m]
    current_round = len(assistant_msgs) + 1

    called_tools = set()
    for m in messages:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                if isinstance(tc, dict):
                    called_tools.add((tc.get("function") or {}).get("name"))
                else:
                    called_tools.add(getattr(tc, "function", None) and getattr(tc.function, "name", None))

    if tools and current_round <= 3:
        tool_calls = []
        import hashlib
        seed_str = f"{last_user_msg}_{current_round}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)
        
        available_tool_names = sorted([name for name in ((t.get("function") or {}).get("name") for t in tools) if name])
        uncalled_tools = sorted([name for name in available_tool_names if name not in called_tools])
        
        target_tools_to_call = []
        if uncalled_tools:
            num_to_pick = (seed % min(2, len(uncalled_tools))) + 1
            temp_seed = seed
            for _ in range(num_to_pick):
                if not uncalled_tools: break
                idx = temp_seed % len(uncalled_tools)
                target_tools_to_call.append(uncalled_tools.pop(idx))
                temp_seed //= max(1, len(uncalled_tools))
        else:
            target_tools_to_call.append(available_tool_names[seed % len(available_tool_names)])
            
        for func_name in target_tools_to_call:
            tool_schema = next((t for t in tools if (t.get("function") or {}).get("name") == func_name), None)
            if not tool_schema:
                continue
                
            func_obj = tool_schema.get("function") or {}
            params_obj = func_obj.get("parameters") or {}
            props = params_obj.get("properties") or {}
            
            mock_args = {}
            for k, v in props.items():
                if not isinstance(v, dict):
                    v = {}
                val_type = v.get("type", "string")
                prop_seed = int(hashlib.md5(f"{seed}_{k}".encode()).hexdigest(), 16)
                if val_type == "string":
                    if k in ["query", "claim", "domestic_feature", "feature"]:
                        words = sorted(re.findall(r'\b[A-Za-z]+\b', last_user_msg))
                        if len(words) > 3:
                            sample_k = min(5, len(words))
                            sample_words = []
                            t_seed = prop_seed
                            for _ in range(sample_k):
                                if not words: break
                                idx = t_seed % len(words)
                                sample_words.append(words.pop(idx))
                                t_seed //= max(1, len(words))
                            mock_args[k] = " ".join(sample_words)
                        else:
                            mock_args[k] = f"mock_{k}_{(prop_seed % 900) + 100}"
                    else:
                        mock_args[k] = f"mock_{k}_{(prop_seed % 900) + 100}"
                elif val_type in ("integer", "number"):
                    mock_args[k] = (prop_seed % 100) + 1
                elif val_type == "boolean":
                    mock_args[k] = bool(prop_seed % 2)
                elif val_type == "object":
                    mock_args[k] = {"mock_key": "mock_val"}
                elif val_type == "array":
                    mock_args[k] = ["mock_item"]
                else:
                    mock_args[k] = f"mock_{val_type}"

            tool_calls.append({
                "id": f"call_mock_{current_round}_{func_name}_{(seed % 9000) + 1000}",
                "type": "function",
                "function": {
                    "name": func_name,
                    "arguments": json.dumps(mock_args, ensure_ascii=False)
                }
            })
            
        if tool_calls:
            content_text = f"[MOCK_TRANSPORT] 正在随机调用 {len(tool_calls)} 个工具以推进工作流程 (通用 Fallback)。收到您的输入: '{last_user_msg_truncated}'"
        else:
            tool_calls = None
    else:
        content_text = "[MOCK_TRANSPORT] Fallback triggered. Returning standard error string to allow higher-level engine recovery."
        
    return {
        "content": content_text,
        "tool_calls": tool_calls
    }
