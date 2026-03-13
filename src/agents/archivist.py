import os
import json

class ArchivistAgent:
    """Generates final technical documentation from the Knowledge Graph artifacts."""
    
    def __init__(self, output_dir: str = ".cartography"):
        
        self.output_dir = output_dir

    def generate_documents(self, module_data: dict, lineage_data: dict) -> str:
        """Translates raw JSON artifacts into a human-readable README summary."""
        nodes = module_data.get("nodes", [])
        edges = lineage_data.get("edges", [])
        
        summary = [
            "# Codebase Cartography Report\n",
            f"## System Overview\n",
            f"- **Total Modules Scanned:** {len(nodes)}\n",
            f"- **Lineage Connections:** {len(edges)}\n",
            "\n## Top Architectural Hubs (PageRank)\n"
        ]
        
        # Simple extraction of top nodes for the report
        for node in nodes[:5]:
            node_id = node.get("id")
            if node_id:
                summary.append(f"- {node_id}\n")
            
        report_path = os.path.join(self.output_dir, "README_SUMMARY.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(summary))
            
        return report_path