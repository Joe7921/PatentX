import asyncio
import json
import httpx
from fastapi.testclient import TestClient

# We need to import the app from the server
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from server.main import app

async def run_test():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("Starting stream...")
        
        # We'll collect events here
        events = []
        interrupt_id = None
        
        async def consume_stream():
            nonlocal interrupt_id
            async with client.stream("GET", "/api/v1/analyze/stream") as response:
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    print(f"Received: {line}")
                    if line.startswith("data:"):
                        data_str = line[5:].strip()
                        try:
                            data = json.loads(data_str)
                            if 'id' in data:
                                interrupt_id = data['id']
                                print(f"Captured interrupt ID: {interrupt_id}")
                        except Exception:
                            pass

        stream_task = asyncio.create_task(consume_stream())
        
        # Wait a bit for the stream to yield hitl_interrupt
        await asyncio.sleep(0.5)
        
        if not interrupt_id:
            print("Failed to get interrupt_id")
            stream_task.cancel()
            return
            
        print("\n--- Testing Invalid ID ---")
        invalid_id = "invalid-1234"
        resume_data = {"action": "continue", "details": "some info"}
        resp = await client.post(f"/api/v1/evaluation/{invalid_id}/resume", json=resume_data)
        print(f"Invalid ID Response Status: {resp.status_code}")
        print(f"Invalid ID Response Body: {resp.text}")
        
        print("\n--- Testing Valid ID ---")
        resp = await client.post(f"/api/v1/evaluation/{interrupt_id}/resume", json=resume_data)
        print(f"Valid ID Response Status: {resp.status_code}")
        print(f"Valid ID Response Body: {resp.text}")
        
        # Wait for the stream to finish
        await stream_task

if __name__ == "__main__":
    asyncio.run(run_test())
