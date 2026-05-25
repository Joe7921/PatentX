# run_test.py
# 启动真实 FastAPI 开发服务器并运行 verify_backend.py 集成测试，以防 ASGI 内存死锁。

import subprocess
import time
import sys
import os

def main():
    server_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 物理删除遗留文件 PatentStarChart.tsx
    target_chart = os.path.abspath(os.path.join(server_dir, "..", "frontend", "src", "components", "PatentStarChart.tsx"))
    if os.path.exists(target_chart):
        print(f"Physically removing legacy component: {target_chart}")
        os.remove(target_chart)
    else:
        print(f"Legacy component not found (already deleted): {target_chart}")

    log_file = open(os.path.join(server_dir, "uvicorn.log"), "w")
    # 1. 启动 uvicorn 真实服务后台进程
    print("Starting FastAPI dev server via uvicorn...")
    server_proc = subprocess.Popen(
        ["py", "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8089"],
        cwd=server_dir,
        stdout=log_file,
        stderr=log_file,
        text=True
    )
    
    # 等待服务器端口就绪
    time.sleep(2.5)
    
    # 检查服务器进程是否意外退出
    if server_proc.poll() is not None:
        print("Failed to start uvicorn server!")
        log_file.close()
        with open(os.path.join(server_dir, "uvicorn.log"), "r") as f:
            print(f"UVICORN LOGS:\n{f.read()}")
        sys.exit(1)
        
    try:
        # 2. 运行 verify_backend.py，将端口指定为 8089
        print("Running verify_backend.py integration test...")
        # 传递环境变量指定测试端口
        env = os.environ.copy()
        env["TEST_PORT"] = "8089"
        
        test_res = subprocess.run(
            ["py", "verify_backend.py"],
            cwd=server_dir,
            env=env,
            capture_output=True,
            text=True
        )
        
        print("Test run completed.")
        print(f"--- TEST STDOUT ---\n{test_res.stdout}")
        print(f"--- TEST STDERR ---\n{test_res.stderr}")
        
        ret_code = test_res.returncode
    finally:
        # 3. 强行关闭服务器进程
        print("Stopping dev server...")
        server_proc.terminate()
        server_proc.wait()
        log_file.close()
        
    if ret_code == 0:
        print("Integration verification PASSED!")
    else:
        print("Integration verification FAILED!")
        with open(os.path.join(server_dir, "uvicorn.log"), "r") as f:
            print(f"--- UVICORN LOGS ---\n{f.read()}")
        
    sys.exit(ret_code)

if __name__ == "__main__":
    main()
