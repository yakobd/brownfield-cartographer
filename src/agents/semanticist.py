import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from openai import OpenAI
from src.utils.budget import BudgetManager
import logging
logging.getLogger("root").setLevel(logging.ERROR)

load_dotenv()

class SemanticistAgent:
    def __init__(self):
        """Initializes OpenRouter via OpenAI client with safe fallback behavior."""
        load_dotenv()
        self.model_name = "google/gemini-pro-1.5" # For bulk
        self.synthesis_model = "openai/gpt-4o-mini" # For the Day-One Report
        self.budget = BudgetManager(limit_usd=2.00)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_referer = os.getenv("OPENROUTER_HTTP_REFERER", "https://brownfield-cartographer.local")
        self.openrouter_title = os.getenv("OPENROUTER_X_TITLE", "Brownfield Cartographer")
        self.client = None

        if not self.openrouter_api_key:
            print("CRITICAL: OPENROUTER_API_KEY not found in .env file.")
            self.embedding_model = None
            return

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.openrouter_api_key,
            default_headers={
                "HTTP-Referer": self.openrouter_referer,
                "X-Title": self.openrouter_title,
            },
        )

        try:
            print(f"✔ Semanticist: OpenRouter client initialized with model {self.model_name}.")
        except Exception as e:
            print(f"FAILED to initialize OpenRouter client: {e}")
            self.client = None

        self.embedding_model = None

    def _analysis_failed_payload(self) -> Dict:
        return {
            "purpose": "Analysis failed for this module.",
            "drift_detected": False,
            "drift_note": None,
        }

    def _analyze_module(self, file_path: str, code_content: str, docstring: Optional[str] = None) -> Dict:
        """Send module code to Gemini and return semantic_analysis payload."""
        if not self.client:
            return self._analysis_failed_payload()

        snippet = code_content[:5000]
        prompt = f"""Return ONLY raw JSON (no markdown, no prose) analyzing this code file: {file_path}
Existing docstring: {docstring if docstring else "None"}

    Critical instruction:
    - The provided code snippet is the ground truth.
    - Derive the business purpose from the actual code logic.
    - Use the docstring only as a secondary reference to assess documentation drift.

Required JSON keys:
"purpose": (A 1-sentence business purpose)
"drift_detected": (boolean)
"drift_note": (string or null)

Important output rule:
- Respond with JSON only. Do not include code fences or extra text.

Code:
{snippet}"""

        for attempt in range(1, 4):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": "System: You are a senior architect. Always respond in valid JSON.\n\nUser: " + prompt,
                        }
                    ],
                    temperature=0.1,
                )

                raw_content = (response.choices[0].message.content or "").strip()
                if not raw_content:
                    raise ValueError("Empty semantic_analysis response")

                self.budget.update_spend(prompt, raw_content)
                clean_json = raw_content.replace("```json", "").replace("```", "").strip()
                parsed = json.loads(clean_json)

                return {
                    "purpose": parsed.get("purpose", f"Logic for {os.path.basename(file_path)}"),
                    "drift_detected": bool(parsed.get("drift_detected", False)),
                    "drift_note": parsed.get("drift_note"),
                }
            except Exception as e:
                print(
                    f"DEBUG: Gemini semantic_analysis call failed for {file_path} "
                    f"(attempt {attempt}/3): {e}"
                )
                if attempt < 3:
                    time.sleep(2)

        return self._analysis_failed_payload()

    def generate_purpose_statement(self, file_path: str, code_content: str, docstring: Optional[str] = None) -> Dict:
        """Determines business purpose using OpenRouter with robust parsing and cleaning."""
        if self.budget.is_over_budget():
            print("WARNING: Semantic analysis skipped because budget is exceeded.")
            return {
                "purpose": "Budget Exceeded",
                "drift_detected": False,
                "drift_note": None,
            }

        if not self.client:
            return {"purpose": "API not initialized", "drift_detected": False, "drift_note": None}

        return self._analyze_module(file_path, code_content, docstring)
    def run_semantic_phase(self, nodes: List[Dict]) -> List[Dict]:
        """Processes the top 10 Hubs (filtering for .py files) to add semantic meaning."""
        if not self.client:
            return nodes

        # FILTER: Only target actual Python files to avoid analyzing config/yaml as "Business Logic"
        code_nodes = [n for n in nodes if n.get("id", "").endswith(".py")]
        
        # Only target the most important code files (Top PageRank Hubs)
        hubs = sorted(code_nodes, key=lambda x: x.get("pagerank", 0), reverse=True)[:10]
        
        for node in hubs:
            path = node.get("id")
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"--- Analyzing Hub: {path} ---")
                    result = self.generate_purpose_statement(path, content)
                    node["semantic_analysis"] = result
                    time.sleep(1)
        
        return nodes

    def cluster_into_domains(self, nodes: List[Dict]) -> List[Dict]:
        """Group semantic purpose statements into domains and annotate each node."""
        purpose_rows: List[Dict] = []

        for idx, node in enumerate(nodes):
            semantic = node.get("semantic_analysis") if isinstance(node, dict) else None
            if not isinstance(semantic, dict):
                continue
            purpose = semantic.get("purpose")
            if isinstance(purpose, str) and purpose.strip():
                purpose_rows.append({"node_index": idx, "purpose": purpose.strip()})

        if not purpose_rows:
            return nodes

        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        for embed_idx, row in enumerate(purpose_rows):
            row["embedding_index"] = embed_idx

        purpose_texts = [row["purpose"] for row in purpose_rows]
        embeddings = self.embedding_model.encode(purpose_texts, normalize_embeddings=True)

        purpose_count = len(purpose_rows)
        if purpose_count > 15:
            n_clusters = 8
        elif purpose_count >= 8:
            n_clusters = 5
        else:
            n_clusters = purpose_count
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
        labels = kmeans.fit_predict(embeddings)

        for i, label in enumerate(labels):
            purpose_rows[i]["cluster"] = int(label)

        cluster_labels: Dict[int, str] = {}
        for cluster_id in range(n_clusters):
            cluster_rows = [row for row in purpose_rows if row["cluster"] == cluster_id]
            if not cluster_rows:
                continue

            centroid = kmeans.cluster_centers_[cluster_id]
            ranked_rows = sorted(
                cluster_rows,
                key=lambda row: sum(
                    (embeddings[row["embedding_index"]][dim] - centroid[dim]) ** 2
                    for dim in range(len(centroid))
                ),
            )
            top_purposes = [row["purpose"] for row in ranked_rows[:3]]
            domain_label = self._label_cluster_domain(top_purposes, cluster_id)
            cluster_labels[cluster_id] = domain_label

        for row in purpose_rows:
            node_idx = row["node_index"]
            cluster_id = row["cluster"]
            nodes[node_idx]["domain"] = cluster_labels.get(cluster_id, f"Domain{cluster_id + 1}")

        return nodes

    def _label_cluster_domain(self, top_purposes: List[str], cluster_id: int) -> str:
        """Ask Gemini for a one-word cluster label."""
        if not self.client:
            return f"Domain{cluster_id + 1}"

        prompt = f"""
You are labeling a software domain cluster.
Top 3 purpose statements:
{json.dumps(top_purposes, indent=2)}
Return only one word that best names the domain (e.g., Ingestion, Transformation).
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": "System: Return exactly one word.\n\nUser: " + prompt,
                    },
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            label = content.split()[0] if content else ""
            label = "".join(ch for ch in label if ch.isalpha())
            return label or f"Domain{cluster_id + 1}"
        except Exception:
            return f"Domain{cluster_id + 1}"

    def generate_fde_report(self, nodes: List[Dict], output_dir: str | Path = ".cartography") -> str:
        """Create a concise Day-One FDE report using evidence-grounded hub context."""
        output_path_root = Path(output_dir).resolve()
        output_path_root.mkdir(parents=True, exist_ok=True)

        code_nodes = [n for n in nodes if n.get("id", "").endswith(".py")]
        top_hubs = sorted(code_nodes, key=lambda x: x.get("pagerank", 0), reverse=True)[:10]

        hub_summaries: List[str] = []
        for node in top_hubs:
            node_id = str(node.get("id", "unknown"))
            semantic = node.get("semantic_analysis") if isinstance(node, dict) else None
            purpose = semantic.get("purpose", "No purpose available") if isinstance(semantic, dict) else "No purpose available"
            hub_summaries.append(f"- {node_id}: {purpose}")

        codebase_path = output_path_root / "CODEBASE.md"
        with open(codebase_path, "w", encoding="utf-8") as codebase_file:
            codebase_file.write("# Codebase Hub Summaries\n\n")
            codebase_file.write("\n\n".join(hub_summaries) + "\n")

        domain_groups: Dict[str, List[str]] = {}
        for node in nodes:
            domain = node.get("domain")
            if domain:
                domain_groups.setdefault(domain, []).append(str(node.get("id", "unknown")))

        if domain_groups:
            domain_summary_lines = [f"- {d}: {len(ids)} files (e.g., {ids[0]})" for d, ids in domain_groups.items()]
            domain_summary = "\n".join(domain_summary_lines)
        else:
            domain_summary = "- No domain clusters available."

        drift_nodes = [n.get("id") for n in nodes if isinstance(n.get("semantic_analysis"), dict) and n["semantic_analysis"].get("drift_detected")]
        drift_summary = ", ".join(drift_nodes[:10]) if drift_nodes else "None detected"

        prompt = f"""
