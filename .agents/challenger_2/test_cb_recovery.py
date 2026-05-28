import asyncio
import os
import sys
import httpx
import time
sys.path.append('.')
from server.llm_factory import LLMFactory

async def test():
    # Avoid Fast failing
    os.environ['DEEPSEEK_API_KEY'] = 'sk-real-key'
    
    # Mock httpx to simulate real HTTP failure
    class MockResponse:
        status_code = 500
        text = "Internal Server Error"
        
    class MockClient:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass
        async def post(self, *args, **kwargs):
            return MockResponse()
            
    httpx.AsyncClient = MockClient

    # Mock time
    original_time = time.time
    current_time = original_time()
    
    def mock_time():
        return current_time
    time.time = mock_time

    config = {'model': 'deepseek-v4-pro'}
    client = LLMFactory.get_client('epo_examiner', config)
    
    # Trip the breaker
    print("--- Tripping Breaker ---")
    for i in range(3):
        await client.chat([{'role': 'user', 'content': 'test'}])
        
    print('Failure counts:', LLMFactory._failure_counts)
    print('Circuit breaker until:', LLMFactory._circuit_breaker_until)
    
    # Advance time by 35 seconds (past breaker duration)
    print("--- Advancing time by 35s ---")
    current_time += 35
    
    # One more call, should try and fail, but does it trip immediately?
    await client.chat([{'role': 'user', 'content': 'test'}])
    print('After 1 failure on recovery:')
    print('Failure counts:', LLMFactory._failure_counts)
    print('Circuit breaker until:', LLMFactory._circuit_breaker_until)
    
    # Check if breaker is open again
    current_time += 1 # advance 1s
    try:
        await client.chat([{'role': 'user', 'content': 'test'}])
    except Exception as e:
        pass
    print('After 2 failures on recovery:')
    print('Failure counts:', LLMFactory._failure_counts)
    print('Circuit breaker until:', LLMFactory._circuit_breaker_until)

asyncio.run(test())
