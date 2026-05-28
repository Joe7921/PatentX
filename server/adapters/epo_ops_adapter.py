# epo_ops_adapter.py
# EPO OPS API 适配器

import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.base_adapter import BaseAdapter

class EpoOpsAdapter(BaseAdapter):
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # 前置 PII 脱敏
        safe_query = self.filter_pii(query)
        
        if self.mock_fallback:
            import os
            mock_module = os.getenv("MOCK_INJECTION_MODULE")
            if mock_module:
                import importlib
                mock = importlib.import_module(mock_module)
                
                # 定位焦点
                focus_keywords = [kw for kw in ["辩论", "debate", "法官", "judge", "矩阵", "matrix"] if kw in query.lower()]
                if not focus_keywords:
                    focus_keywords = ["patent"]
                    
                return mock.mock_bigquery_retrieve(safe_query, focus_keywords, self.truncate_by_budget)
            else:
                raise RuntimeError("EPO OPS client not initialized and no mock module injected.")
        else:
            raise NotImplementedError("Real EPO OPS credentials not configured. Set mock_fallback=true.")