You are a Senior Forward Deployed Engineer onboarding onto this codebase.
Hub summaries with semantic purpose statements:
{chr(10).join(hub_summaries)}
Domain Cluster Summary:
{domain_summary}
Drift: {drift_summary}

    Produce a concise, high-leverage Markdown report.
    Output ONLY the 5 Day-One questions below, each followed by:
    - Exactly 2 short analysis paragraphs.
    - A bullet list named "Evidence" containing supporting citations.

    You MUST provide evidence for every claim using specific file paths and line numbers from the provided context.
    Use this citation format: path/to/file.py:L45

    Answer these exact 5 FDE Day-One questions:
    1. What is the primary data ingestion path?
    2. What are the 3-5 most critical output datasets/endpoints?
    3. What is the blast radius if the most critical module fails?
    4. Where is the business logic concentrated vs. distributed?
    5. What has changed most frequently in the last 90 days?
"""
        report_body: str | None = None
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                if not self.client:
                    raise RuntimeError("OpenRouter client not initialized")

                response = self.client.chat.completions.create(
                    model=self.synthesis_model,
                    messages=[
                        {
                            "role": "user",
                            "content": "System: You are a Senior Forward Deployed Engineer producing concise onboarding analysis.\n\nUser: " + prompt,
                        },
                    ],
                )
                report_body = (response.choices[0].message.content or "").strip()
                if not report_body:
                    raise ValueError("Empty FDE synthesis response")
                break
            except Exception as e:
                last_error = e
                print(f"CRITICAL: FDE Synthesis failed with error: {e} (attempt {attempt}/3)")
                if attempt < 3:
                    time.sleep(2)

        if not report_body:
            report_body = (
                "FDE synthesis failed after 3 attempts. "
                "Please check OpenRouter availability and API configuration."
            )
            if last_error is not None:
                report_body += f"\n\nLast error: {last_error}"

        report_path = output_path_root / "ONBOARDING_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# FDE Onboarding Report\n\n")
            f.write(report_body + "\n")

        return str(report_path)