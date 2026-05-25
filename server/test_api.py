import asyncio
import httpx
from main import app
import json

async def test_successful_flow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("Testing successful flow...")
        node_start_received = False
        hitl_interrupt_received = False
        completed_received = False
        interrupt_id = None
        
        async with client.stream("GET", "/api/v1/analyze/stream") as response:
            buffer = ""
            async for chunk in response.aiter_text():
                print(f"DEBUG CHUNK: {repr(chunk)}")
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
                            
                    if event_name == "node_start":
                        node_start_received = True
                        print("  - node_start received")
                    elif event_name == "hitl_interrupt":
                        hitl_interrupt_received = True
                        data = json.loads(data_json)
                        interrupt_id = data["id"]
                        print(f"  - hitl_interrupt received, id={interrupt_id}")
                        
                        # Concurrently send POST /resume with 3D joint key expert annotations
                        expert_details = json.dumps({
                            "DF_0_EP4012055A2_EP4012055A2_F1": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：法官协调不构成完全公开"},
                            "DF_1_EP3812049A1_EP3812049A1_F1": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：流式传输非完全公开"},
                            "DF_1_EP3812049A1_EP3812049A1_F2": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：挂起组件非完全公开"},
                            "DF_2_EP3812049A1_EP3812049A1_F3": {"status": "[专家修正]", "novelty_impact": "Low", "details": "专家修正：恢复机制非完全公开"}
                        })
                        async def send_resume():
                            # 延时 1.0 秒确保后端 GET 流已完全进入 event.wait() 挂起状态，规避并发竞态
                            await asyncio.sleep(1.0)
                            try:
                                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as post_client:
                                    res = await post_client.post(
                                        f"/api/v1/evaluation/{interrupt_id}/resume", 
                                        json={"action": "continue", "details": expert_details}
                                    )
                                    print(f"  - send_resume POST status: {res.status_code}, body: {res.text}")
                            except Exception as e:
                                print(f"  - send_resume POST failed with exception: {str(e)}")
                        asyncio.create_task(send_resume())
                    elif event_name == "completed":
                        completed_received = True
                        print("  - completed received")
                        data = json.loads(data_json)
                        state = data.get("state", {})
                        
                        # 验证第二轮辩论与决策注入及概率重算
                        prob = state.get("overall_probability")
                        print(f"  - Recalculated probability: {prob}")
                        assert prob == 0.95
                        
                        logs = state.get("debate_logs", [])
                        round2_examiner_verified = any("审查员 (Round 2)" in log for log in logs)
                        round2_applicant_verified = any("申请人代理 (Round 2)" in log for log in logs)
                        assert round2_examiner_verified
                        assert round2_applicant_verified
                        print("  - Round 2 debate logs and probability verified")
                        
        assert node_start_received and hitl_interrupt_received and completed_received
        print("Successful flow test passed.\n")
 
async def test_invalid_id_flow():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        print("Testing invalid ID flow...")
        invalid_id = "this-is-an-invalid-id"
        response = await client.post(
            f"/api/v1/evaluation/{invalid_id}/resume",
            json={"action": "continue", "details": "looks good"}
        )
        print(f"  - POST /resume with invalid ID returned status {response.status_code}")
        print(f"  - Response body: {response.text}")
        assert response.status_code == 404
        assert "not found" in response.text.lower()
        print("Invalid ID flow test passed.\n")

async def main():
    await test_successful_flow()
    await test_invalid_id_flow()
    print("All tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
