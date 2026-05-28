import asyncio
from server.agentic_engine import _argument_pre_processor
from server.blackboard import Blackboard
import json

def test_argument_pre_processor():
    print("Testing _argument_pre_processor...")
    bb = Blackboard()

    # Test 1: Valid JSON dict
    print("\nTest 1: Valid JSON dict")
    args = '{"domestic_feature_id": "DF_0", "domestic_feature": "abc", "prior_art_id": "PA_1", "prior_art_feature": "def"}'
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    print("Result:", type(res), res)
    assert isinstance(res, dict)
    assert res.get("prior_art_id") == "PA_1"

    # Test 2: Valid JSON string (not a dict)
    print("\nTest 2: Valid JSON string")
    args = '"just a string"'
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    print("Result:", type(res), res)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR] Tool Error")

    # Test 3: Invalid JSON string
    print("\nTest 3: Invalid JSON string")
    args = '{"unclosed_dict: "value"'
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    print("Result:", type(res), res)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR] Tool Error")

    # Test 4: Valid JSON list (not a dict)
    print("\nTest 4: Valid JSON list")
    args = '["a", "b"]'
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    print("Result:", type(res), res)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR] Tool Error")
    
    # Test 5: None
    print("\nTest 5: None")
    res = _argument_pre_processor("generate_feature_alignment_matrix", None, bb)
    print("Result:", type(res), res)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR] Tool Error")
    
    # Test 6: Python object directly passed as dict
    print("\nTest 6: Python dict directly")
    args = {"domestic_feature_id": "DF_0", "domestic_feature": "abc", "prior_art_id": "PA_1", "prior_art_feature": "def"}
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    print("Result:", type(res), res)
    assert isinstance(res, dict)
    assert res.get("prior_art_id") == "PA_1"

    print("\nAll stress tests passed for _argument_pre_processor.")

if __name__ == "__main__":
    test_argument_pre_processor()
