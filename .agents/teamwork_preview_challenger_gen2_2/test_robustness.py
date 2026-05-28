import os
import sys
import time
import asyncio

# Add codebase root to sys.path
sys.path.append(r"d:\Antigravity projects\PatentX")
sys.path.append(r"d:\Antigravity projects\PatentX\server")
from server.llm_factory import LLMFactory, MockLLMClient
from server.agentic_engine import _argument_pre_processor
from server.blackboard import Blackboard

async def test_circuit_breaker():
    print("--- Testing Circuit Breaker ---")
    config = {"model": "test-model"}
    client = LLMFactory.get_client("test_agent", config)
    mapped_model = "test-model"
    
    # Simulate 3 failures
    LLMFactory._failure_counts[mapped_model] = 3
    LLMFactory._circuit_breaker_until[mapped_model] = time.time() + 1 # 1 second breaker
    
    print("Circuit Breaker initially tripped. _failure_counts:", LLMFactory._failure_counts[mapped_model])
    
    # Wait for breaker to expire
    time.sleep(1.1)
    
    # Call _call_model to trigger the reset logic without raising exception early
    # But _call_model actually makes an HTTP request.
    # To avoid real HTTP request, we can just look at the reset logic in _call_model manually,
    # or we can mock httpx.AsyncClient.
    
    # Since we can't easily mock httpx here without patching, let's just observe the behavior.
    # Actually, we can use a fake DEEPSEEK_API_KEY to fast-fail, which triggers ValueError early, 
    # but the reset logic runs before that.
    os.environ["DEEPSEEK_API_KEY"] = "sk-c714d64-fake"
    
    try:
        await client._call_model("test-model", "test prompt", "system prompt")
    except ValueError as e:
        print("Caught expected ValueError:", e)
        
    print("After timeout and one request, _failure_counts is:", LLMFactory._failure_counts.get(mapped_model))
    print("If it is 0, the Half-Open state is NOT implemented correctly, because 1 failure after timeout should trip it again (count=3+1 or count kept at 3).")

async def test_mock_transport():
    print("\n--- Testing Mock Transport ---")
    config = {"model": "test-model"}
    client = LLMFactory.get_client("first_examiner", config)
    
    # Send a completely unrelated prompt
    messages = [{"role": "user", "content": "How do I bake a cake?"}]
    response = await client._call_local_fallback_template(messages)
    
    print("Fallback template response for unrelated prompt:")
    print(response.get("content"))
    print("Tool calls:", response.get("tool_calls"))
    
async def test_argument_processor():
    print("\n--- Testing Argument Processor ---")
    blackboard = Blackboard()
    blackboard.claim_features = ["Feature X: some generic feature"]
    
    # Simulate calling the tool with missing arguments
    tc_args = {}
    processed_args = _argument_pre_processor("generate_feature_alignment_matrix", tc_args, blackboard)
    print("Processed args with empty input:", processed_args)

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker())
    asyncio.run(test_mock_transport())
    asyncio.run(test_argument_processor())
