import sys
import os
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from server.agentic_engine import _argument_pre_processor
from server.blackboard import Blackboard

async def test_argument_processor():
    print("Testing _argument_pre_processor")
    
    # Mock blackboard
    bb = Blackboard()
    # Ensure it's populated a bit
    await bb.reset("test", ["Feature A"])
    await bb.set_retrieved_patents([{"id": "PA_1", "features": [{"id": "F1", "text": "txt", "focus": "foc"}]}])
    
    # Test 1: pa_id is None
    # if prior_art_id is explicitly passed as None, the processor might crash at pa_id in p["id"]
    # Wait, the code says:
    # if "prior_art_id" not in tc_args or not tc_args["prior_art_id"]:
    # So if it's None, it will be replaced.
    try:
        args = {"prior_art_id": None}
        res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
        print("Test 1 (prior_art_id=None): Pass")
    except Exception as e:
        print(f"Test 1 (prior_art_id=None): Fail - {type(e).__name__}: {e}")

    # Test 2: raw_args is completely malformed (e.g., list instead of dict, or string that doesn't parse to dict)
    try:
        res = _argument_pre_processor("generate_feature_alignment_matrix", '["not a dict"]', bb)
        print("Test 2 (raw_args is list string): Pass")
    except Exception as e:
        print(f"Test 2 (raw_args is list string): Fail - {type(e).__name__}: {e}")

    # Test 3: raw_args is None
    try:
        res = _argument_pre_processor("generate_feature_alignment_matrix", None, bb)
        print("Test 3 (raw_args=None): Pass")
    except Exception as e:
        print(f"Test 3 (raw_args=None): Fail - {type(e).__name__}: {e}")

    # Test 4: domestic_feature_id without numbers
    try:
        args = {"domestic_feature_id": "DF_NO_NUMBER"}
        res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
        print("Test 4 (df_id without numbers): Pass")
    except Exception as e:
        print(f"Test 4 (df_id without numbers): Fail - {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_argument_processor())
