import asyncio
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'server'))

from llm_factory import LLMFactory
from adapters.bigquery_adapter import BigQueryAdapter

async def test_llm_factory_edge_cases():
    print("--- Testing LLMFactory Generic Mock Fallback Edge Cases ---")
    
    # We want to force the local fallback template to trigger.
    # To do this, we provide a non-existent API base to trigger connection error,
    # or just an invalid token which fails and retries until fallback.
    os.environ["DEEPSEEK_API_KEY"] = "sk-fake-key"
    os.environ["DEEPSEEK_API_BASE"] = "http://localhost:9999/nonexistent"
    
    config = {"model": "test-edge-model"}
    client = LLMFactory.get_client("test_agent", config)
    
    # Edge case 1: property type missing, explicitly null, or properties is null
    tools = [
        {
            "function": {
                "name": "edge_tool_1",
                "parameters": {
                    "properties": {
                        "no_type": {},
                        "null_prop": None
                    }
                }
            }
        },
        {
            "function": {
                "name": "edge_tool_2",
                "parameters": {
                    "properties": None
                }
            }
        },
        {
            "function": {
                "name": "edge_tool_3",
                "parameters": None
            }
        },
        {
            "function": None
        }
    ]
    
    messages = [{"role": "user", "content": "trigger mock tool calls with edge cases"}]
    
    try:
        res = await client.chat(messages, tools=tools)
        print("Edge case chat returned successfully!")
        print(res)
    except Exception as e:
        print(f"LLMFactory failed on edge cases: {e}")
        import traceback
        traceback.print_exc()

def test_bigquery_edge_cases():
    print("--- Testing BigQueryAdapter Edge Cases ---")
    
    config = {"mock_fallback": True}
    adapter = BigQueryAdapter(config)
    
    try:
        # Edge case 1: None query
        print("Querying with None...")
        res = adapter.retrieve(None)
        print(f"None query result: {res}")
    except Exception as e:
        print(f"BigQueryAdapter failed on None query: {e}")
        
    try:
        # Edge case 2: Object query
        print("Querying with dict...")
        res = adapter.retrieve({"some": "object"})
        print(f"Dict query result: {res}")
    except Exception as e:
        print(f"BigQueryAdapter failed on dict query: {e}")

if __name__ == "__main__":
    test_bigquery_edge_cases()
    asyncio.run(test_llm_factory_edge_cases())
