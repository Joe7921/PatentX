import os

frontend_dir = r"d:\Antigravity projects\PatentX\frontend"
for root, dirs, files in os.walk(frontend_dir):
    for file in files:
        if "DiagnosticDashboard" in file:
            print(os.path.join(root, file))
