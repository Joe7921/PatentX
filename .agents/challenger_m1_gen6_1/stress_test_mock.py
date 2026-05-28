import sys
import os
import asyncio
import json

sys.path.append(r"d:\Antigravity projects\PatentX")
from server.llm_factory import MockLLMClient
from server.blackboard import Blackboard

async def run_stress_test():
    bb = Blackboard()
    client = MockLLMClient("test_agent", {"model": "mock"}, bb)
    
    # Edge case 1: Tool with no parameters
    tools1 = [{"function": {"name": "tool_no_params"}}]
    
    # Edge case 2: Tool with null properties
    tools2 = [{"function": {"name": "tool_null_props", "parameters": {"properties": None}}}]
    
    # Edge case 3: Tool with null property value
    tools3 = [{"function": {"name": "tool_null_val", "parameters": {"properties": {"val1": None}}}}]
    
    # Edge case 4: Tool with missing type
    tools4 = [{"function": {"name": "tool_missing_type", "parameters": {"properties": {"val1": {}}}}}]

    messages = [{"role": "user", "content": "hello"}]
    
    for i, tools in enumerate([tools1, tools2, tools3, tools4]):
        print(f"\nTesting Edge Case {i+1}...")
        try:
            res = await client._call_local_fallback_template(messages, tools)
            print(f"Success: {json.dumps(res)}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"FAILED Edge Case {i+1}: {type(e).__name__} - {e}")

if __name__ == "__main__":
    asyncio.run(run_stress_test())
