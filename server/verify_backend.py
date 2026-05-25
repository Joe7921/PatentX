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
                        
                        # Concurrently send POST /resume with 3D joint key expert annotations
                        print(f"Sending resume for ID: {interrupt_id}")
                        import json
                        expert_details = json.dumps({
                            "DF_0_EP4012055A2_EP4012055A2_F1": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：法官协调不构成完全公开"},
                            "DF_1_EP3812049A1_EP3812049A1_F1": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：流式传输非完全公开"},
                            "DF_1_EP3812049A1_EP3812049A1_F2": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：挂起组件非完全公开"},
                            "DF_2_EP3812049A1_EP3812049A1_F3": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：恢复机制非完全公开"}
                        })
                        asyncio.create_task(
                            action_client.post(
                                f"/api/v1/evaluation/{interrupt_id}/resume", 
                                json={"action": "continue", "details": expert_details}
                            )
                        )
                        
                    elif event_name == "completed":
                        completed_received = True
                        import json
                        data = json.loads(data_json)
                        state = data.get("state", {})
                        
                        # 1. 验证 Fallback 机制日志
                        logs = state.get("debate_logs", [])
                        fallback_verified = any("LLM 降级预警" in log for log in logs)
                        print(f"Fallback verification status: {fallback_verified}")
                        
                        # 2. 验证 Token Budget 截断痕迹
                        patents = state.get("retrieved_patents", [])
                        truncation_verified = any("已截断" in p.get("claim_1", "") for p in patents)
                        print(f"Token Budget truncation verification status: {truncation_verified}")
                        
                        # 3. 验证第二轮辩论与决策注入及概率重算
                        prob = state.get("overall_probability")
                        print(f"Recalculated probability: {prob}")
                        prob_verified = (prob == 0.95)
                        
                        round2_examiner_verified = any("审查员 (Round 2)" in log for log in logs)
                        round2_applicant_verified = any("申请人代理 (Round 2)" in log for log in logs)
                        print(f"Round 2 Examiner response verified: {round2_examiner_verified}")
                        print(f"Round 2 Applicant response verified: {round2_applicant_verified}")
                        
                        if not fallback_verified:
                            print("Assertion Failed: Fallback warning not found in logs!")
                            completed_received = False
                        if not truncation_verified:
                            print("Assertion Failed: Truncation warning not found in claims!")
                            completed_received = False
                        if not prob_verified:
                            print(f"Assertion Failed: Expected recalculated probability 0.95, got {prob}!")
                            completed_received = False
                        if not round2_examiner_verified or not round2_applicant_verified:
                            print("Assertion Failed: Round 2 debate logs missing!")
                            completed_received = False
                        
        if node_start_received and hitl_interrupt_received and completed_received:
            print("All assertions passed!")
            sys.exit(0)
        else:
            print(f"Failed. node_start={node_start_received}, hitl_interrupt={hitl_interrupt_received}, completed={completed_received}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
