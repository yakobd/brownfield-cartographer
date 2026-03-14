# CODEBASE
Architecture Overview:
This CODEBASE summary combines module structure and lineage metadata to highlight where the system's architecture is concentrated, how data flows from ingestion to sink points, and where operational risk is likely to accumulate due to dependency complexity, documentation drift, or high change velocity.
- Critical Path:
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\check_db.py (PageRank: 0.000000)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\run_refinery.py (PageRank: 0.000000)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_phase_3.py (PageRank: 0.000000)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_pipeline.py (PageRank: 0.000000)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_rag_search.py (PageRank: 0.000000)
- Data Sources & Sinks:
Ingestion points:
- None detected
Output points:
- None detected
- Technical Debt:
Circular dependencies:
- None detected
Documentation Drift flags:
- None detected
- High-Velocity Core:
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\models\document_schema.py (change_frequency: 6)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\rubric\extraction_rules.yaml (change_frequency: 5)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\agents\extractor.py (change_frequency: 5)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\agents\triage.py (change_frequency: 5)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\strategies\vision_extractor.py (change_frequency: 5)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\utils\config_loader.py (change_frequency: 4)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\strategies\fast_text_extractor.py (change_frequency: 3)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\strategies\layout_extractor.py (change_frequency: 3)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\engines\indexer.py (change_frequency: 2)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\engines\vector_store.py (change_frequency: 2)
