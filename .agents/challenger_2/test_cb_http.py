import asyncio
import os
import sys
import httpx
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

    config = {'model': 'deepseek-v4-pro'}
    client = LLMFactory.get_client('epo_examiner', config)
    
    for i in range(5):
        print(f'Call {i}')
        # chat will catch the exception and fallback
        result = await client.chat([{'role': 'user', 'content': 'test'}])
        print('Result:', result['content'][:50])
            
    print('Failure counts:', LLMFactory._failure_counts)
    print('Circuit breaker until:', LLMFactory._circuit_breaker_until)

asyncio.run(test())
