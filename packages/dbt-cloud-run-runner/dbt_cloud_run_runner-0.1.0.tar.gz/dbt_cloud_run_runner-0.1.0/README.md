# dbt-cloud-run-runner

A Python client library for running dbt projects on Google Cloud Run.

## Installation

```bash
pip install dbt-cloud-run-runner
```

## Usage

```python
from dbt_cloud_run_runner import Client

# Initialize the client
client = Client(
    gcp_project="your-gcp-project",
    gcs_bucket="your-gcs-bucket",
    region="us-central1",  # optional, defaults to us-central1
)

# Prepare a dbt project for BigQuery
setup = client.prepare_bigquery(
    service_account_key={"type": "service_account", ...},  # Your service account key JSON
    target_project="your-bigquery-project",
    target_dataset="your_dataset",
    path_to_local_dbt_project="./path/to/dbt/project",
    image="us-docker.pkg.dev/delphiio-prod/public-images/dbt-runner:v0.0.7",
)

# Run the dbt project on Cloud Run
execution_id = client.run(setup)
print(f"Execution started: {execution_id}")

# Wait for completion
status = client.wait_for_completion(execution_id)
print(f"Execution finished with state: {status.state.value}")

# Or poll status manually
status = client.get_status(execution_id)
print(f"Current state: {status.state.value}")
```

## Features

- **Automatic GCS setup**: Uploads your dbt project and credentials to GCS with signed URLs
- **Cloud Run job management**: Creates and manages Cloud Run jobs automatically
- **BigQuery integration**: Generates `profiles.yml` for BigQuery targets
- **Status monitoring**: Track execution status with polling or wait for completion

## Requirements

- Python 3.9+
- Google Cloud project with Cloud Run and GCS enabled
- Service account with appropriate permissions:
  - Cloud Run Admin (`roles/run.admin`)
  - Storage Admin (`roles/storage.admin`) on the GCS bucket
  - BigQuery access for the target project/dataset
