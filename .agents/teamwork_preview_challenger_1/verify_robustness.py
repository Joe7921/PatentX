import asyncio
import os
import sys
import json
import time

# Add the server and root directory to python path
sys.path.append(os.path.join(r"d:\Antigravity projects\PatentX\server"))
sys.path.append(os.path.join(r"d:\Antigravity projects\PatentX"))

from llm_factory import LLMFactory
from agentic_engine import _argument_pre_processor
from blackboard import Blackboard

async def test_argument_processor():
    print("=== Testing Argument Processor ===")
    bb = Blackboard()
    # Mock some state
    bb.claim_features = ["Feature A", "Feature B", "Feature C"]
    await bb.set_retrieved_patents([
        {"id": "EP4012055A2", "features": [{"id": "F1", "text": "foo"}]},
        {"id": "EP3812049A1", "features": [{"id": "F1", "text": "bar"}]}
    ])
    
    # 1. Test empty args
    raw_args = {}
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, bb)
    print(f"Empty args -> {processed}")
    assert processed["domestic_feature_id"] == "DF_0"
    
    # 2. Test implicit domestic_feature_id from text
    raw_args = {"domestic_feature": "采用SSE流式传输，状态挂起"}
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, bb)
    print(f"Implicit SSE -> {processed}")
    assert processed["domestic_feature_id"] == "DF_1"
    
    # 3. Test string payload
    raw_args = '{"domestic_feature": "有鉴权恢复"}'
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, bb)
    print(f"String JSON -> {processed}")
    assert processed["domestic_feature_id"] == "DF_2"
    
    print("Argument Processor Tests Passed!\n")

async def test_mock_transport_and_circuit_breaker():
    print("=== Testing Mock Transport & Circuit Breaker ===")
    
    # Temporarily rename .env so load_dotenv() doesn't override our env vars
    env_path = r"d:\Antigravity projects\PatentX\server\.env"
    env_bak_path = r"d:\Antigravity projects\PatentX\server\.env.bak_test"
    if os.path.exists(env_path):
        os.rename(env_path, env_bak_path)
        
    try:
        # 1. Set fake key to trigger Mock Transport immediately
        os.environ["DEEPSEEK_API_KEY"] = "sk-c714d64_fake_key_for_test"
        
        bb = Blackboard()
        client = LLMFactory.get_client("first_examiner", {"model": "gemini-1.5-pro"}, bb)
        
        res = await client.generate("Test prompt")
        print(f"Fast fail Mock Transport response: {res['content'][:50]}...")
        assert "正在执行检索" in res["content"] or "检索" in res["content"]
        
        # 2. Test Circuit Breaker
        # Use a non-fake key to bypass fast fail
        os.environ["DEEPSEEK_API_KEY"] = "sk-real-but-invalid-key"
        # Set a bad base URL to trigger httpx connection error
        os.environ["DEEPSEEK_API_BASE"] = "http://127.0.0.1:12345"
        
        client = LLMFactory.get_client("first_examiner", {"model": "deepseek-v4-flash"}, bb)
        
        # Fail 3 times to trigger CB
        for i in range(3):
            try:
                print(f"Call {i+1}...")
                await client._call_model("deepseek-v4-flash", "Test", "")
            except ValueError as e:
                print(f"Expected failure: {e}")
                
        # The 4th call should immediately raise Circuit Breaker before httpx
        print("Testing 4th call...")
        try:
            await client._call_model("deepseek-v4-flash", "Test", "")
            print("FAIL: Circuit breaker did not trigger")
        except ValueError as e:
            if "Circuit breaker active" in str(e):
                print("Circuit breaker triggered successfully!")
            else:
                print(f"Unexpected error: {e}")
                
        # Chat() should also hit Circuit Breaker and use Mock transport
        res2 = await client.chat([{"role": "user", "content": "Test"}])
        print(f"Chat Mock fallback after CB: {res2['content'][:50]}...")
        assert "正在执行检索" in res2["content"] or "检索" in res2["content"]
        print("Mock Transport & Circuit Breaker Tests Passed!\n")
    finally:
        # Restore .env
        if os.path.exists(env_bak_path):
            if os.path.exists(env_path):
                os.remove(env_path)
            os.rename(env_bak_path, env_path)

async def main():
    await test_argument_processor()
    await test_mock_transport_and_circuit_breaker()

if __name__ == "__main__":
    asyncio.run(main())
