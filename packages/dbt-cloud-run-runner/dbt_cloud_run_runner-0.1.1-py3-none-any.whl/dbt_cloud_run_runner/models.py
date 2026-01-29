"""
Data models for dbt-cloud-run-runner.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime


class ExecutionState(Enum):
    """State of a Cloud Run job execution."""
    
    UNKNOWN = "UNKNOWN"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class DbtCloudRunSetup:
    """
    Configuration for a dbt Cloud Run execution.
    
    Contains the GCS blob paths and signed URLs needed to run dbt.
    """
    
    # GCS blob paths (gs://bucket/path format)
    profiles_yml_blob: str
    dbt_project_blob: str
    credentials_blob: str
    output_blob: str
    logs_blob: str
    
    # Pre-signed URLs for the Docker container
    profiles_yml_url: str
    dbt_project_url: str
    credentials_url: str
    output_url: str
    logs_url: str
    
    # Docker image to use
    image: str
    
    def to_env_vars(self) -> dict[str, str]:
        """Return environment variables for the Cloud Run job."""
        return {
            "DBT_PROJECT_URL": self.dbt_project_url,
            "PROFILE_YML": self.profiles_yml_url,
            "CREDENTIALS_URL": self.credentials_url,
            "OUTPUT_URL": self.output_url,
            "LOGS_URL": self.logs_url,
        }


@dataclass
class ExecutionStatus:
    """
    Status of a Cloud Run job execution.
    """
    
    execution_id: str
    state: ExecutionState
    create_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    @property
    def is_terminal(self) -> bool:
        """Return True if the execution has reached a terminal state."""
        return self.state in (
            ExecutionState.SUCCEEDED,
            ExecutionState.FAILED,
            ExecutionState.CANCELLED,
        )
    
    @property
    def is_successful(self) -> bool:
        """Return True if the execution completed successfully."""
        return self.state == ExecutionState.SUCCEEDED
