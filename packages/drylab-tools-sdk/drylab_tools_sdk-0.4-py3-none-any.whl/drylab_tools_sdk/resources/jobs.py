"""Nextflow job operations."""

import time
from typing import Optional, Dict, Any, List

import requests

from drylab_tools_sdk.resources.base import BaseResource
from drylab_tools_sdk.models.job import Job, JobStatus, JobListResult, JobActionResult


class JobsResource(BaseResource):
    """
    Nextflow job management operations.

    Submit, monitor, and manage Nextflow pipeline jobs.

    Example:
        # Submit a job
        job = client.jobs.submit(
            pipeline_id="rnaseq",
            params={
                "input": "drylab://MyProject/data/samplesheet.csv",
                "outdir": "drylab://MyProject/results",
                "genome": "GRCh38"
            },
            compute_profile="aws-batch-fargate-spot"
        )
        if job.success:
            print(f"Submitted job: {job.id}")
    """

    def submit(
        self,
        pipeline_id: str,
        params: Dict[str, Any],
        compute_profile: str = "aws-batch-fargate-spot",
        version: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Job:
        """
        Submit a new Nextflow pipeline job.

        Args:
            pipeline_id: Pipeline to run. Can be:
                - Public pipeline ID: "rnaseq", "sarek", "fetchngs"
                - User pipeline: "user-{uuid}"
            params: Pipeline parameters. Path parameters should use drylab:// paths.
            compute_profile: Compute backend (default: "aws-batch-fargate-spot")
            version: Pipeline version (optional, defaults to latest)
            project_id: Associate job with a project (optional)

        Returns:
            Job object with id and initial status

        Example:
            job = client.jobs.submit(
                pipeline_id="rnaseq",
                params={
                    "input": "drylab://MyProject/data/samplesheet.csv",
                    "outdir": "drylab://MyProject/results",
                    "genome": "GRCh38"
                },
                compute_profile="aws-batch-fargate-spot"
            )
            if job.success:
                print(f"Submitted job: {job.id}")
        """
        # Pre-validation: Check params is a dict
        if not isinstance(params, dict):
            return Job(
                id="",
                pipeline_id=pipeline_id,
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Invalid parameters. 'params' must be a dictionary/JSON object.",
            )

        try:
            response = self._http.post(
                "/api/v1/ai/nextflow/jobs/submit-job",
                json={
                    "pipeline_id": pipeline_id,
                    "params": params,
                    "compute_profile": compute_profile,
                    "version": version,
                    "project_id": project_id,
                },
            )

            return Job.from_response(
                response,
                success=True,
                status=f"Job submitted successfully. Job ID: {response.get('job_id', response.get('id', 'unknown'))}",
            )
            
        except requests.exceptions.ConnectionError:
            return Job(
                id="",
                pipeline_id=pipeline_id,
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return Job(
                    id="",
                    pipeline_id=pipeline_id,
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"Pipeline not found: {pipeline_id}. Please check the pipeline ID is correct.",
                )
            elif e.response.status_code == 400:
                # Try to extract detailed error message
                try:
                    error_detail = e.response.json().get("detail", {})
                    if isinstance(error_detail, dict) and "errors" in error_detail:
                        # Path validation errors
                        errors = error_detail["errors"]
                        error_msgs = [f"{err.get('field', 'unknown')}: {err.get('error', '')}" for err in errors]
                        return Job(
                            id="",
                            pipeline_id=pipeline_id,
                            job_status=JobStatus.UNKNOWN,
                            success=False,
                            status=f"Path validation failed: {'; '.join(error_msgs)}. Please check that path parameters use 'drylab://' protocol.",
                        )
                    else:
                        error_msg = str(error_detail) if error_detail else "Invalid request parameters."
                        return Job(
                            id="",
                            pipeline_id=pipeline_id,
                            job_status=JobStatus.UNKNOWN,
                            success=False,
                            status=f"Validation error: {error_msg}",
                        )
                except:
                    return Job(
                        id="",
                        pipeline_id=pipeline_id,
                        job_status=JobStatus.UNKNOWN,
                        success=False,
                        status="Validation error (HTTP 400). Please check your parameters and try again.",
                    )
            else:
                return Job(
                    id="",
                    pipeline_id=pipeline_id,
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return Job(
                id="",
                pipeline_id=pipeline_id,
                job_status=JobStatus.UNKNOWN,
                success=False,
                status=f"Unexpected error while submitting job: {str(e)}. Please report this to the Drylab team.",
            )

    def submit_custom(
        self,
        pipeline_name: str,
        pipeline_zip_path: str,
        schema: Dict[str, Any],
        params: Dict[str, Any],
        compute_profile: str = "aws-batch-fargate-spot",
        description: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Job:
        """
        Register a custom pipeline and submit a job in one call.

        Use this when you have a custom Nextflow pipeline zip file
        in the vault and want to run it.

        Args:
            pipeline_name: Name for the pipeline
            pipeline_zip_path: Vault path to pipeline zip file
            schema: Pipeline parameter schema (JSON object)
            params: Pipeline parameters
            compute_profile: Compute backend (default: "aws-batch-fargate-spot")
            description: Pipeline description (optional)
            project_id: Associate with project (optional)

        Returns:
            Job object

        Example:
            job = client.jobs.submit_custom(
                pipeline_name="my-analysis",
                pipeline_zip_path="/MyProject/pipelines/my-pipeline.zip",
                schema={"path_fields": ["input", "outdir"]},
                params={
                    "input": "drylab://MyProject/data/input.csv",
                    "outdir": "drylab://MyProject/results"
                }
            )
            if job.success:
                print(f"Submitted: {job.id}")
        """
        # Pre-validation
        if not isinstance(schema, dict):
            return Job(
                id="",
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Invalid schema format. Schema must be a dictionary/JSON object.",
            )
        
        if not isinstance(params, dict):
            return Job(
                id="",
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Invalid parameters. 'params' must be a dictionary/JSON object.",
            )

        try:
            response = self._http.post(
                "/api/v1/ai/nextflow/jobs/submit-custom-job",
                json={
                    "pipeline_name": pipeline_name,
                    "pipeline_zip_vault_path": pipeline_zip_path,
                    "schema_json": schema,
                    "params": params,
                    "compute_profile": compute_profile,
                    "description": description,
                    "project_id": project_id,
                },
            )

            return Job.from_response(
                response,
                success=True,
                status=f"Pipeline registered and job submitted successfully. Job ID: {response.get('job_id', response.get('id', 'unknown'))}",
            )
            
        except requests.exceptions.ConnectionError:
            return Job(
                id="",
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return Job(
                    id="",
                    pipeline_id="",
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"Pipeline zip file not found: {pipeline_zip_path}. Please check the vault path is correct.",
                )
            elif e.response.status_code == 400:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    return Job(
                        id="",
                        pipeline_id="",
                        job_status=JobStatus.UNKNOWN,
                        success=False,
                        status=f"Validation error: {error_detail}",
                    )
                except:
                    return Job(
                        id="",
                        pipeline_id="",
                        job_status=JobStatus.UNKNOWN,
                        success=False,
                        status="Validation error (HTTP 400). Please check your pipeline zip, schema, and parameters.",
                    )
            else:
                return Job(
                    id="",
                    pipeline_id="",
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return Job(
                id="",
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status=f"Unexpected error: {str(e)}. Please report this to the Drylab team.",
            )

    def get(self, job_id: str) -> Job:
        """
        Get the current status of a job.

        Args:
            job_id: Job UUID

        Returns:
            Job object with current status

        Example:
            job = client.jobs.get("550e8400-e29b-41d4-a716-446655440000")
            if job.success:
                print(f"Status: {job.job_status.value}")
        """
        try:
            response = self._http.post(f"/api/v1/ai/nextflow/jobs/{job_id}/get", json={})

            return Job.from_response(
                response,
                success=True,
                status=f"Job status retrieved. Current status: {response.get('status', 'unknown')}",
            )
            
        except requests.exceptions.ConnectionError:
            return Job(
                id=job_id,
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return Job(
                    id=job_id,
                    pipeline_id="",
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"Job not found: {job_id}. Please check the job ID is correct.",
                )
            else:
                return Job(
                    id=job_id,
                    pipeline_id="",
                    job_status=JobStatus.UNKNOWN,
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return Job(
                id=job_id,
                pipeline_id="",
                job_status=JobStatus.UNKNOWN,
                success=False,
                status=f"Unexpected error while retrieving job: {str(e)}. Please report this to the Drylab team.",
            )

    def list(
        self,
        status: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        limit: int = 20,
        ai_only: bool = True,
    ) -> JobListResult:
        """
        List jobs with optional filters.

        Args:
            status: Filter by status ("running", "completed", "failed")
            pipeline_id: Filter by pipeline
            limit: Maximum number of jobs (1-100)
            ai_only: Only show AI-submitted jobs (default: True)

        Returns:
            JobListResult with jobs list and status

        Example:
            result = client.jobs.list(status="running")
            if result.success:
                print(f"Found {len(result.jobs)} running jobs")
        """
        try:
            response = self._http.post(
                "/api/v1/ai/nextflow/jobs/list",
                json={
                    "status": status,
                    "pipeline_id": pipeline_id,
                    "limit": limit,
                    "ai_only": ai_only,
                },
            )

            jobs = [Job.from_response(j) for j in response.get("jobs", [])]
            
            return JobListResult(
                jobs=jobs,
                success=True,
                status=f"Found {len(jobs)} job(s).",
            )
            
        except requests.exceptions.ConnectionError:
            return JobListResult(
                jobs=[],
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            return JobListResult(
                jobs=[],
                success=False,
                status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
            )
        except Exception as e:
            return JobListResult(
                jobs=[],
                success=False,
                status=f"Unexpected error while listing jobs: {str(e)}. Please report this to the Drylab team.",
            )

    def cancel(self, job_id: str) -> JobActionResult:
        """
        Cancel a running job.

        Args:
            job_id: Job UUID

        Returns:
            JobActionResult with success status

        Example:
            result = client.jobs.cancel(job.id)
            print(result)
        """
        try:
            self._http.post(f"/api/v1/ai/nextflow/jobs/{job_id}/cancel", json={})
            
            return JobActionResult(
                job_id=job_id,
                action="cancel",
                success=True,
                status=f"Cancellation initiated for job {job_id}.",
            )
            
        except requests.exceptions.ConnectionError:
            return JobActionResult(
                job_id=job_id,
                action="cancel",
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return JobActionResult(
                    job_id=job_id,
                    action="cancel",
                    success=False,
                    status=f"Job not found: {job_id}. Please check the job ID is correct.",
                )
            elif e.response.status_code == 400:
                return JobActionResult(
                    job_id=job_id,
                    action="cancel",
                    success=False,
                    status="Job is not running. It may have already completed or been cancelled.",
                )
            else:
                return JobActionResult(
                    job_id=job_id,
                    action="cancel",
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return JobActionResult(
                job_id=job_id,
                action="cancel",
                success=False,
                status=f"Unexpected error while cancelling job: {str(e)}. Please report this to the Drylab team.",
            )

    def delete(self, job_id: str) -> JobActionResult:
        """
        Delete a job record.

        Args:
            job_id: Job UUID

        Returns:
            JobActionResult with success status

        Example:
            result = client.jobs.delete(job.id)
            print(result)
        """
        try:
            self._http.post(f"/api/v1/ai/nextflow/jobs/{job_id}/delete", json={})
            
            return JobActionResult(
                job_id=job_id,
                action="delete",
                success=True,
                status=f"Job {job_id} deleted successfully.",
            )
            
        except requests.exceptions.ConnectionError:
            return JobActionResult(
                job_id=job_id,
                action="delete",
                success=False,
                status="Connection failed. The Drylab backend may be unavailable. Please check your network connection and try again later.",
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return JobActionResult(
                    job_id=job_id,
                    action="delete",
                    success=False,
                    status=f"Job not found: {job_id}. It may have already been deleted.",
                )
            else:
                return JobActionResult(
                    job_id=job_id,
                    action="delete",
                    success=False,
                    status=f"API error (HTTP {e.response.status_code}). Please try again later or contact the Drylab team if the issue persists.",
                )
        except Exception as e:
            return JobActionResult(
                job_id=job_id,
                action="delete",
                success=False,
                status=f"Unexpected error while deleting job: {str(e)}. Please report this to the Drylab team.",
            )

    def wait_for_completion(
        self,
        job_id: str,
        poll_interval: int = 30,
        timeout: Optional[int] = None,
    ) -> Job:
        """
        Wait for a job to complete.

        Args:
            job_id: Job UUID
            poll_interval: Seconds between status checks (default: 30)
            timeout: Maximum seconds to wait (optional)

        Returns:
            Job object with final status

        Raises:
            TimeoutError: If timeout is reached before completion

        Example:
            job = client.jobs.submit(...)
            final_job = client.jobs.wait_for_completion(job.id, timeout=3600)
            if final_job.is_success:
                print("Job completed!")
        """
        start_time = time.time()

        while True:
            job = self.get(job_id)
            
            # If we can't retrieve the job, return the error
            if not job.success:
                return job

            if job.is_complete:
                return job

            if timeout and (time.time() - start_time) > timeout:
                return Job(
                    id=job_id,
                    pipeline_id=job.pipeline_id,
                    job_status=job.job_status,
                    success=False,
                    status=f"Timeout: Job {job_id} did not complete within {timeout} seconds.",
                )

            time.sleep(poll_interval)
