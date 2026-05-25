# lens_adapter.py
# The Lens API 适配器

import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.base_adapter import BaseAdapter
from tools.patent_tools import PatentDatabase

class LensAdapter(BaseAdapter):
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        safe_query = self.filter_pii(query)
        
        if self.mock_fallback:
            # 仿真获取 The Lens 数据
            raw_results = PatentDatabase.recursive_retrieve(safe_query)
            processed_results = []
            
            # 定位焦点
            focus_keywords = [kw for kw in ["流", "stream", "辩论", "debate"] if kw in query.lower()]
            if not focus_keywords:
                focus_keywords = ["patent"]
                
            for pid, pdata in raw_results:
                truncated_claim = self.truncate_by_budget(pdata["claim_1"], focus_keywords)
                processed_results.append({
                    "id": pid,
                    "title": pdata["title"],
                    "patent_family": pdata["patent_family"],
                    "claim_1": truncated_claim,
                    "features": pdata["features"]
                })
            return processed_results
        else:
            raise NotImplementedError("Real Lens API token not configured. Set mock_fallback=true.")
