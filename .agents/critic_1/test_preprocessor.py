import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'server')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio
from agentic_engine import _argument_pre_processor

def test_argument_pre_processor():
    bb = None
    
    args = {"domestic_feature_id": "1", "domestic_feature": "2", "prior_art_id": "3", "prior_art_feature": "4"}
    res = _argument_pre_processor("generate_feature_alignment_matrix", args, bb)
    assert isinstance(res, dict)
    
    import json
    args_str = json.dumps(args)
    res = _argument_pre_processor("generate_feature_alignment_matrix", args_str, bb)
    assert isinstance(res, dict)
    
    res = _argument_pre_processor("generate_feature_alignment_matrix", "{invalid:", bb)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR]")
    
    res = _argument_pre_processor("generate_feature_alignment_matrix", '"just string"', bb)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR]")
    
    args_missing = {"domestic_feature": "2"}
    res = _argument_pre_processor("generate_feature_alignment_matrix", args_missing, bb)
    assert isinstance(res, str)
    assert res.startswith("[ARGUMENT_PROCESSOR]")
    
    print("All tests passed!")

if __name__ == "__main__":
    test_argument_pre_processor()
