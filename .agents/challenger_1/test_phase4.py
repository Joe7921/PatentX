import asyncio
import os
import sys

# Add both root (for tools) and server to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "server")))

from agentic_engine import _determine_vote, _get_generic_vote_reasoning
from blackboard import Blackboard
from llm_factory import MockLLMClient, LLMFactory

async def test_phase4_mock_failure():
    print("Testing Phase 4 mock failure...")
    
    # We will instantiate a MockLLMClient and call generate without tools
    # Force the local fallback by using a fake API key
    os.environ["DEEPSEEK_API_KEY"] = "sk-c714d64-fake-test-key"
    
    bb = Blackboard()
    llm = LLMFactory.get_client("chairman", {"model": "deepseek-v4-flash"}, bb)
    
    # Simulate Phase 4 generate call
    system_instruction = "You are chairman. Output JSON."
    prompt = "Here is the debate..."
    
    resp = await llm.generate(prompt, system_instruction=system_instruction)
    print(f"MockLLMClient.generate returned: {resp}")
    
    content = resp.get("content", "")
    
    # Ensure it's not JSON
    try:
        import json
        json.loads(content)
        print("FAIL: Content is valid JSON")
    except json.JSONDecodeError:
        print("PASS: Content is NOT valid JSON")
        
        # Test agentic engine fallback logic
        bb.feature_alignment_matrices = {"PA_1": []}
        vote_decision = _determine_vote("chairman", 3)
        print(f"Vote decision from _determine_vote: {vote_decision}")
        reasoning = await _get_generic_vote_reasoning("chairman", vote_decision, bb)
        print(f"Context-aware reasoning: {reasoning}")
        print("PASS: Fallback logic executed successfully")

if __name__ == "__main__":
    asyncio.run(test_phase4_mock_failure())
