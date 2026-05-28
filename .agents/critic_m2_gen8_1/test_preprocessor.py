import sys
import json
sys.path.append('d:/Antigravity projects/PatentX')
sys.path.append('d:/Antigravity projects/PatentX/server')
from server.agentic_engine import _argument_pre_processor

class MockBlackboard:
    def __init__(self):
        self.expert_annotations = {"some": "data"}

blackboard = MockBlackboard()

tests = [
    ('test1', 'invalid json'),
    ('test2', '"just a string"'),
    ('test3', 'null'),
    ('generate_feature_alignment_matrix', '{"domestic_feature_id": "1", "domestic_feature": "test"}'),
    ('generate_feature_alignment_matrix', '{"domestic_feature_id": "1", "domestic_feature": "test", "prior_art_id": "2", "prior_art_feature": "test"}'),
    ('generate_feature_alignment_matrix', {"domestic_feature_id": "1", "domestic_feature": "test", "prior_art_id": "2", "prior_art_feature": "test", "expert_annotations": 123}),
]

for name, args in tests:
    print(f'\n--- Testing {name} with args {args} ---')
    try:
        res = _argument_pre_processor(name, args, blackboard)
        print(f'Result: {res}')
    except Exception as e:
        print(f'Exception: {e}')
