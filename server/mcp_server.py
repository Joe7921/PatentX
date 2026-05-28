import sys
import os
from typing import Dict, Any, List, Tuple

# 确保能找到项目根目录下的 tools 包
current_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(current_dir)
if project_dir not in sys.path:
    sys.path.append(project_dir)

from tools.patent_tools import (
    search_patent_db as _search_patent_db,
    search_academic_db as _search_academic_db,
    generate_feature_alignment_matrix as _generate_feature_alignment_matrix
)
from mcp.server.fastmcp import FastMCP

# 创建 PatentX MCP Server
mcp = FastMCP("PatentX_Tools")

@mcp.tool()
def search_patent_db(query: str) -> str:
    """
    检索 EPO 专利数据库。
    传入需要检索的文本，返回匹配的专利 ID 和相关特征的 JSON 字符串。
    """
    import json
    results = _search_patent_db(query)
    return json.dumps(results, ensure_ascii=False)

@mcp.tool()
def search_academic_db(query: str) -> str:
    """
    检索学术文献 (NPL)。
    """
    return _search_academic_db(query)

@mcp.tool()
def generate_feature_alignment_matrix(
    domestic_feature_id: str,
    domestic_feature: str,
    prior_art_id: str,
    prior_art_feature: str,
    expert_annotations: str = "{}"
) -> str:
    """
    针对国内专利特征与检索到的对比文件特征生成对齐矩阵（评估新颖性）。
    expert_annotations: JSON 字符串，包含人类专家针对该组合的预先批注。
    """
    import json
    try:
        prior_art_feat_dict = json.loads(prior_art_feature)
    except Exception:
        prior_art_feat_dict = {"id": "unknown", "text": prior_art_feature}
        
    try:
        expert_ann_dict = json.loads(expert_annotations)
    except Exception:
        expert_ann_dict = {}

    result = _generate_feature_alignment_matrix(
        domestic_feature_id,
        domestic_feature,
        prior_art_id,
        prior_art_feat_dict,
        expert_ann_dict
    )
    return json.dumps(result, ensure_ascii=False)

if __name__ == "__main__":
    # 以 stdio 模式运行
    mcp.run(transport="stdio")
