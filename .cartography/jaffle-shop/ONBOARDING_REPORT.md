# FDE Onboarding Report

## FDE Day-One Onboarding Report

**1. What is the primary data ingestion path?**

Based on the provided context, there's insufficient information to determine the primary data ingestion path. The provided script focuses on triggering and monitoring dbt Cloud jobs, not the initial ingestion of data into the system. More context regarding the data sources and upstream processes feeding into dbt Cloud is required.

The script's purpose is to orchestrate the execution of dbt Cloud jobs, suggesting that the data ingestion happens before this step, as dbt transforms data already in a database or data warehouse. Therefore, the actual data ingestion path lies outside of the scope of this isolated script focusing on dbt Cloud job orchestration.

*Evidence*
*   C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\scripts\dbt_cloud_run_job.py: The script focuses on triggering and monitoring an already running dbt Cloud job.

**2. What are the 3-5 most critical output datasets/endpoints?**

Again, based solely on the given context, identifying the critical output datasets/endpoints is impossible. The script doesn't define or interact with specific datasets directly. Its role is purely operational, monitoring dbt Cloud job runs and reporting their status.

To determine the critical datasets, we'd need to understand the dbt Cloud jobs that are being triggered. What models are being built? What databases are they targeting? Without this additional context, it's impossible to identify the most vital output datasets.

*Evidence*
*   C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\scripts\dbt_cloud_run_job.py: The script's sole function is to trigger and monitor a dbt Cloud job and has no knowledge of the underlying data.

**3. What is the blast radius if the most critical module fails?**

If the `dbt_cloud_run_job.py` script fails, the immediate blast radius is limited to the orchestration pipeline. This means dbt Cloud jobs might not be triggered or monitored correctly. The delayed or absent feedback loop will disrupt the intended reporting to those awaiting the job run information.

The secondary effect is potentially more significant: if dbt Cloud jobs are not triggered or monitored appropriately, data transformations might be delayed or fail silently, leading to stale or inaccurate data in downstream systems. This could affect decision-making processes relying on the transformed data. The blast radius therefore encompasses any system depending on the successful completion of the scheduled dbt Cloud job.

*Evidence*
*   C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\scripts\dbt_cloud_run_job.py: Failure of the tool causes missed dbt Cloud job triggers, monitoring, and reporting.

**4. Where is the business logic concentrated vs. distributed?**

The provided script contains minimal business logic. Its primary function is to interact with the dbt Cloud API. Any core business logic would reside within the dbt Cloud project itself, specifically within the dbt models (SQL transformations) that the triggered job executes.

The orchestration aspect is centralized in this script, but the actual data transformations and business rules are distributed within the dbt Cloud project. To understand specifically *where* the business logic lives, further dbt project files would need to be examined.

*Evidence*
*   C:\Users\Yakob\Desktop\10 Academy\Week-4\cloned_repo_2\jaffle-shop\.github\workflows\scripts\dbt_cloud_run_job.py: Limited to triggering and monitoring functionalities and contains trivial business logic.

**5. What has changed most frequently in the last 90 days?**

Based on the limited information provided, It's impossible to determine exactly which part of the system has changed most frequently. The script's stability depends on the stability of the dbt Cloud API and the requirements of the orchestration pipeline it serves.

However, given the nature of data transformation projects, it is more likely that the *dbt Models* have changed substantially more frequently than the orchestration script. Data requirements and logic will likely be evolving at a fast pace compared to job orchestration/triggering. But, with only this orchestration script to look at, no factual claims can be made.

*Evidence*
*   No data about change frequency is available.
