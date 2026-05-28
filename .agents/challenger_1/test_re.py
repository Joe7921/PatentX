import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.agentic_engine import _argument_pre_processor
from server.blackboard import Blackboard

async def test_re_import():
    print("Testing if missing 're' import causes incorrect idx")
    bb = Blackboard()
    await bb.reset("test", ["Feature A", "Feature B", "Feature C"])
    
    args = {"domestic_feature_id": "DF_1"}
    # we don't provide domestic_feature, so it should auto-complete it using idx
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    
    print(f"Extracted feature: {res.get('domestic_feature')}")

if __name__ == "__main__":
    asyncio.run(test_re_import())
