# Codebase Cartography Report
## System Overview
- **Total Modules Scanned:** 1108
- **Lineage Connections:** 4577

## Top Architectural Hubs (PageRank)
- C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform\.pre-commit-config.yaml
- C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform\build.yaml
- C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform\docker-compose.yaml
- C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform\.gemini\config.yaml
- C:/Users/Yakob/Desktop/10 Academy/Week-4/cloned_repo_3/ol-data-platform\.github\workflows\project_automation.yaml

## Business Purpose Statements
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\dbt-create-staging-models.py**: This script automates the generation of dbt source YAML files based on a given schema and table prefix, facilitating data modeling and transformation within a dbt project.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\dbt-local-dev.py**: This script provides a command-line interface for local dbt development using DuckDB and Iceberg, enabling registration of AWS Glue Iceberg tables as DuckDB views, testing Glue/Iceberg connectivity, and cleaning up Trino development schemas.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\uv-operations.py**: This script automates the execution of 'uv' commands across multiple code repositories within a specified directory, streamlining dependency management and project maintenance.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\utils\chunk_tracking_logs_by_day.py**: This script reorganizes tracking log files in an S3 bucket by date, moving or copying them from the root of the source bucket to date-based prefixes in the destination bucket.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_deployments\reconcile_edxorg_partitions.py**: This script reconciles edxorg archive asset partitions and S3 objects with invalid course IDs caused by a parsing error, correcting S3 paths and re-emitting asset materializations under the canonical partition keys.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\__init__.py**: This file initializes the `dg_projects` package, likely setting up necessary configurations or importing modules to make the package functional.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\__init__.py**: This file initializes the `b2b_organization` package, likely setting up necessary configurations or importing modules to define the structure and functionality related to business-to-business organization management within the larger data platform.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\definitions.py**: This Dagster definitions file configures resources, assets, jobs, and sensors to orchestrate the export of B2B organization data to S3, handling Vault authentication and environment-specific bucket configurations.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\__init__.py**: This file initializes the `b2b_organization` Python package, likely setting up necessary configurations or importing modules for managing business-to-business organization-related functionalities.
- **C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\assets\data_export.py**: This asset exports data from a dbt model related to organization administration, filtering it by organization key, saving it to a CSV file, and yielding an output with metadata including a data version based on the file's SHA256 hash.
