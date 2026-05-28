import asyncio
import os
import time
from server.llm_factory import LLMFactory

async def test():
    # Intentionally use a fake API key so it fails quickly
    os.environ["DEEPSEEK_API_KEY"] = "sk-c714d64_fake_key_to_force_failure"
    
    config = {
        "model": "deepseek-v4-flash",
        "temperature": 0.0
    }
    client = LLMFactory.get_client("test_agent", config)
    
    print("Testing generate()...")
    # Call 1 (failure -> fallback)
    res1 = await client.generate("Input Message 1: How are you?")
    print("Call 1 result:", res1)
    
    # Call 2
    res2 = await client.generate("Input Message 2: What is your name?")
    print("Call 2 result:", res2)
    
    # Call 3
    res3 = await client.generate("Input Message 3: Tell me a joke.")
    print("Call 3 result:", res3)
    
    # Call 4 - should trigger circuit breaker!
    try:
        res4 = await client.generate("Input Message 4: Circuit Breaker time.")
        print("Call 4 result:", res4)
    except Exception as e:
        print("Call 4 error:", e)

if __name__ == "__main__":
    asyncio.run(test())
