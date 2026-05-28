# bigquery_adapter.py
# Google Patents BigQuery 真实适配器 (支持 credentials 密钥加载与公共数据集 SQL 查询)

import sys
import os
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from adapters.base_adapter import BaseAdapter

class BigQueryAdapter(BaseAdapter):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client = None
        if not self.mock_fallback:
            self._init_client()

    def _init_client(self):
        from google.oauth2 import service_account
        from google.cloud import bigquery
        
        server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_key = os.path.join(server_dir, "gcp-key.json")
        
        # 优先读取配置文件中的密钥路径，其次找本地 gcp-key.json
        cred_path = self.config.get("credentials_json") or local_key
        
        if cred_path and os.path.exists(cred_path):
            try:
                credentials = service_account.Credentials.from_service_account_file(cred_path)
                self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
                print(f"[BigQuery] Initialized real Client using key file: {cred_path}")
            except Exception as e:
                print(f"[BigQuery] Failed to load key file '{cred_path}': {e}")
                self.client = None
        elif os.getenv("ENV_GCP_CREDENTIALS"):
            try:
                import json
                info = json.loads(os.getenv("ENV_GCP_CREDENTIALS"))
                credentials = service_account.Credentials.from_service_account_info(info)
                self.client = bigquery.Client(credentials=credentials, project=credentials.project_id)
                print("[BigQuery] Initialized real Client using ENV_GCP_CREDENTIALS")
            except Exception as e:
                print(f"[BigQuery] Failed to load credentials from ENV: {e}")
                self.client = None
                
        if not self.client:
            # 尝试使用 GCP 默认凭证
            try:
                self.client = bigquery.Client()
                print("[BigQuery] Initialized real Client using Application Default Credentials (ADC)")
            except Exception as e:
                print(f"[BigQuery] Application Default Credentials load failed: {e}")
                print("[BigQuery] Falling back to MOCK database due to missing GCP credentials.")
                self.mock_fallback = True

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # 前置安全脱敏
        safe_query = self.filter_pii(query)
        
        # 从查询词中拆分出焦点关键字用于滑动窗口截断
        focus_keywords = [kw for kw in ["流", "stream", "中断", "pause", "恢复", "resume"] if kw in query.lower()]
        if not focus_keywords:
            focus_keywords = ["patent"]  # 兜底焦点
            
        if self.mock_fallback:
            import os
            mock_module = os.getenv("MOCK_INJECTION_MODULE")
            if mock_module:
                import importlib
                mock = importlib.import_module(mock_module)
                return mock.mock_bigquery_retrieve(safe_query, focus_keywords, self.truncate_by_budget)
            else:
                raise RuntimeError("BigQuery client not initialized and no mock module injected.")
            
        else:
            # 真实 BigQuery 公开专利表查询
            if not self.client:
                self._init_client()
                
            # 若初始化失败，自动降级为 Mock 防止崩溃
            if not self.client or self.mock_fallback:
                print("[BigQuery] Client not initialized. Checking for dynamic mock injection.")
                self.mock_fallback = True
                return self.retrieve(query)
                
            regex_pattern = "|".join(focus_keywords) if focus_keywords else "agent|stream|pause|resume"
            
            # SQL 查询 patents-public-data 公开数据集
            sql = f"""
            SELECT 
              publication_number,
              (SELECT text FROM UNNEST(title_localized) WHERE language = 'en' LIMIT 1) as title,
              (SELECT text FROM UNNEST(abstract_localized) WHERE language = 'en' LIMIT 1) as abstract,
              (SELECT text FROM UNNEST(claims_localized) WHERE language = 'en' LIMIT 1) as claim
            FROM 
              `patents-public-data.patents.publications`
            WHERE 
              country_code = 'EP'
              AND (
                EXISTS(
                  SELECT 1 FROM UNNEST(title_localized) t 
                  WHERE language = 'en' AND REGEXP_CONTAINS(LOWER(t.text), r'{regex_pattern}')
                )
                OR EXISTS(
                  SELECT 1 FROM UNNEST(abstract_localized) a
                  WHERE language = 'en' AND REGEXP_CONTAINS(LOWER(a.text), r'{regex_pattern}')
                )
              )
            LIMIT 5
            """
            
            try:
                print(f"[BigQuery] Querying patents-public-data using regex: {regex_pattern}...")
                query_job = self.client.query(sql)
                results = query_job.result()
                
                processed_results = []
                for row in results:
                    pid = row.publication_number
                    title = row.title or "Untitled EP Patent"
                    claim_text = row.claim or row.abstract or "No claims description text available"
                    
                    # 执行 Token Budget 滑动窗口截断
                    truncated_claim = self.truncate_by_budget(claim_text, focus_keywords)
                    
                    # 动态生成子特征，以便契合下游 Agent 辩论对齐
                    features = []
                    import re
                    parts = [p.strip() for p in re.split(r'[,;.]', claim_text) if len(p.strip()) > 10]
                    if not parts:
                        parts = [claim_text]
                    
                    for i, part in enumerate(parts[:3]):
                        matched_focus = next((kw for kw in focus_keywords if kw.lower() in part.lower()), None)
                        if not matched_focus:
                            words = re.findall(r'\b[A-Za-z]{5,}\b', part)
                            matched_focus = words[0] if words else "Feature"
                            
                        features.append({
                            "id": f"{pid}_F{i+1}",
                            "text": part[:150],
                            "focus": matched_focus.capitalize()
                        })
                    
                    processed_results.append({
                        "id": pid,
                        "title": title,
                        "patent_family": "EP-FAMILY-REAL",
                        "claim_1": truncated_claim,
                        "features": features
                    })
                    
                if not processed_results:
                    print("[BigQuery] Real query returned 0 results. Check mock injection.")
                    self.mock_fallback = True
                    return self.retrieve(query)
                    
                return processed_results
                
            except Exception as e:
                print(f"[BigQuery] Real query execution failed: {e}. Check mock injection.")
                self.mock_fallback = True
                return self.retrieve(query)
