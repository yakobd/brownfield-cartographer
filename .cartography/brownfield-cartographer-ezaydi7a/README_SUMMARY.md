# Codebase Cartography Report
## System Overview
- **Total Modules Scanned:** 28
- **Lineage Connections:** 0

## Top Architectural Hubs (PageRank)
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\check_db.py
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\run_refinery.py
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_phase_3.py
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_pipeline.py
- C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_rag_search.py

## Business Purpose Statements
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\check_db.py**: This script checks the ChromaDB vector database located in the .refinery directory, lists the collections, and prints the number of chunks and a sample text from each collection if it's not empty.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\run_refinery.py**: This script automates the process of extracting information from a PDF document, chunking it semantically, indexing it for efficient retrieval, and extracting facts into a SQLite database, enabling question answering and knowledge discovery.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_phase_3.py**: This script performs an end-to-end test of a document processing pipeline, including triage, extraction, chunking, and indexing of a PDF document, and verifies the integrity of the generated chunks.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_pipeline.py**: This code defines and tests a strategy (StrategyC) for extracting information from documents, focusing on budget constraints and output structure.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\test_rag_search.py**: This script performs a Retrieval-Augmented Generation (RAG) search on a PDF document, using semantic chunking, document indexing, and vector storage to retrieve relevant information based on a user query, with an optional page filtering step based on a hierarchical page index.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\validate_mastery.py**: This script validates the functionality of document triage and extraction processes by analyzing a PDF, profiling it using a TriageAgent, extracting data using an ExtractionRouter, and verifying the extraction ledger.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\research\density_check.py**: This script analyzes the first page of a list of PDF files to extract text and image information, calculate character density, and heuristically detect the possible presence of stamps or handwriting.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\research\docling_test.py**: The code tests the docling library by converting a PDF document to Markdown, analyzing the extracted content (specifically tables), and saving the Markdown output to a file.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\agents\chunker.py**: This code defines classes to validate and convert raw extraction segments from a document into structured LDU (Logical Document Unit) objects, ensuring data integrity and consistency.
- **C:\Users\Yakob\AppData\Local\Temp\brownfield-cartographer-ezaydi7a\src\agents\domain_classifier.py**: This code defines a domain classifier that uses keywords to categorize text into specific domains and provides a confidence score for the classification.
