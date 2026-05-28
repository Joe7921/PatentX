import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../tools')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../server')))

from tools.patent_tools import generate_feature_alignment_matrix

def test_feature_alignment_matrix():
    print("Testing generate_feature_alignment_matrix")
    
    # Test 1: Normal execution
    try:
        res = generate_feature_alignment_matrix(
            "DF_1", "Feature A", "PA_1", {"id": "PA_1_F1", "text": "Feature A", "focus": "A"}, {}
        )
        print("Test 1 (Normal): Pass")
    except Exception as e:
        print(f"Test 1 (Normal): Fail - {e}")

    # Test 2: expert_annotations is None
    try:
        res = generate_feature_alignment_matrix(
            "DF_1", "Feature A", "PA_1", {"id": "PA_1_F1", "text": "Feature A", "focus": "A"}, None
        )
        print("Test 2 (expert_annotations=None): Pass")
    except Exception as e:
        print(f"Test 2 (expert_annotations=None): Fail - {type(e).__name__}: {e}")

    # Test 3: prior_art_feature is None
    try:
        res = generate_feature_alignment_matrix(
            "DF_1", "Feature A", "PA_1", None, {}
        )
        print("Test 3 (prior_art_feature=None): Pass")
    except Exception as e:
        print(f"Test 3 (prior_art_feature=None): Fail - {type(e).__name__}: {e}")

    # Test 4: prior_art_feature is empty dict (missing 'text')
    try:
        res = generate_feature_alignment_matrix(
            "DF_1", "Feature A", "PA_1", {}, {}
        )
        print("Test 4 (prior_art_feature={}): Pass")
    except Exception as e:
        print(f"Test 4 (prior_art_feature={{}}): Fail - {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_feature_alignment_matrix()
