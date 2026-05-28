import sys
sys.path.append('.')
from tools.patent_tools import generate_feature_alignment_matrix

result = generate_feature_alignment_matrix(
    domestic_feature_id='DF1',
    domestic_feature='My random domestic feature',
    prior_art_id='PA1',
    prior_art_feature='some string prior art feature',
    expert_annotations={}
)
print(result)
