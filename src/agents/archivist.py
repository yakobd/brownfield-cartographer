import os
import json
from datetime import datetime, timezone

class ArchivistAgent:
    """Generates final technical documentation from the Knowledge Graph artifacts."""
    
    def __init__(self, output_dir: str = ".cartography"):
        
        self.output_dir = output_dir

    def log_trace(
        self,
        agent_name: str,
        action: str,
        evidence_source: str,
        confidence_score: float,
    ) -> None:
        """Append a trace entry to .cartography/cartography_trace.jsonl."""
        os.makedirs(self.output_dir, exist_ok=True)
        trace_path = os.path.join(self.output_dir, "cartography_trace.jsonl")
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": agent_name,
            "action": action,
            "evidence_source": evidence_source,
            "confidence_score": confidence_score,
        }
        with open(trace_path, "a", encoding="utf-8") as trace_file:
            trace_file.write(json.dumps(entry) + "\n")

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

        summary.append("\n## Business Purpose Statements\n")
        purpose_count = 0
        for node in nodes:
            semantic = node.get("semantic_analysis") if isinstance(node, dict) else None
            if not isinstance(semantic, dict):
                continue

            purpose = semantic.get("purpose")
            if not purpose:
                continue

            node_id = node.get("id", "unknown")
            summary.append(f"- **{node_id}**: {purpose}\n")
            purpose_count += 1

        if purpose_count == 0:
            summary.append("- No semantic purpose statements were generated.\n")
            
        report_path = os.path.join(self.output_dir, "README_SUMMARY.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(summary))
            
        return report_path

    def generate_CODEBASE_md(self, module_graph_path: str, lineage_graph_path: str) -> str:
        """Build CODEBASE.md from module and lineage graph artifacts."""
        with open(module_graph_path, "r", encoding="utf-8") as module_file:
            module_data = json.load(module_file)
        with open(lineage_graph_path, "r", encoding="utf-8") as lineage_file:
            lineage_data = json.load(lineage_file)

        module_nodes = module_data.get("nodes", [])
        lineage_nodes = lineage_data.get("nodes", [])

        top_modules = sorted(
            module_nodes,
            key=lambda node: float(node.get("pagerank", 0.0) or 0.0),
            reverse=True,
        )[:5]

        critical_path_lines = []
        for node in top_modules:
            node_id = str(node.get("id", "unknown"))
            pagerank = float(node.get("pagerank", 0.0) or 0.0)
            critical_path_lines.append(f"- {node_id} (PageRank: {pagerank:.6f})")
        if not critical_path_lines:
            critical_path_lines.append("- No PageRank-ranked modules found.")

        source_points = sorted(
            {
                str(node.get("id", "unknown"))
                for node in lineage_nodes
                if str(node.get("id", "")).startswith("source:")
            }
        )
        sink_points = sorted(
            {
                str(node.get("id", "unknown"))
                for node in lineage_nodes
                if str(node.get("id", "")).startswith("sink:")
            }
        )
        data_points_lines = []
        data_points_lines.append("Ingestion points:")
        data_points_lines.extend([f"- {item}" for item in source_points] or ["- None detected"])
        data_points_lines.append("Output points:")
        data_points_lines.extend([f"- {item}" for item in sink_points] or ["- None detected"])

        circular_dependencies = module_data.get("circular_dependencies", [])
        drift_flags = []
        for node in module_nodes:
            semantic = node.get("semantic_analysis") if isinstance(node, dict) else None
            if not isinstance(semantic, dict):
                continue
            if semantic.get("drift_detected") is True:
                drift_note = semantic.get("drift_note")
                node_id = str(node.get("id", "unknown"))
                if drift_note:
                    drift_flags.append(f"- {node_id}: {drift_note}")
                else:
                    drift_flags.append(f"- {node_id}: Documentation drift detected")

        technical_debt_lines = []
        if circular_dependencies:
            technical_debt_lines.append("Circular dependencies:")
            for cycle in circular_dependencies:
                technical_debt_lines.append(f"- {' -> '.join(cycle)}")
        else:
            technical_debt_lines.append("Circular dependencies:")
            technical_debt_lines.append("- None detected")

        technical_debt_lines.append("Documentation Drift flags:")
        technical_debt_lines.extend(drift_flags or ["- None detected"])

        high_velocity_modules = sorted(
            module_nodes,
            key=lambda node: int(node.get("change_frequency", 0) or 0),
            reverse=True,
        )[:10]
        high_velocity_lines = [
            f"- {str(node.get('id', 'unknown'))} (change_frequency: {int(node.get('change_frequency', 0) or 0)})"
            for node in high_velocity_modules
        ] or ["- None detected"]

        overview = (
            "This CODEBASE summary combines module structure and lineage metadata to highlight where the system's "
            "architecture is concentrated, how data flows from ingestion to sink points, and where operational risk "
            "is likely to accumulate due to dependency complexity, documentation drift, or high change velocity."
        )

        self.log_trace(
            agent_name="ArchivistAgent",
            action="Write Architecture Overview",
            evidence_source=f"{module_graph_path}, {lineage_graph_path}",
            confidence_score=0.82,
        )
        self.log_trace(
            agent_name="ArchivistAgent",
            action="Write Critical Path",
            evidence_source=module_graph_path,
            confidence_score=0.90,
        )
        self.log_trace(
            agent_name="ArchivistAgent",
            action="Write Data Sources & Sinks",
            evidence_source=lineage_graph_path,
            confidence_score=0.90,
        )
        self.log_trace(
            agent_name="ArchivistAgent",
            action="Write Technical Debt",
            evidence_source=module_graph_path,
            confidence_score=0.86,
        )
        self.log_trace(
            agent_name="ArchivistAgent",
            action="Write High-Velocity Core",
            evidence_source=module_graph_path,
            confidence_score=0.90,
        )

        output_lines = [
            "# CODEBASE\n",
            "Architecture Overview:\n",
            f"{overview}\n",
            "- Critical Path:\n",
            *[f"{line}\n" for line in critical_path_lines],
            "- Data Sources & Sinks:\n",
            *[f"{line}\n" for line in data_points_lines],
            "- Technical Debt:\n",
            *[f"{line}\n" for line in technical_debt_lines],
            "- High-Velocity Core:\n",
            *[f"{line}\n" for line in high_velocity_lines],
        ]

        output_path = os.path.join(self.output_dir, "CODEBASE.md")
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("".join(output_lines))

        return output_path