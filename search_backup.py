import os

agents_dir = r"d:\Antigravity projects\PatentX\.agents"
matches = []

for root, dirs, files in os.walk(agents_dir):
    for file in files:
        if "DiagnosticDashboard" in file or file.endswith(".tsx") or file.endswith(".ts") or file.endswith(".py"):
            path = os.path.join(root, file)
            matches.append(path)

print("Found files:", matches)
