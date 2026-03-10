# Phase 0: Reconnaissance Report - Jaffle Shop

**Target Repository:** https://github.com/dbt-labs/jaffle_shop
**Date:** March 10, 2026

### 1. Strategic FDE Analysis

**Question 1:** What is the primary data ingestion path?

- **Answer:** It's the seeds/ folder. The raw data starts as static CSV files (raw_customers.csv, etc.) which are loaded into the warehouse via the dbt seed command.

**Question 2:** What are the 3-5 most critical output datasets/endpoints?

- **Answer:** The "Marts" models. Specifically dim_customers and fct_orders. These are the final tables business users actually query.

**Question 3:** What is the blast radius if the most critical module fails?

- **Answer:** If stg_orders (staging) fails, it breaks fct_orders, which likely breaks every executive dashboard. The "blast radius" is high because it's a foundation-level transformation.

**Question 4:** Where is the business logic concentrated vs. distributed?

- **Answer:** It's distributed. Some logic is in SQL CASE statements in the models, but the "relationship" logic is concentrated in the schema.yml files (tests and refs).

**Question 5:** What has changed most frequently in the last 90 days (git velocity map)?

- **Answer:** Usually, it's the marts/ folder because business requirements change more often than staging logic.

### 2. Technical Onboarding Insights

- **The Entry Point:** `dbt_project.yml` and `profiles.yml`. These files define the project context and warehouse connections.
- **The Critical Path:** `seeds (CSVs)` → `stg_orders/customers` → `orders/customers (marts)`.
- **The Data Skeleton:** Core entities are `orders`, `customers`, and `payments`.
- **Hidden Dependencies:** Implicit links exist between `.sql` files and `.yml` configurations via the `{{ ref() }}` macro.
- **The Fragile Zone:** The `marts` models with complex joins and multiple `ref()` calls.

### 3. Difficulty Analysis & Architectural Priorities

- **The Manual Struggle:** Finding where a Python function actually calls a SQL model. In jaffle_shop, the connection is "hidden" inside YAML files or ref() functions.

- **Architectural Priority:** This tells me my Hydrologist Agent cannot just look at Python; it must have a "Stitcher" module that reads YAML to connect Python logic to SQL tables.

- **The Navigation Gap:** It was hard to see the "Big Picture" of how many times stg_customers is used across the whole repo without using grep multiple times.

- **Architectural Priority:** My Surveyor Agent needs to calculate Centrality (which files are imported the most) to highlight these "Hotspots" automatically.
