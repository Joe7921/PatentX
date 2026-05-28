import sys
import os
import asyncio
import time
import json

# Add server directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from llm_factory import LLMFactory
from agentic_engine import _argument_pre_processor
from blackboard import Blackboard

async def test_argument_processor():
    print("\n--- Testing Argument Processor ---")
    blackboard = Blackboard()
    await blackboard.reset("test_eval_1", ["Feature A", "Feature B"])
    await blackboard.set_retrieved_patents([
        {"id": "PA_1", "title": "Test Patent 1", "patent_family": "F1", "claim_1": "Test claim", "features": [
            {"id": "PA_1_F0", "text": "PA Feature A", "focus": "Test"},
            {"id": "PA_1_F1", "text": "PA Feature B", "focus": "Test"}
        ]}
    ])

    # Test 1: Empty arguments
    print("Test 1: Empty arguments for generate_feature_alignment_matrix")
    raw_args = {}
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, blackboard)
    print("Processed:", processed)
    assert processed["domestic_feature_id"] == "default_df_id", "Failed to assign default DF ID"
    # Note: If domestic_feature_id defaults to "default_df_id", index regex extraction might fail and yield 0.
    assert processed["domestic_feature"] == "Feature A", f"Failed to assign domestic feature, got: {processed.get('domestic_feature')}"
    assert processed["prior_art_id"] == "PA_1", "Failed to assign prior art ID"
    
    # Test 2: Valid arguments but missing some
    print("Test 2: Partial arguments")
    raw_args = {"domestic_feature_id": "DF_1"}
    processed = _argument_pre_processor("generate_feature_alignment_matrix", raw_args, blackboard)
    print("Processed:", processed)
    assert processed["domestic_feature"] == "Feature B", "Failed to assign domestic feature for index 1"
    
    print("Argument Processor Tests Passed.")

async def test_circuit_breaker_and_mock_transport():
    print("\n--- Testing Circuit Breaker & Mock Transport ---")
    LLMFactory._circuit_breaker_until = {}
    LLMFactory._failure_counts = {}
    
    config = {
        "model": "deepseek-v4-flash",
        "fallback_model": None
    }
    client = LLMFactory.get_client("test_agent", config)
    
    # Set invalid API key to trigger failures
    os.environ["DEEPSEEK_API_KEY"] = "invalid_key_for_test"
    os.environ["DEEPSEEK_API_BASE"] = "http://localhost:9999/nonexistent"
    
    print("Simulating consecutive failures...")
    for i in range(1, 5):
        print(f"Call {i}...")
        try:
            # chat internally calls _call_model_chat, which catches exceptions and calls _call_local_fallback_template
            # But wait, chat() catches the Exception and invokes fallback, so it NEVER throws outside!
            res = await client.chat([{"role": "user", "content": "Hello"}])
            print(f"Result {i}: {res['content'][:50]}")
            # The circuit breaker is triggered *inside* _call_model_chat, but chat() swallows it and returns Mock!
        except Exception as e:
            print(f"Exception {i}: {e}")

    print("Checking circuit breaker state...")
    cb_until = LLMFactory._circuit_breaker_until.get("deepseek-v4-flash", 0)
    failures = LLMFactory._failure_counts.get("deepseek-v4-flash", 0)
    print(f"CB Until: {cb_until}, Failures: {failures}")
    
    assert cb_until > time.time(), "Circuit breaker was not tripped!"
    
    # Wait for recovery
    print("Faking time to test recovery...")
    LLMFactory._circuit_breaker_until["deepseek-v4-flash"] = time.time() - 1
    
    # Next call should attempt API again, fail, and increment failures?
    # Wait, the code says:
    # if cb_until and now >= cb_until:
    #     LLMFactory._circuit_breaker_until[mapped_model] = 0
    #     LLMFactory._failure_counts[mapped_model] = 0
    res = await client.chat([{"role": "user", "content": "Hello again"}])
    assert LLMFactory._circuit_breaker_until.get("deepseek-v4-flash", 0) == 0, "CB should be reset"
    assert LLMFactory._failure_counts.get("deepseek-v4-flash", 0) == 1, "Failures should be 1 after reset and immediate fail"
    print("Circuit Breaker Recovery Test Passed.")

if __name__ == "__main__":
    asyncio.run(test_argument_processor())
    asyncio.run(test_circuit_breaker_and_mock_transport())
