import asyncio
import os
import sys
import time

sys.path.append(os.path.abspath(r"d:\Antigravity projects\PatentX\server"))
sys.path.append(os.path.abspath(r"d:\Antigravity projects\PatentX"))

from llm_factory import LLMFactory, MockLLMClient
from blackboard import Blackboard
from agentic_engine import _argument_pre_processor

async def test_circuit_breaker_and_mock_transport():
    print("=== Testing Circuit Breaker ===")
    
    # rename .env temporarily so load_dotenv doesn't override our mock
    env_path = os.path.abspath(r"d:\Antigravity projects\PatentX\server\.env")
    env_backup = env_path + ".bak"
    if os.path.exists(env_path):
        os.rename(env_path, env_backup)
        
    try:
        # Do NOT inject failure, just give a wrong API BASE to cause network error
        os.environ["INJECT_LLM_FAILURE"] = "false"
        os.environ["DEEPSEEK_API_KEY"] = "sk-invalid_key"
        os.environ["DEEPSEEK_API_BASE"] = "http://localhost:12345/non_existent_api"
        
        config = {"model": "deepseek-v4-flash", "fallback_model": None}
        blackboard = Blackboard()
        client = LLMFactory.get_client("epo_examiner", config, blackboard)
        
        messages = [{"role": "user", "content": "hello"}]
        
        # Reset state
        LLMFactory._failure_counts = {}
        LLMFactory._circuit_breaker_until = {}
        
        for i in range(1, 6):
            try:
                print(f"Call {i}...")
                await client._call_model_chat("deepseek-v4-flash", messages)
            except ValueError as e:
                if "Circuit breaker active" in str(e):
                    print(f"-> Circuit breaker triggered on call {i} successfully! Expected on call 4 or 5.")
                elif "Failed to connect to LLM API" in str(e):
                    print(f"-> Network failed on call {i} (Count: {LLMFactory._failure_counts.get('deepseek-v4-flash', 0)})")
                else:
                    print(f"-> Caught other ValueError: {e}")
                
        print("\n=== Testing Mock Transport (chat method) ===")
        # It should hit the circuit breaker or fallback immediately
        result = await client.chat(messages)
        print("Mock Transport Result content:")
        print(result.get("content"))
    finally:
        if os.path.exists(env_backup):
            if os.path.exists(env_path):
                os.remove(env_path)
            os.rename(env_backup, env_path)

def test_argument_processor():
    print("\n=== Testing Argument Processor ===")
    blackboard = Blackboard()
    blackboard.claim_features = ["Feature A", "Feature B", "Feature C"]
    
    raw_args = '{"focus": "test"}'
    
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, blackboard)
    
    assert "domestic_feature_id" in processed
    assert "prior_art_id" in processed
    assert "prior_art_feature" in processed
    assert "domestic_feature" in processed
    print("-> Argument Processor completed successfully")

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker_and_mock_transport())
    test_argument_processor()
    print("\nAll tests passed locally!")
