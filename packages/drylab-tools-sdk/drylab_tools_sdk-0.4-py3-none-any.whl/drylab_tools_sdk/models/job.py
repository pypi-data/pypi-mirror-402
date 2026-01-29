"""Job data models."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class JobStatus(str, Enum):
    """Job status values."""

    SUBMITTED = "submitted"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass
class Job:
    """Represents a Nextflow job."""

    id: str
    pipeline_id: str
    job_status: JobStatus  # Renamed from 'status' to avoid conflict with operation status
    run_name: Optional[str] = None
    compute_profile: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error: Optional[str] = None
    job_success: Optional[bool] = None  # Whether the job itself succeeded
    complete: Optional[bool] = None
    # Operation result fields
    success: bool = True  # Whether the SDK operation succeeded
    status: str = "Job retrieved successfully."  # Operation status message

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.job_status in (JobStatus.SUBMITTED, JobStatus.PENDING, JobStatus.RUNNING)

    @property
    def is_complete(self) -> bool:
        """Check if job has finished (success or failure)."""
        return self.complete or self.job_status in (
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        )

    @property
    def is_success(self) -> bool:
        """Check if job completed successfully."""
        return self.job_success is True or self.job_status == JobStatus.COMPLETED

    @classmethod
    def from_response(cls, data: Dict[str, Any], success: bool = True, status: str = "Job retrieved successfully.") -> "Job":
        """Create Job from API response."""
        status_str = data.get("status", "unknown")
        try:
            job_status = JobStatus(status_str)
        except ValueError:
            job_status = JobStatus.UNKNOWN

        return cls(
            id=data.get("job_id", data.get("id", "")),
            pipeline_id=data.get("pipeline_id", ""),
            job_status=job_status,
            run_name=data.get("run_name"),
            compute_profile=data.get("compute_profile"),
            params=data.get("params"),
            progress=data.get("progress"),
            start_time=data.get("start"),
            end_time=data.get("complete_time"),
            error=data.get("error_message"),
            job_success=data.get("success"),
            complete=data.get("complete"),
            success=success,
            status=status,
        )

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        
        lines = [f"✓ {self.status}"]
        lines.append(f"  Job ID: {self.id}")
        lines.append(f"  Pipeline: {self.pipeline_id}")
        lines.append(f"  Status: {self.job_status.value}")
        
        if self.run_name:
            lines.append(f"  Run name: {self.run_name}")
        if self.progress is not None:
            lines.append(f"  Progress: {self.progress}%")
        if self.error:
            lines.append(f"  Error: {self.error}")
        
        return "\n".join(lines)


@dataclass
class JobListResult:
    """Result of listing jobs."""

    jobs: List[Job] = field(default_factory=list)
    success: bool = True
    status: str = "Jobs listed successfully."

    def __repr__(self) -> str:
        if not self.success:
            return f"✗ {self.status}"
        
        lines = [f"✓ {self.status}"]
        lines.append(f"Found {len(self.jobs)} jobs:")
        
        for j in self.jobs[:10]:  # Show first 10
            lines.append(f"  - {j.id}: {j.job_status.value} ({j.pipeline_id})")
        
        if len(self.jobs) > 10:
            lines.append(f"  ... and {len(self.jobs) - 10} more")
        
        return "\n".join(lines)


@dataclass
class JobActionResult:
    """Result of a job action (cancel, delete)."""

    job_id: str
    action: str
    success: bool
    status: str

    def __repr__(self) -> str:
        if self.success:
            return f"✓ {self.status}"
        else:
            return f"✗ {self.status}"
