import sys
import os

sys.path.append(r"d:\Antigravity projects\PatentX")
sys.path.append(r"d:\Antigravity projects\PatentX\server")
from server.adapters.bigquery_adapter import BigQueryAdapter

def run_bq_stress_test():
    adapter = BigQueryAdapter({})
    
    # Force mock fallback to test the internal truncation and generation
    adapter.mock_fallback = True
    
    # Edge Case 1: Empty query
    print("\nTesting Empty Query...")
    try:
        res = adapter.retrieve("")
        print(f"Empty Query Success, returned {len(res)} results")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Empty Query Failed: {e}")
        
    # Edge Case 2: Very long query
    print("\nTesting Very Long Query...")
    try:
        res = adapter.retrieve("a " * 10000)
        print(f"Long Query Success, returned {len(res)} results")
    except Exception as e:
        print(f"Long Query Failed: {e}")
        
    # Edge Case 3: Query with weird characters
    print("\nTesting Special Chars...")
    try:
        res = adapter.retrieve("!@#$%^&*()")
        print(f"Special Chars Success, returned {len(res)} results")
    except Exception as e:
        print(f"Special Chars Failed: {e}")

if __name__ == "__main__":
    run_bq_stress_test()
