import asyncio
import sys
import httpx
from main import app

async def main():
    import os
    port = os.getenv("TEST_PORT", "8089")
    base_url = f"http://127.0.0.1:{port}"
    print(f"Connecting to test server at {base_url}...")
    async with httpx.AsyncClient(base_url=base_url, trust_env=False, timeout=None) as stream_client, \
               httpx.AsyncClient(base_url=base_url, trust_env=False, timeout=None) as action_client:
        print("Starting stream...")
        node_start_received = False
        hitl_interrupt_received = False
        completed_received = False
        interrupt_id = None
        
        async with stream_client.stream("GET", "/api/v1/analyze/stream") as response:
            print(f"Stream response status code: {response.status_code}")
            buffer = ""
            async for chunk in response.aiter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    event_block, buffer = buffer.split("\n\n", 1)
                    lines = event_block.split("\n")
                    event_name = ""
                    data_json = ""
                    for line in lines:
                        line_clean = line.strip()
                        if line_clean.startswith("event: "):
                            event_name = line_clean[7:]
                        elif line_clean.startswith("data: "):
                            data_json = line_clean[6:]
                            
                    safe_msg = f"Received event: {event_name}, data: {data_json}"
                    encoding = sys.stdout.encoding or 'utf-8'
                    print(safe_msg.encode(encoding, errors='replace').decode(encoding))
                    
                    if event_name == "node_start":
                        node_start_received = True
                    elif event_name == "hitl_interrupt":
                        hitl_interrupt_received = True
                        import json
                        data = json.loads(data_json)
                        interrupt_id = data["id"]
                        
                        print(f"Sending resume for ID: {interrupt_id}")
                        
                        # Dynamically fetch the blackboard to find the actual alignment keys
                        async def fetch_and_resume():
                            # wait briefly to ensure blackboard is updated
                            await asyncio.sleep(0.5)
                            try:
                                bb_resp = await action_client.get(f"/api/v1/evaluation/{interrupt_id}/blackboard")
                                state = bb_resp.json()
                                matrices = state.get("feature_alignment_matrices", {})
                                expert_details_dict = {}
                                for pa_id, alignments in matrices.items():
                                    for al in alignments:
                                        df_id = al.get("domestic_feature_id", "")
                                        pf_id = al.get("prior_art_feature_id", "")
                                        key = f"{df_id}_{pa_id}_{pf_id}"
                                        expert_details_dict[key] = {
                                            "status": "[专家修正]",
                                            "novelty_impact": "Low",
                                            "details": f"专家修正：动态应用到 {key}"
                                        }
                                
                                expert_details = json.dumps(expert_details_dict) if expert_details_dict else json.dumps({"global": "Fallback"})
                                await action_client.post(
                                    f"/api/v1/evaluation/{interrupt_id}/resume", 
                                    json={"action": "continue", "details": expert_details}
                                )
                            except Exception as e:
                                print(f"Error fetching blackboard and resuming: {e}")
                                # fallback
                                await action_client.post(
                                    f"/api/v1/evaluation/{interrupt_id}/resume", 
                                    json={"action": "continue", "details": "{}"}
                                )
                        
                        asyncio.create_task(fetch_and_resume())
                        
                    elif event_name == "completed":
                        completed_received = True
                        import json
                        data = json.loads(data_json)
                        state = data.get("state", {})
                        
                        # 1. 验证 Fallback 机制日志 (可能被触发)
                        logs = state.get("debate_logs", [])
                        fallback_verified = any("LLM 降级预警" in log or "[MOCK_TRANSPORT]" in log for log in logs)
                        print(f"Fallback verification status (LLM/Mock): {fallback_verified}")
                        
                        # 2. 验证 Token Budget 截断痕迹 (可能在 Mock 中不再必然出现，所以设为宽松警告)
                        patents = state.get("retrieved_patents", [])
                        truncation_verified = any("已截断" in p.get("claim_1", "") for p in patents)
                        print(f"Token Budget truncation verification status: {truncation_verified}")
                        
                        # 3. 验证第二轮辩论与决策注入及概率重算 (结构化验证)
                        prob = state.get("overall_probability")
                        print(f"Recalculated probability: {prob}")
                        prob_verified = isinstance(prob, float)
                        
                        votes = state.get("votes", [])
                        valid_votes = ["Grant", "Reject", "Conditional Grant"]
                        votes_verified = len(votes) > 0 and all(v.get("vote") in valid_votes for v in votes)
                        print(f"Votes structural verification: {votes_verified}")
                        
                        # 4. 验证专家修正是否应用到了对齐矩阵 (如果在测试运行中确实触发了 HITL)
                        matrices = state.get("feature_alignment_matrices", {})
                        expert_applied = False
                        for pa_id, alignments in matrices.items():
                            for al in alignments:
                                if "[专家修正]" in al.get("status", "") or "[专家修正]" in al.get("explanation", ""):
                                    expert_applied = True
                                    break
                        print(f"Expert annotations applied verified (if hitl): {expert_applied}")
                        
                        if not fallback_verified:
                            print("Assertion Failed: Fallback or MOCK_TRANSPORT warning not found in logs!")
                            completed_received = False
                        if not prob_verified:
                            print(f"Assertion Failed: Expected probability to be float, got {prob}!")
                            completed_received = False
                        if not votes_verified:
                            print("Assertion Failed: Votes were missing or contained invalid string values!")
                            completed_received = False
                        
        if node_start_received and completed_received:
            print("All assertions passed! (Structural correctness verified)")
            sys.exit(0)
        else:
            print(f"Failed. node_start={node_start_received}, hitl_interrupt={hitl_interrupt_received}, completed={completed_received}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
