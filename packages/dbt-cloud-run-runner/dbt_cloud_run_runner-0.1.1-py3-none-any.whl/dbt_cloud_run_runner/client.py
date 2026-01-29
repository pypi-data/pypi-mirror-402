"""
Client for running dbt projects on Google Cloud Run.
"""

import json
import os
import tempfile
import uuid
import zipfile
from datetime import timedelta
from pathlib import Path
from typing import Any, Optional

from google.cloud import storage
from google.cloud import run_v2

from .models import DbtCloudRunSetup, ExecutionStatus, ExecutionState


class Client:
    """
    Client for running dbt projects on Google Cloud Run.
    
    Example:
        client = Client(gcp_project="my-project", gcs_bucket="my-bucket")
        
        setup = client.prepare_bigquery(
            service_account_key={...},
            target_project="my-project",
            target_dataset="my_dataset",
            path_to_local_dbt_project="./my_dbt_project",
            image="gcr.io/my-project/dbt-runner:v1.0.0",
        )
        
        execution = client.run(setup)
        
        status = client.get_status(execution)
    """
    
    DEFAULT_JOB_NAME = "dbt-runner"
    DEFAULT_REGION = "us-central1"
    DEFAULT_URL_EXPIRATION_HOURS = 2
    
    def __init__(
        self,
        gcp_project: str,
        gcs_bucket: str,
        region: str = DEFAULT_REGION,
        job_name: str = DEFAULT_JOB_NAME,
    ):
        """
        Initialize the dbt Cloud Run runner client.
        
        Args:
            gcp_project: GCP project ID.
            gcs_bucket: GCS bucket name for storing dbt project and artifacts.
            region: GCP region for Cloud Run jobs (default: us-central1).
            job_name: Name for the Cloud Run job (default: dbt-runner).
        """
        self.gcp_project = gcp_project
        self.gcs_bucket = gcs_bucket
        self.region = region
        self.job_name = job_name
        
        # Initialize GCP clients
        self._storage_client: Optional[storage.Client] = None
        self._run_client: Optional[run_v2.JobsClient] = None
        self._executions_client: Optional[run_v2.ExecutionsClient] = None
    
    @property
    def storage_client(self) -> storage.Client:
        """Lazy-load the GCS client."""
        if self._storage_client is None:
            self._storage_client = storage.Client(project=self.gcp_project)
        return self._storage_client
    
    @property
    def run_client(self) -> run_v2.JobsClient:
        """Lazy-load the Cloud Run Jobs client."""
        if self._run_client is None:
            self._run_client = run_v2.JobsClient()
        return self._run_client
    
    @property
    def executions_client(self) -> run_v2.ExecutionsClient:
        """Lazy-load the Cloud Run Executions client."""
        if self._executions_client is None:
            self._executions_client = run_v2.ExecutionsClient()
        return self._executions_client
    
    def _generate_run_id(self) -> str:
        """Generate a unique run ID."""
        return uuid.uuid4().hex[:12]
    
    def _get_bucket(self) -> storage.Bucket:
        """Get the GCS bucket."""
        return self.storage_client.bucket(self.gcs_bucket)
    
    def _upload_blob(self, blob_path: str, content: bytes) -> storage.Blob:
        """Upload content to a GCS blob."""
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)
        blob.upload_from_string(content)
        return blob
    
    def _generate_signed_url(
        self,
        blob_path: str,
        method: str = "GET",
        expiration_hours: int = DEFAULT_URL_EXPIRATION_HOURS,
        content_type: Optional[str] = None,
    ) -> str:
        """Generate a signed URL for a GCS blob."""
        bucket = self._get_bucket()
        blob = bucket.blob(blob_path)
        
        kwargs: dict[str, Any] = {
            "version": "v4",
            "expiration": timedelta(hours=expiration_hours),
            "method": method,
        }
        
        if content_type and method == "PUT":
            kwargs["content_type"] = content_type
        
        return blob.generate_signed_url(**kwargs)
    
    def _zip_dbt_project(self, path_to_local_dbt_project: str) -> bytes:
        """
        Zip a dbt project directory, excluding the target/ directory.
        
        Args:
            path_to_local_dbt_project: Path to the local dbt project directory.
            
        Returns:
            Bytes of the zip file.
        """
        project_path = Path(path_to_local_dbt_project)
        
        if not project_path.exists():
            raise ValueError(f"dbt project path does not exist: {path_to_local_dbt_project}")
        
        if not project_path.is_dir():
            raise ValueError(f"dbt project path is not a directory: {path_to_local_dbt_project}")
        
        # Check for dbt_project.yml
        if not (project_path / "dbt_project.yml").exists():
            raise ValueError(
                f"No dbt_project.yml found in {path_to_local_dbt_project}. "
                "Is this a valid dbt project?"
            )
        
        # Directories and files to exclude
        exclude_dirs = {"target", ".git", "__pycache__", ".venv", "venv", "node_modules"}
        exclude_files = {".DS_Store"}
        
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(project_path):
                    # Modify dirs in-place to skip excluded directories
                    dirs[:] = [d for d in dirs if d not in exclude_dirs]
                    
                    for file in files:
                        if file in exclude_files:
                            continue
                        
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(project_path)
                        zf.write(file_path, arcname)
            
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            os.unlink(tmp_path)
    
    def _generate_bigquery_profiles_yml(
        self,
        service_account_key: dict[str, Any],
        target_project: str,
        target_dataset: str,
        profile_name: str = "default",
        location: str = "US",
    ) -> str:
        """
        Generate a profiles.yml content for BigQuery with embedded credentials.
        
        Uses OAuth via application default credentials, which will be set via
        GOOGLE_APPLICATION_CREDENTIALS environment variable pointing to a
        credentials file created by the entrypoint.
        
        Args:
            service_account_key: Service account key JSON as a dictionary (stored separately).
            target_project: BigQuery project ID.
            target_dataset: BigQuery dataset name.
            profile_name: dbt profile name (default: "default").
            location: BigQuery location (default: "US").
            
        Returns:
            profiles.yml content as a string.
        """
        import yaml
        
        # Build the profile structure using oauth method with application default credentials
        # The service account key will be passed via GOOGLE_APPLICATION_CREDENTIALS env var
        profile = {
            profile_name: {
                "outputs": {
                    "dev": {
                        "type": "bigquery",
                        "method": "oauth",
                        "project": target_project,
                        "dataset": target_dataset,
                        "location": location,
                        "priority": "interactive",
                        "timeout_seconds": 300,
                        "maximum_bytes_billed": 1000000000,
                    }
                },
                "target": "dev",
            }
        }
        
        return yaml.dump(profile, default_flow_style=False, allow_unicode=True)
    
    def prepare_bigquery(
        self,
        service_account_key: dict[str, Any],
        target_project: str,
        target_dataset: str,
        path_to_local_dbt_project: str,
        image: str,
        profile_name: Optional[str] = None,
        location: str = "US",
        url_expiration_hours: int = DEFAULT_URL_EXPIRATION_HOURS,
    ) -> DbtCloudRunSetup:
        """
        Prepare a dbt project for execution on Cloud Run with BigQuery.
        
        This method:
        1. Generates a profiles.yml with embedded BigQuery credentials
        2. Zips the dbt project (excluding target/ directory)
        3. Uploads both to GCS
        4. Generates signed URLs for the Cloud Run job
        
        Args:
            service_account_key: Service account key JSON as a dictionary.
            target_project: BigQuery project ID.
            target_dataset: BigQuery dataset name.
            path_to_local_dbt_project: Path to the local dbt project directory.
            image: Docker image to use for the Cloud Run job.
            profile_name: dbt profile name (defaults to project name from dbt_project.yml).
            location: BigQuery location (default: "US").
            url_expiration_hours: Expiration time for signed URLs (default: 2 hours).
            
        Returns:
            DbtCloudRunSetup with all the configuration needed to run the job.
        """
        run_id = self._generate_run_id()
        base_path = f"dbt-runs/{run_id}"
        
        # Read profile name from dbt_project.yml if not provided
        if profile_name is None:
            dbt_project_yml_path = Path(path_to_local_dbt_project) / "dbt_project.yml"
            if dbt_project_yml_path.exists():
                import yaml
                with open(dbt_project_yml_path) as f:
                    dbt_config = yaml.safe_load(f)
                    profile_name = dbt_config.get("profile", dbt_config.get("name", "default"))
            else:
                profile_name = "default"
        
        # Generate profiles.yml
        profiles_yml_content = self._generate_bigquery_profiles_yml(
            service_account_key=service_account_key,
            target_project=target_project,
            target_dataset=target_dataset,
            profile_name=profile_name,
            location=location,
        )
        
        # Zip the dbt project
        dbt_project_zip = self._zip_dbt_project(path_to_local_dbt_project)
        
        # Define blob paths
        profiles_yml_blob_path = f"{base_path}/profiles.yml"
        dbt_project_blob_path = f"{base_path}/dbt_project.zip"
        credentials_blob_path = f"{base_path}/credentials.json"
        output_blob_path = f"{base_path}/output.zip"
        logs_blob_path = f"{base_path}/logs.zip"
        
        # Upload to GCS
        self._upload_blob(profiles_yml_blob_path, profiles_yml_content.encode("utf-8"))
        self._upload_blob(dbt_project_blob_path, dbt_project_zip)
        self._upload_blob(credentials_blob_path, json.dumps(service_account_key).encode("utf-8"))
        
        # Generate signed URLs
        profiles_yml_url = self._generate_signed_url(
            profiles_yml_blob_path,
            method="GET",
            expiration_hours=url_expiration_hours,
        )
        dbt_project_url = self._generate_signed_url(
            dbt_project_blob_path,
            method="GET",
            expiration_hours=url_expiration_hours,
        )
        credentials_url = self._generate_signed_url(
            credentials_blob_path,
            method="GET",
            expiration_hours=url_expiration_hours,
        )
        output_url = self._generate_signed_url(
            output_blob_path,
            method="PUT",
            expiration_hours=url_expiration_hours,
            content_type="application/zip",
        )
        logs_url = self._generate_signed_url(
            logs_blob_path,
            method="PUT",
            expiration_hours=url_expiration_hours,
            content_type="application/zip",
        )
        
        return DbtCloudRunSetup(
            profiles_yml_blob=f"gs://{self.gcs_bucket}/{profiles_yml_blob_path}",
            dbt_project_blob=f"gs://{self.gcs_bucket}/{dbt_project_blob_path}",
            credentials_blob=f"gs://{self.gcs_bucket}/{credentials_blob_path}",
            output_blob=f"gs://{self.gcs_bucket}/{output_blob_path}",
            logs_blob=f"gs://{self.gcs_bucket}/{logs_blob_path}",
            profiles_yml_url=profiles_yml_url,
            dbt_project_url=dbt_project_url,
            credentials_url=credentials_url,
            output_url=output_url,
            logs_url=logs_url,
            image=image,
        )
    
    def _get_job_name_path(self) -> str:
        """Get the full resource path for the Cloud Run job."""
        return f"projects/{self.gcp_project}/locations/{self.region}/jobs/{self.job_name}"
    
    def _job_exists(self) -> bool:
        """Check if the Cloud Run job exists."""
        try:
            self.run_client.get_job(name=self._get_job_name_path())
            return True
        except Exception:
            return False
    
    def _create_job(self, image: str) -> None:
        """Create the Cloud Run job if it doesn't exist."""
        job = run_v2.Job(
            template=run_v2.ExecutionTemplate(
                template=run_v2.TaskTemplate(
                    containers=[
                        run_v2.Container(
                            image=image,
                            resources=run_v2.ResourceRequirements(
                                limits={"cpu": "2", "memory": "4Gi"},
                            ),
                        )
                    ],
                    timeout={"seconds": 3600},  # 1 hour timeout
                    max_retries=0,
                )
            )
        )
        
        request = run_v2.CreateJobRequest(
            parent=f"projects/{self.gcp_project}/locations/{self.region}",
            job=job,
            job_id=self.job_name,
        )
        
        operation = self.run_client.create_job(request=request)
        operation.result()  # Wait for the job to be created
    
    def _update_job_image(self, image: str) -> None:
        """Update the Cloud Run job with a new image."""
        job = self.run_client.get_job(name=self._get_job_name_path())
        
        # Update the container image
        job.template.template.containers[0].image = image
        
        request = run_v2.UpdateJobRequest(job=job)
        operation = self.run_client.update_job(request=request)
        operation.result()  # Wait for the update
    
    def run(self, setup: DbtCloudRunSetup) -> str:
        """
        Run a dbt project on Cloud Run.
        
        This method:
        1. Creates the Cloud Run job if it doesn't exist
        2. Updates the job with the correct image
        3. Runs the job with the environment variables from the setup
        
        Args:
            setup: DbtCloudRunSetup from prepare_bigquery().
            
        Returns:
            Execution ID that can be used with get_status().
        """
        # Ensure job exists
        if not self._job_exists():
            self._create_job(setup.image)
        else:
            # Update the image if needed
            self._update_job_image(setup.image)
        
        # Create an execution with the environment variables
        env_vars = [
            run_v2.EnvVar(name=name, value=value)
            for name, value in setup.to_env_vars().items()
        ]
        
        request = run_v2.RunJobRequest(
            name=self._get_job_name_path(),
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=env_vars,
                    )
                ]
            ),
        )
        
        operation = self.run_client.run_job(request=request)
        
        # Get the execution metadata from the operation without waiting for completion
        # The operation.metadata contains the execution info
        execution_metadata = operation.metadata
        
        # Extract execution ID from the full name in metadata
        # Format: projects/{project}/locations/{location}/jobs/{job}/executions/{execution_id}
        if hasattr(execution_metadata, 'name') and execution_metadata.name:
            execution_id = execution_metadata.name.split("/")[-1]
        else:
            # Fall back to waiting for operation if metadata doesn't have the name
            try:
                execution = operation.result()
                execution_id = execution.name.split("/")[-1]
            except Exception:
                # If the job failed, we can still extract the execution ID from the operation
                # by checking the metadata again or parsing the error
                raise
        
        return execution_id
    
    def get_status(self, execution_id: str) -> ExecutionStatus:
        """
        Get the status of a Cloud Run job execution.
        
        Args:
            execution_id: Execution ID from run().
            
        Returns:
            ExecutionStatus with the current state of the execution.
        """
        execution_path = f"{self._get_job_name_path()}/executions/{execution_id}"
        
        execution = self.executions_client.get_execution(name=execution_path)
        
        # Map Cloud Run conditions to our state enum
        state = ExecutionState.UNKNOWN
        error_message = None
        
        for condition in execution.conditions:
            if condition.type_ == "Completed":
                if condition.state == run_v2.Condition.State.CONDITION_SUCCEEDED:
                    state = ExecutionState.SUCCEEDED
                elif condition.state == run_v2.Condition.State.CONDITION_FAILED:
                    state = ExecutionState.FAILED
                    error_message = condition.message
                elif condition.state == run_v2.Condition.State.CONDITION_PENDING:
                    state = ExecutionState.PENDING
                elif condition.state == run_v2.Condition.State.CONDITION_RECONCILING:
                    state = ExecutionState.RUNNING
        
        # If no terminal condition, check if running
        if state == ExecutionState.UNKNOWN:
            if execution.running_count > 0:
                state = ExecutionState.RUNNING
            elif execution.succeeded_count > 0:
                state = ExecutionState.SUCCEEDED
            elif execution.failed_count > 0:
                state = ExecutionState.FAILED
            else:
                state = ExecutionState.PENDING
        
        return ExecutionStatus(
            execution_id=execution_id,
            state=state,
            create_time=execution.create_time,
            start_time=execution.start_time,
            completion_time=execution.completion_time,
            error_message=error_message,
        )
    
    def wait_for_completion(
        self,
        execution_id: str,
        poll_interval_seconds: float = 10.0,
        timeout_seconds: Optional[float] = None,
    ) -> ExecutionStatus:
        """
        Wait for a Cloud Run job execution to complete.
        
        Args:
            execution_id: Execution ID from run().
            poll_interval_seconds: Time between status checks (default: 10).
            timeout_seconds: Maximum time to wait (default: None = wait forever).
            
        Returns:
            ExecutionStatus with the final state of the execution.
            
        Raises:
            TimeoutError: If the execution doesn't complete within the timeout.
        """
        import time
        
        start_time = time.time()
        
        while True:
            status = self.get_status(execution_id)
            
            if status.is_terminal:
                return status
            
            if timeout_seconds is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    raise TimeoutError(
                        f"Execution {execution_id} did not complete within {timeout_seconds} seconds"
                    )
            
            time.sleep(poll_interval_seconds)
