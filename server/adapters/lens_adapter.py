# lens_adapter.py
# The Lens API 适配器

import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.base_adapter import BaseAdapter

class LensAdapter(BaseAdapter):
    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        safe_query = self.filter_pii(query)
        
        if self.mock_fallback:
            import os
            mock_module = os.getenv("MOCK_INJECTION_MODULE")
            if mock_module:
                import importlib
                mock = importlib.import_module(mock_module)
                
                # 定位焦点
                focus_keywords = [kw for kw in ["流", "stream", "辩论", "debate"] if kw in query.lower()]
                if not focus_keywords:
                    focus_keywords = ["patent"]
                
                return mock.mock_bigquery_retrieve(safe_query, focus_keywords, self.truncate_by_budget)
            else:
                raise RuntimeError("Lens client not initialized and no mock module injected.")
            
        else:
            raise NotImplementedError("Real Lens API token not configured. Set mock_fallback=true.")
