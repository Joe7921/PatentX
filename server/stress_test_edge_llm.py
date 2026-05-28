import asyncio
import json
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'server'))

from llm_factory import LLMFactory

async def test_llm_factory_edge_cases():
    print("--- Testing LLMFactory Generic Mock Fallback Edge Cases ---")
    
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
        }
    ]
    
    messages = [{"role": "user", "content": "trigger mock tool calls with edge cases"}]
    
    try:
        res = await client.chat(messages, tools=tools)
        print("Edge case 1 chat returned successfully!")
        print(res)
    except Exception as e:
        print(f"LLMFactory failed on edge case 1: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_factory_edge_cases())
