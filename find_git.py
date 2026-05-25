import os

current = os.path.abspath(".")
print("Current dir:", current)

while True:
    git_dir = os.path.join(current, ".git")
    if os.path.exists(git_dir):
        print("Found .git in:", current)
        break
    parent = os.path.dirname(current)
    if parent == current:
        print("No .git found in parents")
        break
    current = parent

print("Contents of current dir:", os.listdir("."))
