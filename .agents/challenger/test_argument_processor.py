import sys
import json
import os

# Add server to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "server"))
from agentic_engine import _argument_pre_processor

def test_processor():
    results = []
    
    # 1. Invalid JSON string
    res = _argument_pre_processor("some_func", "{invalid_json:")
    print(f"Test 1 (Invalid JSON): {res}")
    assert isinstance(res, str) and res.startswith("[ARGUMENT_PROCESSOR] Tool Error: Invalid JSON"), "Failed Test 1"
    
    # 2. Valid JSON but not dict
    res = _argument_pre_processor("some_func", "[1, 2, 3]")
    print(f"Test 2 (List instead of Dict): {res}")
    assert isinstance(res, str) and res.startswith("[ARGUMENT_PROCESSOR] Tool Error: Arguments must be a JSON object"), "Failed Test 2"

    # 3. None arguments
    res = _argument_pre_processor("some_func", None)
    print(f"Test 3 (None arguments): {res}")
    assert isinstance(res, str) and res.startswith("[ARGUMENT_PROCESSOR] Tool Error: Arguments must be a JSON object"), "Failed Test 3"

    # 4. Missing required parameter for generate_feature_alignment_matrix
    res = _argument_pre_processor("generate_feature_alignment_matrix", '{"domestic_feature_id": "1"}')
    print(f"Test 4 (Missing req param): {res}")
    assert isinstance(res, str) and "Missing required parameter" in res, "Failed Test 4"

    # 5. Missing expert_annotations auto-fill
    res = _argument_pre_processor("generate_feature_alignment_matrix", {
        "domestic_feature_id": "1",
        "domestic_feature": "A",
        "prior_art_id": "2",
        "prior_art_feature": "B"
    })
    print(f"Test 5 (Auto-fill expert_annotations): {res}")
    assert isinstance(res, dict) and res["expert_annotations"] == "{}", "Failed Test 5"

    # 6. expert_annotations provided but not string (should be auto-filled/replaced)
    res = _argument_pre_processor("generate_feature_alignment_matrix", {
        "domestic_feature_id": "1",
        "domestic_feature": "A",
        "prior_art_id": "2",
        "prior_art_feature": "B",
        "expert_annotations": ["not", "a", "string"]
    })
    print(f"Test 6 (Invalid expert_annotations type): {res}")
    assert isinstance(res, dict) and res["expert_annotations"] == "{}", "Failed Test 6"

    # 7. expert_annotations provided as string (should be preserved)
    res = _argument_pre_processor("generate_feature_alignment_matrix", {
        "domestic_feature_id": "1",
        "domestic_feature": "A",
        "prior_art_id": "2",
        "prior_art_feature": "B",
        "expert_annotations": '{"custom": "yes"}'
    })
    print(f"Test 7 (Valid expert_annotations type): {res}")
    assert isinstance(res, dict) and res["expert_annotations"] == '{"custom": "yes"}', "Failed Test 7"

    print("ALL TESTS PASSED")

if __name__ == "__main__":
    test_processor()
