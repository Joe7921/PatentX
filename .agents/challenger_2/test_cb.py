import asyncio
import os
import sys
sys.path.append('.')
from server.llm_factory import LLMFactory

async def test():
    os.environ['INJECT_LLM_FAILURE'] = 'true'
    # Need DEEPSEEK_API_KEY to avoid Fast failing
    os.environ['DEEPSEEK_API_KEY'] = 'sk-real-key'
    
    config = {'model': 'v4-flash'}
    client = LLMFactory.get_client('epo_examiner', config)
    
    for i in range(5):
        print(f'Call {i}')
        # chat will catch the exception and fallback
        result = await client.chat([{'role': 'user', 'content': 'test'}])
        print('Result:', result['content'][:50])
            
    print('Failure counts:', LLMFactory._failure_counts)
    print('Circuit breaker until:', LLMFactory._circuit_breaker_until)

asyncio.run(test())
