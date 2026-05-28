import sys
import os
import asyncio
import json
import time

sys.path.append(r"d:\Antigravity projects\PatentX")
sys.path.append(r"d:\Antigravity projects\PatentX\server")

from server.llm_factory import LLMFactory
from server.blackboard import Blackboard
from server.agentic_engine import _argument_pre_processor

async def test_argument_processor():
    print("--- Testing Argument Processor ---")
    blackboard = Blackboard()
    blackboard.claim_features = ["Feature A", "Feature B"]
    
    # 1. Missing domestic_feature_id and prior_art_id
    raw_args = {"domestic_feature": "test", "prior_art_feature": "test"}
    res = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, blackboard)
    print("Test 1 Result:", res)
    assert res["domestic_feature_id"] == "default_df_id", "Failed to fix domestic_feature_id"
    assert "default_pa_id" in str(res.get("prior_art_id", "")), "Failed to fix prior_art_id"

    # 2. String instead of dict
    raw_args_str = '{"domestic_feature": "test2"}'
    res2 = _argument_pre_processor("generate_feature_alignment_matrix", raw_args_str, blackboard)
    print("Test 2 Result:", res2)
    assert isinstance(res2, dict), "Failed to parse json string"
    assert res2["domestic_feature"] == "test2"
    assert res2["domestic_feature_id"] == "default_df_id"
    print("Argument Processor test passed!\n")

async def test_circuit_breaker_and_mock_transport():
    print("--- Testing Circuit Breaker & Mock Transport ---")
    blackboard = Blackboard()
    
    # Use an invalid config to force failure
    config = {
        "model": "deepseek-v4-flash",
        "api_key": "fake_key",
        "api_base": "http://127.0.0.1:9999/v1" # invalid url to trigger immediate connection error
    }
    
    client = LLMFactory.get_client("test_agent", config, blackboard)
    
    # Force 3 failures
    for i in range(3):
        try:
            print(f"Attempt {i+1}...")
            await client._call_model("hello", config["api_base"], config["api_key"], config["model"])
        except Exception as e:
            print(f"Exception caught: {e}")
            
    # Check circuit breaker status
    cb_time = LLMFactory._circuit_breaker_until.get(config["model"], 0)
    print(f"Circuit breaker until: {cb_time}")
    
    # Test 4th attempt - should immediately trigger circuit breaker (or fail fast)
    try:
        print("Attempt 4 (Should be short-circuited)...")
        await client._call_model("hello", config["api_base"], config["api_key"], config["model"])
    except Exception as e:
        print(f"Exception caught on attempt 4: {e}")
        
    # Test chat generation which uses fallback
    print("Testing chat fallback...")
    messages = [{"role": "user", "content": "test"}]
    res = await client.chat(messages=messages, tools=[])
    print(f"Fallback content: {res.get('content')}")
    
    # Reset CB
    LLMFactory._circuit_breaker_until = {}
    LLMFactory._failure_counts = {}
    print("Circuit Breaker test passed!\n")

async def main():
    await test_argument_processor()
    await test_circuit_breaker_and_mock_transport()

if __name__ == "__main__":
    asyncio.run(main())
