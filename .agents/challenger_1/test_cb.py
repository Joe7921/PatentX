import sys
import os
import asyncio
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.llm_factory import LLMFactory

async def test_circuit_breaker():
    print("Testing Circuit Breaker")
    
    # We will instantiate two clients sharing the same model.
    # To force failure, we will pass a bad API base.
    os.environ["DEEPSEEK_API_BASE"] = "http://localhost:9999/bad"
    os.environ["DEEPSEEK_API_KEY"] = "sk-real-key"
    
    config = {"model": "deepseek-v4-flash", "temperature": 0.2}
    client1 = LLMFactory.get_client("agent1", config)
    client2 = LLMFactory.get_client("agent2", config)
    
    # Agent 1 fails twice
    try:
        await client1.chat([{"role": "user", "content": "hi"}])
    except Exception as e:
        pass
    try:
        await client1.chat([{"role": "user", "content": "hi"}])
    except Exception as e:
        pass
        
    print(f"Failures for deepseek-v4-flash: {LLMFactory._failure_counts.get('deepseek-v4-flash')}")
    
    # Agent 2 fails once. This should trip the circuit breaker for Agent 2.
    try:
        await client2.chat([{"role": "user", "content": "hi"}])
    except Exception as e:
        pass
        
    print(f"Failures for deepseek-v4-flash: {LLMFactory._failure_counts.get('deepseek-v4-flash')}")
    cb_time = LLMFactory._circuit_breaker_until.get('deepseek-v4-flash', 0)
    print(f"Circuit breaker until: {cb_time} (Current time: {time.time()})")
    
    if cb_time > time.time():
        print("Circuit breaker was tripped globally by Agent 2's first failure!")

if __name__ == "__main__":
    asyncio.run(test_circuit_breaker())
