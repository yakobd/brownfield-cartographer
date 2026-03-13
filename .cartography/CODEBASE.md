# Codebase Hub Summaries

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\dbt-create-staging-models.py: This script automates the generation of dbt source YAML files based on a given schema and table prefix, facilitating data modeling and transformation within a dbt project.
  First 50 lines:
1: #!/usr/bin/env python3
2: # ruff: noqa: T201, BLE001, UP045
3: """
4: This script provides commands to generate dbt sources and staging models.
5: It interacts with dbt to discover tables and generate the necessary YAML and SQL files.
6: """
7: 
8: import json
9: import re
10: import subprocess
11: from pathlib import Path
12: from typing import Optional
13: 
14: import yaml
15: from cyclopts import App
16: 
17: app = App()
18: 
19: 
20: def extract_domain_from_prefix(prefix: str) -> str:
21:     """
22:     Extract the domain (second section) from a table prefix.
23: 
24:     Args:
25:         prefix: The table prefix (e.g., 'raw__mitlearn__app__postgres__')
26: 
27:     Returns:
28:         The domain name (e.g., 'mitlearn')
29:     """
30:     parts = prefix.split("__")
31:     if len(parts) >= 2:  # noqa: PLR2004
32:         return parts[1]
33:     return ""
34: 
35: 
36: def run_dbt_command(
37:     dbt_project_dir: str, command: list[str], target: Optional[str]
38: ) -> subprocess.CompletedProcess[str]:
39:     """
40:     Run a dbt command and captures its output.
41: 
42:     Args:
43:         dbt_project_dir: The directory of the dbt project.
44:         command: A list of strings representing the dbt command and its arguments.
45:         target: The dbt target to use.
46: 
47:     Returns:
48:         A CompletedProcess object containing the result of the dbt command.
49:     """
50:     # Check if this is a regular dbt command or a run-operation command

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\dbt-local-dev.py: This script provides a command-line interface for local dbt development using DuckDB and Iceberg, enabling registration of AWS Glue Iceberg tables as DuckDB views, testing Glue/Iceberg connectivity, and cleaning up Trino development schemas.
  First 50 lines:
