import os
import json
import math
import re

from src.agents.surveyor import Surveyor
from src.analyzers.git_analyzer import get_git_velocity
from src.models.models import FileNode

def main():
    # 1. Target repository path
    target_repo = os.path.abspath("C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform") 
    
    surveyor = Surveyor()
    knowledge_graph = []

    print(f"--- Mapping Codebase: {target_repo} ---")

    # 2. Safety Check
    if not os.path.exists(target_repo):
        print(f"ERROR: Directory NOT FOUND at {target_repo}")
        return

    file_count = 0
    # The broadened loop starts here
    for root, dirs, files in os.walk(target_repo):
        for file in files:
            # BROADEN THE FILTER: Include SQL and YAML
            if file.endswith((".py", ".sql", ".yml", ".yaml")):
                file_count += 1
                full_path = os.path.join(root, file)
                
                try:
                    # Logic: Use the Surveyor ONLY for Python files
                    if file.endswith(".py"):
                        file_node = surveyor.parse_file(full_path)
                    else:
                        # For SQL, extract dbt 'ref' or 'source' as imports
                        with open(full_path, "r", encoding="utf-8") as f:
                            content = f.read()
    
                        # Regex to find {{ ref('model_name') }}
                        dbt_refs = re.findall(r"ref\(['\"](\w+)['\"]\)", content)
    
                        file_node = FileNode(
                            file_path=full_path,
                            language="sql" if file.endswith(".sql") else "yaml",
                            file_size=os.path.getsize(full_path),
                            imports=dbt_refs, # Now your imports won't be empty!
                            entities=[]
    )

                    # Get the velocity for EVERY file (SQL included)
                    file_node.change_frequency = get_git_velocity(full_path)
                    
                    knowledge_graph.append(file_node)
                    print(f"[{file_count}] Registered: {file} ({file_node.language}) | Velocity: {file_node.change_frequency}")
                    
                except Exception as e:
                    print(f"FAILED to process {file}: {e}")

    if file_count == 0:
        print("WARNING: No relevant files found. Check your target_repo path!")

    survey_data = [node.model_dump() for node in knowledge_graph]

    # 4. Final Phase 1 Analysis
    print("\n--- Running Phase 1 Analytics (NetworkX) ---")
    from src.graph.knowledge_graph import analyze_codebase_graph

    # Save only final analysis artifacts under .cartography.
    os.makedirs(".cartography", exist_ok=True)
    module_graph_path = ".cartography/module_graph.json"

    analysis = analyze_codebase_graph(module_graph_path, survey_data=survey_data)

    # Compute high-velocity core from in-memory FileNode objects.
    sorted_nodes = sorted(knowledge_graph, key=lambda node: node.change_frequency, reverse=True)
    if sorted_nodes:
        top_count = max(1, math.ceil(len(sorted_nodes) * 0.2))
        analysis["high_velocity_core"] = [node.file_path for node in sorted_nodes[:top_count]]
    else:
        analysis["high_velocity_core"] = []

    # Per specs: write the graph to .cartography/module_graph.json
    with open(module_graph_path, "w") as f:
        json.dump(analysis, f, indent=4)

    print(f"--- Done! Saved graph analysis to {module_graph_path} ---")

    print(f"Top Architectural Hub: {analysis['hubs'][0] if analysis['hubs'] else 'N/A'}")
    print(f"Circular Loops Found: {len(analysis['circular_dependencies'])}")
    print(f"High-Velocity Core Files: {len(analysis['high_velocity_core'])}")
    print("--- Phase 1 Complete ---")

if __name__ == "__main__":
    main()
