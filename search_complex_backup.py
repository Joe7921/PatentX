import os

agents_dir = r"d:\Antigravity projects\PatentX\.agents"
matches = []

for root, dirs, files in os.walk(agents_dir):
    for file in files:
        path = os.path.join(root, file)
        # 排除自己的 original_prompt.md 等
        if "worker_m7_verifier_retry" in path:
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if "export default function DiagnosticDashboard" in content:
                    print(f"Match: {path}, len: {len(content)}, lines: {len(content.splitlines())}")
                    matches.append(path)
        except Exception as e:
            pass

print("Search completed.")
