import os
import yaml
import json
import py_compile
import sys

def verify_configs():
    base_dir = r"d:\Antigravity projects\PatentX"
    errors = []

    # 1. Check Python tools
    tools_dir = os.path.join(base_dir, "tools")
    for file in os.listdir(tools_dir):
        if file.endswith(".py"):
            try:
                py_compile.compile(os.path.join(tools_dir, file), doraise=True)
            except Exception as e:
                errors.append(f"Python compile error in {file}: {e}")

    # 2. Check YAML files
    yaml_files = [
        "app/agents/_custom/patent_judge.yaml",
        "app/agents/_custom/epo_examiner.yaml",
        "app/agents/_custom/patent_applicant.yaml",
        "app/agents/_custom/pii_filter.yaml",
        "app/interactions/_custom/adversarial_debate.yaml"
    ]
    for yf in yaml_files:
        full_path = os.path.join(base_dir, yf)
        if not os.path.exists(full_path):
            errors.append(f"Missing YAML file: {yf}")
        else:
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    yaml.safe_load(f)
            except Exception as e:
                errors.append(f"YAML parse error in {yf}: {e}")

    # 3. Check JSON
    json_path = os.path.join(base_dir, "patentx_pipeline.json")
    if not os.path.exists(json_path):
        errors.append("Missing JSON file: patentx_pipeline.json")
    else:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                pipeline = json.load(f)
            
            # 4. Check dependencies in JSON
            steps = pipeline.get("global_routing", {}).get("layer_0", [])
            components_found = set()
            for step in steps:
                if "component" in step:
                    components_found.add(step["component"])
                if "nested_subgraph" in step:
                    l1 = step["nested_subgraph"].get("layer_1", {})
                    if "controller" in l1:
                        components_found.add(l1["controller"])
                    if "layer_2_tools" in l1:
                        for tool in l1["layer_2_tools"]:
                            components_found.add(tool)
            
            for comp in components_found:
                comp_path = os.path.join(base_dir, comp)
                if not os.path.exists(comp_path):
                    errors.append(f"Pipeline component missing: {comp}")

        except Exception as e:
            errors.append(f"JSON parse error: {e}")

    if errors:
        print("Verification failed with errors:")
        for err in errors:
            print(f"- {err}")
        sys.exit(1)
    else:
        print("Verification passed! All files are valid.")
        sys.exit(0)

if __name__ == "__main__":
    verify_configs()
