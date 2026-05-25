import subprocess

try:
    # 尝试从 git HEAD 恢复文件内容
    content = subprocess.check_output(
        ["git", "show", "HEAD:frontend/src/components/DiagnosticDashboard.tsx"],
        text=True,
        encoding="utf-8"
    )
    with open("frontend/src/components/DiagnosticDashboard.tsx", "w", encoding="utf-8") as f:
        f.write(content)
    print("RESTORE_SUCCESS")
except Exception as e:
    print("RESTORE_FAILED", str(e))
