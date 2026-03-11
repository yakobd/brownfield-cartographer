# Phase 0: Reconnaissance Report - MIT Open Learning Data Platform

**Target Repository:**  https://github.com/mitodl/ol-data-platform
**Scale:** 1,108 Files | 858 Sources | 3,054 Sinks
**Date:** March 10, 2026

### 1. Strategic FDE Analysis

**Question 1:** What is the primary data ingestion path?

- **Answer:**  Ingestion is a hybrid of Python-based Airflow DAGs and dbt seeds. Raw event tracking logs (JSON/Parquet) are pulled from S3/GCS buckets. The orchestration/ directory acts as the traffic controller, feeding data into the staging/ dbt models for initial normalization.


**Question 2:** What are the 3-5 most critical output datasets/endpoints?

- **Answer:** 1. fct_user_activity: The backbone of engagement metrics. 2. dim_users: The primary identity dimension across MITx Online. 3. user_reporting: The warehouse layer specifically designed for executive dashboards. 4. int__mitx__courses: The intermediate layer that aggregates course metadata.

**Question 3:** What is the blast radius if the most critical module fails?

- **Answer:** Critical. My Hydrologist analysis identifies stg__mitxonline__openedx__tracking_logs__user_activity.sql as a "Super-Hub." Because it sits at the base of the transformation pyramid, a single schema change here invalidates over 3,054 downstream nodes. This represents a massive operational risk that manual auditing cannot track.

**Question 4:** Where is the business logic concentrated vs. distributed?

- **Answer:**  Logic is distributed and decoupled. Heavy transformations live in SQL (Jinja-templated), but the "When" and "How" are locked in Python Airflow operators and YAML configurations. This decoupling creates a "Visibility Gap" where it's hard to tell which Python script is responsible for which SQL table update

**Question 5:** What has changed most frequently in the last 90 days (git velocity map)?

- **Answer:** High velocity is observed in the transform/models/staging/mitxonline/ path. This suggests that the source systems (OpenEdX tracking logs) are frequently evolving, requiring constant patches to the staging layer to maintain data integrity.

### 2. Technical Onboarding Insights

- **Scale Complexity:** At 1,100+ files, the cognitive load is too high for a new engineer. Without an automated map, understanding why a change in src/ broke a report in marts/ takes hours of grep commands.
- **The "Dynamic" Problem:** Many SQL references are constructed via Jinja macros or Python f-strings. This means a simple text search won't find dependencies. The architecture demands a tool that can resolve these dynamic links.
- **Environment Isolation:** The use of multiple profiles (Production vs. QA) adds a layer of complexity to how lineage is calculated, as the "Source" might change depending on the runtime context.

### 3. Difficulty Analysis & Architectural Priorities

- **The Navigation Gap (The "So What?"):** Looking at a list of 1,000 files tells you nothing. The priority for the Surveyor Agent was to implement PageRank Centrality. By treating code imports like web links, we can automatically bubble up the "Top 10" most important files for a new engineer to read first.
- **The Parsing Challenge:** Standard SQL parsers fail on dbt's Jinja-heavy SQL. The Hydrologist Agent had to be built with a "Fallback Logic" (Postgres -> BigQuery -> Snowflake) to ensure that even if one dialect fails, the data flow is captured.
- **Data Integrity via Pydantic:** With 3,000+ sinks, a small error in the JSON structure would break the Phase 4 UI. A core architectural priority was using Pydantic Models to strictly validate every node and edge before it hits the disk.