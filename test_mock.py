import sys
import os
import asyncio
import json

# Add server to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

from server.llm_factory import LLMFactory, MockLLMClient
from server.agentic_engine import _argument_pre_processor
from server.blackboard import Blackboard

async def test_argument_processor():
    print("\n--- Testing Argument Processor ---")
    bb = Blackboard()
    
    # 1. Invalid JSON
    res = _argument_pre_processor("some_tool", "{invalid_json", bb)
    print("Invalid JSON:", res)
    assert res == "[ARGUMENT_PROCESSOR] Tool Error: Invalid JSON arguments"
    
    # 2. Not a dict (e.g., list)
    res = _argument_pre_processor("some_tool", "[1, 2, 3]", bb)
    print("Not a dict:", res)
    assert res == "[ARGUMENT_PROCESSOR] Tool Error: Arguments must be a JSON object"
    
    # 3. Missing required for generate_feature_alignment_matrix
    res = _argument_pre_processor("generate_feature_alignment_matrix", '{"domestic_feature_id": "1"}', bb)
    print("Missing required:", res)
    assert res == "[ARGUMENT_PROCESSOR] Tool Error: Missing required parameter 'domestic_feature'"
    
    # 4. Valid generate_feature_alignment_matrix
    res = _argument_pre_processor("generate_feature_alignment_matrix", '{"domestic_feature_id": "1", "domestic_feature": "A", "prior_art_id": "2", "prior_art_feature": "B"}', bb)
    print("Valid generate:", res)
    assert isinstance(res, dict)
    assert "expert_annotations" in res

async def test_mock_fallback_template():
    print("\n--- Testing Mock Local Fallback Template ---")
    
    config = {"model": "test-model"}
    bb = Blackboard()
    client = MockLLMClient("test_agent", config, bb)
    
    tools = [
        {
            "function": {
                "name": "test_tool",
                "parameters": {
                    "properties": {
                        "str_val": {"type": "string"},
                        "int_val": {"type": "integer"},
                        "bool_val": {"type": "boolean"},
                        "obj_val": {"type": "object"},
                        "arr_val": {"type": "array"}
                    }
                }
            }
        }
    ]
    
    messages = [{"role": "user", "content": "hello"}]
    
    # Call local fallback via mock module
    import server.testing_mocks as testing_mocks
    res = await testing_mocks.mock_llm_generate(messages, tools, bb)
    print("Mock fallback response:", json.dumps(res, ensure_ascii=False, indent=2))
    assert res["tool_calls"] is not None
    assert len(res["tool_calls"]) > 0
    
    tc = res["tool_calls"][0]
    args = json.loads(tc["function"]["arguments"])
    
    assert isinstance(args["str_val"], str)
    assert isinstance(args["int_val"], int)
    assert isinstance(args["bool_val"], bool)
    assert isinstance(args["obj_val"], dict)
    assert isinstance(args["arr_val"], list)

    print("All mock types match.")

async def test_circuit_breaker():
    print("\n--- Testing Circuit Breaker ---")
    config = {"model": "test-model-cb"}
    bb = Blackboard()
    client = LLMFactory.get_client("test_agent", config, bb)
    
    # Bypass fake key check if it exists by using a key that starts with sk- but not sk-c714d64
    os.environ["DEEPSEEK_API_KEY"] = "sk-testkey-12345" 
    os.environ["DEEPSEEK_API_BASE"] = "http://localhost:9999" # invalid port
    
    failures = 0
    for i in range(4):
        try:
            await client._call_model("test-model-cb", "test", "")
        except ValueError as e:
            print(f"Call {i+1} failed with: {e}")
            failures += 1
            
    # Check circuit breaker state
    cb_time = LLMFactory._circuit_breaker_until.get("test-model-cb", 0)
    print("Circuit breaker until:", cb_time)
    assert cb_time > 0, "Circuit breaker not triggered"
    print("Circuit breaker triggered successfully.")

async def main():
    await test_argument_processor()
    await test_mock_fallback_template()
    await test_circuit_breaker()
    print("\nAll tests passed successfully.")

if __name__ == "__main__":
    asyncio.run(main())