1: #!/usr/bin/env python3
2: # ruff: noqa: T201, FBT001, FBT002, S608, BLE001, C901, PLR0912, PLR0913, PLR0915, E501, RUF059, PT028, PLC0415, PLR2004, S607, RUF001
3: """
4: CLI tool for local dbt development with DuckDB + Iceberg.
5: 
6: This unified CLI provides commands for:
7: - Registering AWS Glue Iceberg tables as DuckDB views
8: - Testing Glue/Iceberg connectivity
9: - Cleaning up Trino development schemas
10: 
11: Usage:
12:     # Register all Iceberg tables from AWS Glue
13:     python bin/dbt-local-dev.py register --all-layers
14: 
15:     # Test Glue/Iceberg connectivity
16:     python bin/dbt-local-dev.py test
17: 
18:     # Clean up Trino dev schemas
19:     python bin/dbt-local-dev.py cleanup --target dev_production --execute
20: 
21:     # Show help
22:     python bin/dbt-local-dev.py --help
23: """
24: 
25: import os
26: import sys
27: from concurrent.futures import ThreadPoolExecutor, as_completed
28: from pathlib import Path
29: from threading import Lock
30: from typing import Annotated, Any, Literal
31: 
32: import boto3
33: import cyclopts
34: import duckdb
35: import trino
36: from trino.auth import OAuth2Authentication
37: 
38: # ============================================================================
39: # Constants and Configuration
40: # ============================================================================
41: 
42: DEFAULT_DUCKDB_PATH = Path.home() / ".ol-dbt" / "local.duckdb"
43: DEFAULT_GLUE_DATABASE = "ol_warehouse_production_raw"
44: 
45: # Standard dbt layer databases (in dependency order)
46: LAYER_DATABASES = [
47:     "ol_warehouse_production_raw",
48:     "ol_warehouse_production_staging",
49:     "ol_warehouse_production_intermediate",
50:     "ol_warehouse_production_dimensional",

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\uv-operations.py: This script automates the execution of 'uv' commands across multiple code repositories within a specified directory, streamlining dependency management and other project-related tasks.
  First 50 lines:
1: #!/usr/bin/env python3
2: # ruff: noqa: T201
3: """
4: Script to run uv commands across all code locations in the dg_projects directory.
5: 
6: This script discovers all directories containing a pyproject.toml file and executes
7: the specified uv command on each one.
8: """
9: 
10: import subprocess
11: import sys
12: from pathlib import Path
13: from typing import Annotated
14: 
15: from cyclopts import App, Parameter
16: 
17: app = App(help="Run uv commands across all code locations")
18: 
19: 
20: class Colors:
21:     """ANSI color codes for terminal output."""
22: 
23:     GREEN = "\033[0;32m"
24:     BLUE = "\033[0;34m"
25:     RED = "\033[0;31m"
26:     YELLOW = "\033[1;33m"
27:     NC = "\033[0m"  # No Color
28: 
29: 
30: def find_code_locations(base_dir: Path) -> list[Path]:
31:     """
32:     Find all directories containing a pyproject.toml file.
33: 
34:     Args:
35:         base_dir: The base directory to search for code locations.
36: 
37:     Returns:
38:         A sorted list of Path objects for each code location.
39:     """
40:     locations = []
41:     for item in base_dir.iterdir():
42:         if item.is_dir() and (item / "pyproject.toml").exists():
43:             locations.append(item)  # noqa: PERF401
44:     return sorted(locations)
45: 
46: 
47: def run_uv_command(location: Path, uv_args: list[str], verbose: bool = False) -> bool:  # noqa: FBT001, FBT002
48:     """
49:     Run uv command in the specified location.
50: 

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\bin\utils\chunk_tracking_logs_by_day.py: This script reorganizes tracking log files in an S3 bucket by date, moving or copying them from the root to date-based subdirectories within the destination bucket.
  First 50 lines:
1: #!/usr/bin/env python
2: """
3: Our tracking logs have gone through a few iterations of methods for loading them to S3.
4: This is largely due to different agents being used for shipping the logs.  As a result,
5: the path formatting for those logs is not consistent across time boundaries.
6: 
7: This script is designed to take a source bucket and a destination bucket, and process
8: all files that are in the root of the bucket to be located in path prefixes that are
9: chunked by date.
10: """
11: 
12: import sys
13: from datetime import UTC, datetime, timedelta
14: from typing import Annotated
15: 
16: import typer
17: from boto3 import client, resource
18: 
19: 
20: def date_chunk_files(  # noqa: PLR0913
21:     source_bucket: Annotated[
22:         str,
23:         typer.Argument(
24:             help="The source bucket that tracking logs will be copied or moved from"
25:         ),
26:     ],
27:     dest_bucket: Annotated[
28:         str, typer.Argument(help="The bucket that the tracking logs will be written to")
29:     ],
30:     start_date: Annotated[
31:         str,
32:         typer.Option(
33:             help="The date of the earliest tracking log to process "
34:             "(based on the formatted file name). In %Y-%m-%d format"
35:         ),
36:     ] = "2017-01-01",
37:     end_date: Annotated[
38:         str | None,
39:         typer.Option(
40:             help="The date of the last tracking log to process "
41:             "(based on the formatted file name). In %Y-%m-%d format"
42:         ),
43:     ] = None,
44:     dry_run: Annotated[  # noqa: FBT002
45:         bool,
46:         typer.Option(
47:             help="Set to True to just see what the source and destination paths "
48:             "will be without performing any modifications"
49:         ),
50:     ] = True,

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_deployments\reconcile_edxorg_partitions.py: This script reconciles edxorg archive asset partitions and S3 objects with invalid course IDs caused by a parsing error, correcting S3 paths and re-emitting asset materializations under the canonical partition keys.
  First 50 lines:
1: # ruff: noqa: INP001
2: """Reconcile edxorg archive asset partitions and S3 objects with invalid course IDs.
3: 
4: Partitions created between commit 2c2b9c3a (2026-02-11) and the subsequent fix
5: have course_id values that incorrectly include a data-type suffix:
6: 
7:   Bad:       MITx-15.415x-3T2018-course|edge
8:   Canonical: MITx-15.415x-3T2018|edge
9: 
10: This arises because ``parse_archive_path`` was not consuming the ``-course`` /
11: ``-course_structure`` token that appears between the course run and the source-
12: system marker in ``.json`` archive filenames, so the regex engine absorbed it
13: into the course_id instead.
14: 
15: Impact by asset type
16: --------------------
17: * **course_structure** (``.json``) - wrong course_id in the S3 path AND the
18:   partition key.  Object keys look like::
19: 
20:       edxorg/raw_data/course_structure/edge/MITx-15.415x-3T2018-course/<hash>.json
21: 
22:   These must be S3-copied to the canonical path *and* re-emitted with the
23:   correct partition key and path metadata.
24: 
25: * **course_xml** (``.xml.tar.gz``) - same S3 path problem (the ``-course``
26:   suffix in the filename was absorbed into course_id by the pre-existing regex
27:   before 2c2b9c3a *and* continued afterwards).
28: 
29: * **db_table** (``.sql``) - course_id was always parsed correctly (the table-
30:   name token was consumed by ``DATA_ATTRIBUTE_REGEX``), so **no S3 correction
31:   is needed**.
32: 
33: * **forum_mongo** (``.mongo``) - filenames never carry a suffix before the
34:   source-system marker, so course_id was always correct; **no S3 correction
35:   needed**.
36: 
37: What this script does
38: ---------------------
39: 1. Lists all dynamic partition keys for ``course_and_source``.
40: 2. Identifies keys whose course_id component ends in ``-course`` or
41:    ``-course_structure``.
42: 3. Adds the canonical (suffix-stripped) partition key if not already present.
43: 4. For every asset materialisation event under the bad partition key:
44: 
45:    a. Inspects the ``object_key`` metadata field.
46:    b. If that key embeds the wrong course_id as a path segment, S3-copies the
47:       object to the corrected path (skipped if the destination already exists).
48:    c. Re-emits an ``AssetMaterialisation`` under the canonical partition key
49:       with updated ``object_key``, ``path``, and ``course_id`` metadata.
50: 

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\__init__.py: This file initializes the `dg_projects` package, likely setting up necessary configurations or importing modules for use within the package.
  First 50 lines:


- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\__init__.py: This file initializes the `b2b_organization` package, likely setting up necessary configurations or importing modules to define the structure and functionality related to business-to-business organization management within the larger data platform.
  First 50 lines:


- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\definitions.py: This Dagster definitions file configures resources, assets, jobs, and sensors to orchestrate the export of B2B organization data to S3, handling Vault authentication and environment-specific bucket configurations.
  First 50 lines:
1: from b2b_organization.assets.data_export import export_b2b_organization_data
2: from b2b_organization.sensors.b2b_organization import b2b_organization_list_sensor
3: from dagster import (
4:     Definitions,
5:     define_asset_job,
6: )
7: from dagster_aws.s3 import S3Resource
8: from ol_orchestrate.lib.constants import DAGSTER_ENV, VAULT_ADDRESS
9: from ol_orchestrate.lib.dagster_helpers import (
10:     default_file_object_io_manager,
11:     default_io_manager,
12: )
13: from ol_orchestrate.lib.utils import authenticate_vault
14: 
15: b2b_bucket_map = {
16:     "dev": {"bucket": "ol-devops-sandbox", "prefix": "pipeline-storage"},
17:     "ci": {"bucket": "ol-b2b-partners-storage-ci", "prefix": ""},
18:     "qa": {"bucket": "ol-b2b-partners-storage-qa", "prefix": ""},
19:     "production": {"bucket": "ol-b2b-partners-storage-production", "prefix": ""},
20: }
21: 
22: # Initialize vault with resilient loading
23: try:
24:     vault = authenticate_vault(DAGSTER_ENV, VAULT_ADDRESS)
25:     vault_authenticated = True
26: except Exception as e:  # noqa: BLE001 (resilient loading)
27:     import warnings
28: 
29:     from ol_orchestrate.resources.secrets.vault import Vault
30: 
31:     warnings.warn(
32:         f"Failed to authenticate with Vault: {e}. Using mock configuration.",
33:         stacklevel=2,
34:     )
35:     vault = Vault(vault_addr=VAULT_ADDRESS, vault_auth_type="github")
36:     vault_authenticated = False
37: 
38: 
39: b2b_organization_data_export_job = define_asset_job(
40:     name="b2b_organization_data_export_job",
41:     selection=[export_b2b_organization_data],
42: )
43: 
44: # Create unified definitions
45: defs = Definitions(
46:     resources={
47:         "io_manager": default_io_manager(DAGSTER_ENV),
48:         "s3file_io_manager": default_file_object_io_manager(
49:             dagster_env=DAGSTER_ENV,
50:             bucket=b2b_bucket_map[DAGSTER_ENV]["bucket"],

- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\__init__.py: This file initializes the `b2b_organization` Python package, likely setting up necessary configurations or importing modules for managing business-to-business organization-related functionalities.
  First 50 lines:


- C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_3\ol-data-platform\dg_projects\b2b_organization\b2b_organization\assets\data_export.py: This asset exports data from a dbt model related to organization administration, filtering it by organization key, saving it to a CSV file, and yielding an output with metadata including a data version based on the file's SHA256 hash.
  First 50 lines:
1: import hashlib
2: from datetime import UTC, datetime
3: from pathlib import Path
4: 
5: import polars as pl
6: from b2b_organization.partitions.b2b_organization import (
7:     b2b_organization_list_partitions,
8: )
9: from dagster import (
10:     AssetExecutionContext,
11:     AssetKey,
12:     DataVersion,
13:     Output,
14:     asset,
15: )
16: from ol_orchestrate.lib.glue_helper import get_dbt_model_as_dataframe
17: 
18: 
19: @asset(
20:     code_version="b2b_organization_data_export_v1",
21:     group_name="b2b_organization",
22:     deps=[AssetKey(["reporting", "organization_administration_report"])],
23:     partitions_def=b2b_organization_list_partitions,
24:     io_manager_key="s3file_io_manager",
25:     key=AssetKey(["b2b_organization", "administration_report_export"]),
26: )
27: def export_b2b_organization_data(context: AssetExecutionContext):
28:     organization_key = context.partition_key
29:     dbt_report_name = "organization_administration_report"
30: 
31:     data_df = get_dbt_model_as_dataframe(
32:         database_name="ol_warehouse_production_reporting",
33:         table_name=dbt_report_name,
34:     )
35:     organizational_data_df = data_df.filter(
36:         pl.col("organization_key").eq(organization_key)
37:     )
38:     num_rows = organizational_data_df.select(pl.len()).collect().item()
39:     context.log.info(
40:         "%d rows in organization_administration_report for %s",
41:         num_rows,
42:         organization_key,
43:     )
44: 
45:     export_date = datetime.now(tz=UTC).strftime("%Y-%m-%d")
46: 
47:     organizational_data_file = Path(
48:         f"{organization_key}_{dbt_report_name}_{export_date}.csv"
49:     )
50:     organizational_data_df.sink_csv(str(organizational_data_file))
