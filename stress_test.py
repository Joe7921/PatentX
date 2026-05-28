import sys
import os
import asyncio
import json
import traceback

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "server"))

from server.llm_factory import MockLLMClient
from server.blackboard import Blackboard
from server.agentic_engine import _argument_pre_processor

async def stress_test():
    print("--- Stress Testing Gen4 Mock & Argument Processor ---")
    
    config = {"model": "test-model"}
    bb = Blackboard()
    client = MockLLMClient("test_agent", config, bb)
    
    # Test Case 1: Empty tools list
    print("\n[Test 1] Empty tools list")
    res = await client._call_local_fallback_template([{"role": "user", "content": "hi"}], tools=[])
    print("Result (Empty tools):", res.get("content"))
    
    # Test Case 2: tools with missing 'function' or 'parameters' or 'properties'
    print("\n[Test 2] tools with parameters: None")
    tools_param_none = [{"function": {"name": "tool_param_none", "parameters": None}}]
    try:
        res = await client._call_local_fallback_template([{"role": "user", "content": "hi"}], tools=tools_param_none)
        print("Success (unexpected):", res)
    except Exception as e:
        print("Crash caught:", type(e).__name__, str(e))
        traceback.print_exc(limit=2)

    print("\n[Test 3] tools with properties: None")
    tools_prop_none = [{"function": {"name": "tool_prop_none", "parameters": {"properties": None}}}]
    try:
        res = await client._call_local_fallback_template([{"role": "user", "content": "hi"}], tools=tools_prop_none)
        print("Success (unexpected):", res)
    except Exception as e:
        print("Crash caught:", type(e).__name__, str(e))
        traceback.print_exc(limit=2)
        
    print("\n[Test 4] Blackboard is None in MockLLMClient")
    client_no_bb = MockLLMClient("test_agent", config, blackboard=None)
    try:
        res = await client_no_bb._call_local_fallback_template([{"role": "user", "content": "hi"}], tools=[{"function": {"name": "test"}}])
        print("Success with None blackboard! Tool calls:", len(res.get("tool_calls", [])))
    except Exception as e:
        print("Crash caught:", type(e).__name__, str(e))
        
    print("\n[Test 5] Blackboard is None in _argument_pre_processor")
    try:
        tc_args = json.dumps({
            "domestic_feature_id": "1", 
            "domestic_feature": "A", 
            "prior_art_id": "2", 
            "prior_art_feature": "B"
        })
        res = _argument_pre_processor("generate_feature_alignment_matrix", tc_args, None)
        print("Success! Auto-filled expert_annotations:", res.get("expert_annotations"))
    except Exception as e:
        print("Crash caught:", type(e).__name__, str(e))

if __name__ == "__main__":
    asyncio.run(stress_test())
