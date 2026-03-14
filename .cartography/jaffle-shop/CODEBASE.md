# CODEBASE
Architecture Overview:
This CODEBASE summary combines module structure and lineage metadata to highlight where the system's architecture is concentrated, how data flows from ingestion to sink points, and where operational risk is likely to accumulate due to dependency complexity, documentation drift, or high change velocity.
- Critical Path:
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.pre-commit-config.yaml (PageRank: 0.000000)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\dbt_project.yml (PageRank: 0.000000)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\package-lock.yml (PageRank: 0.000000)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\packages.yml (PageRank: 0.000000)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\Taskfile.yml (PageRank: 0.000000)
- Data Sources & Sinks:
Ingestion points:
- source:ecom
Output points:
- sink:count_lifetime_orders
- sink:customer_id
- sink:customer_name
- sink:customer_type
- sink:customers
- sink:first_ordered_at
- sink:is_drink_order
- sink:is_food_order
- sink:last_ordered_at
- sink:lifetime_spend
- sink:lifetime_spend_pretax
- sink:lifetime_tax_paid
- sink:location_id
- sink:order_cost
- sink:order_id
- sink:order_item_id
- sink:order_items
- sink:order_total
- sink:ordered_at
- sink:orders
- sink:product_id
- sink:stg_customers
- sink:stg_locations
- sink:stg_order_items
- sink:stg_orders
- sink:stg_products
- sink:stg_supplies
- sink:supply_uuid
- Technical Debt:
Circular dependencies:
- None detected
Documentation Drift flags:
- None detected
- High-Velocity Core:
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.pre-commit-config.yaml (change_frequency: 1)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\packages.yml (change_frequency: 1)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\dbt_project.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\package-lock.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\Taskfile.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\cd_prod.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\cd_staging.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\ci.yml (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\scripts\dbt_cloud_run_job.py (change_frequency: 0)
- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\macros\cents_to_dollars.sql (change_frequency: 0)
