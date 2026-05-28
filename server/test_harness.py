import asyncio
import json
import time
import os
import sys

# Ensure project root is in path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'server'))

from llm_factory import LLMFactory, MockLLMClient
from agentic_engine import _argument_pre_processor
from blackboard import Blackboard

async def test_argument_processor():
    print("--- Testing Argument Processor ---")
    bb = Blackboard()
    
    # 1. Invalid JSON string
    res = _argument_pre_processor("generate_feature_alignment_matrix", "invalid json", bb)
    print("Invalid JSON:", res)
    assert "[ARGUMENT_PROCESSOR] Tool Error" in res, "Should fail on invalid json"
    
    # 2. Not a dict
    res = _argument_pre_processor("generate_feature_alignment_matrix", "[]", bb)
    print("Not a dict:", res)
    assert "[ARGUMENT_PROCESSOR] Tool Error" in res, "Should fail on non-dict"
    
    # 3. Missing required
    res = _argument_pre_processor("generate_feature_alignment_matrix", '{"domestic_feature_id": "D1"}', bb)
    print("Missing required:", res)
    assert "[ARGUMENT_PROCESSOR] Tool Error" in res, "Should fail on missing required"
    
    # 4. Auto-fill expert_annotations
    valid_args = {
        "domestic_feature_id": "D1",
        "domestic_feature": "A device",
        "prior_art_id": "P1",
        "prior_art_feature": "A tool"
    }
    bb.expert_annotations = {"D1": "Important"}
    res = _argument_pre_processor("generate_feature_alignment_matrix", valid_args, bb)
    print("Valid args auto-fill:", res)
    assert "expert_annotations" in res
    assert '"D1": "Important"' in res["expert_annotations"], "Should auto-fill expert_annotations"

    # 5. Non-generate_feature_alignment_matrix tool
    res = _argument_pre_processor("some_other_tool", {"a": 1}, bb)
    print("Other tool:", res)
    assert res == {"a": 1}, "Should pass through"
    print("Argument Processor tests passed.\n")

async def test_circuit_breaker():
    print("--- Testing Circuit Breaker ---")
    # Reset state
    LLMFactory._failure_counts = {}
    LLMFactory._circuit_breaker_until = {}
    
    bb = Blackboard()
    # Mock config with a fake API base to trigger failures
    os.environ["DEEPSEEK_API_KEY"] = "sk-real-key-for-test" # Bypass fake key check
    os.environ["DEEPSEEK_API_BASE"] = "http://localhost:9999/nonexistent" # Port 9999 should refuse connection
    
    config = {"model": "deepseek-v4-flash"}
    client = LLMFactory.get_client("test_agent", config, blackboard=bb)
    
    # Trigger 3 failures
    for i in range(3):
        print(f"Attempt {i+1}...")
        res = await client.generate("hello")
        assert "[MOCK_TRANSPORT]" in res["content"]
            
    # Next attempt should hit circuit breaker immediately
    start = time.time()
    res = await client.generate("hello")
    elapsed = time.time() - start
    
    # It should have returned Mock without even trying to hit the API (so elapsed time is tiny)
    assert "[MOCK_TRANSPORT]" in res["content"]
    assert elapsed < 0.5, f"Circuit breaker should fast-fail, took {elapsed}s"
    
    # Verify the breaker is active
    assert LLMFactory._circuit_breaker_until["deepseek-v4-flash"] > time.time()
    print("Circuit Breaker tests passed.\n")

async def test_mock_fallback_generic():
    print("--- Testing Generic Mock Fallback ---")
    # Clean up circuit breaker so it doesn't block local fallback in chat
    LLMFactory._circuit_breaker_until = {}
    LLMFactory._failure_counts = {}
    
    bb = Blackboard()
    # Trigger local fallback directly by omitting DEEPSEEK_API_KEY
    os.environ["DEEPSEEK_API_KEY"] = "sk-c714d64-fake-key"
    
    config = {"model": "test-model"}
    client = LLMFactory.get_client("test_agent", config, blackboard=bb)
    
    # 1. Empty blackboard, chat mode (Phase 1)
    tools = [
        {
            "function": {
                "name": "my_test_tool",
                "parameters": {
                    "properties": {
                        "param_str": {"type": "string"},
                        "param_int": {"type": "integer"},
                        "param_bool": {"type": "boolean"},
                        "param_arr": {"type": "array"},
                        "param_obj": {"type": "object"}
                    }
                }
            }
        }
    ]
    messages = [{"role": "user", "content": "do something"}]
    
    res = await client.chat(messages, tools=tools)
    print("Phase 1 Mock:", res)
    assert "[MOCK_TRANSPORT]" in res["content"]
    assert res["tool_calls"] is not None
    assert len(res["tool_calls"]) > 0
    
    args = json.loads(res["tool_calls"][0]["function"]["arguments"])
    print("Generated mock args:", args)
    assert isinstance(args["param_str"], str)
    assert isinstance(args["param_int"], int)
    assert isinstance(args["param_bool"], bool)
    assert isinstance(args["param_arr"], list)
    assert isinstance(args["param_obj"], dict)
    
    # 2. Phase 4 Mock (voting)
    bb.current_phase = 4
    messages_phase4 = [
        {"role": "user", "content": "time to vote"}
        # Add 3 rounds to avoid tool calls
    ]
    for _ in range(4):
        messages_phase4.append({"role": "assistant", "tool_calls": []})
        
    res2 = await client.chat(messages_phase4, tools=tools)
    print("Phase 4 Mock:", res2)
    assert "[MOCK_TRANSPORT]" in res2["content"]
    assert "vote" in res2["content"]
    assert "probability" in res2["content"]
    
    print("Generic Mock Fallback tests passed.\n")

if __name__ == "__main__":
    asyncio.run(test_argument_processor())
    asyncio.run(test_circuit_breaker())
    asyncio.run(test_mock_fallback_generic())
    print("ALL TESTS PASSED")
