"""AWS Batch client wrapper for job submission and management."""

import logging
import time
from dataclasses import dataclass
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class BatchError(Exception):
    """Error interacting with AWS Batch."""

    pass


@dataclass
class ArrayJobStatus:
    """Aggregated status for an array job."""

    total: int
    pending: int
    runnable: int
    starting: int
    running: int
    succeeded: int
    failed: int

    @property
    def completed(self) -> int:
        return self.succeeded + self.failed

    @property
    def in_progress(self) -> int:
        return self.pending + self.runnable + self.starting + self.running

    @property
    def is_complete(self) -> bool:
        return self.completed == self.total

    @property
    def success_rate(self) -> float:
        if self.completed == 0:
            return 0.0
        return self.succeeded / self.completed


class BatchClient:
    """Client for interacting with AWS Batch."""

    def __init__(self, region: str = "us-east-1"):
        """Initialize the Batch client.

        Args:
            region: AWS region
        """
        self.batch = boto3.client("batch", region_name=region)
        self.logs = boto3.client("logs", region_name=region)
        self.region = region

    def submit_job(
        self,
        job_name: str,
        job_definition: str,
        job_queue: str,
        array_size: int | None = None,
        environment: dict[str, str] | None = None,
        parameters: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
        retry_attempts: int = 3,
        depends_on: list[dict] | None = None,
    ) -> str:
        """Submit a job to AWS Batch.

        Args:
            job_name: Name for the job
            job_definition: Job definition name or ARN
            job_queue: Queue to submit to
            array_size: Size of array job (None for single job)
            environment: Environment variables
            parameters: Job parameters
            timeout_seconds: Job timeout in seconds
            retry_attempts: Number of retry attempts
            depends_on: Job dependencies

        Returns:
            AWS Batch job ID

        Raises:
            BatchError: If submission fails
        """
        try:
            submit_args: dict[str, Any] = {
                "jobName": job_name,
                "jobDefinition": job_definition,
                "jobQueue": job_queue,
                "retryStrategy": {"attempts": retry_attempts},
            }

            if array_size and array_size > 1:
                submit_args["arrayProperties"] = {"size": array_size}

            if environment:
                submit_args["containerOverrides"] = {
                    "environment": [
                        {"name": k, "value": v} for k, v in environment.items()
                    ]
                }

            if parameters:
                submit_args["parameters"] = parameters

            if timeout_seconds:
                submit_args["timeout"] = {"attemptDurationSeconds": timeout_seconds}

            if depends_on:
                submit_args["dependsOn"] = depends_on

            response = self.batch.submit_job(**submit_args)
            job_id = response["jobId"]
            logger.info(f"Submitted job {job_name} with ID {job_id}")
            return job_id

        except ClientError as e:
            raise BatchError(f"Failed to submit job: {e}")

    def submit_array_job_with_indices(
        self,
        job_name: str,
        job_definition: str,
        job_queue: str,
        indices: list[int],
        environment: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
        retry_attempts: int = 3,
    ) -> str:
        """Submit an array job for specific indices only.

        Used for retrying specific failed chunks.

        Args:
            job_name: Name for the job
            job_definition: Job definition name or ARN
            job_queue: Queue to submit to
            indices: Specific array indices to run
            environment: Environment variables
            timeout_seconds: Job timeout in seconds
            retry_attempts: Number of retry attempts

        Returns:
            AWS Batch job ID
        """
        # For small number of indices, submit individual jobs
        # For larger numbers, we could use array job with index selection
        # AWS Batch doesn't natively support sparse array indices, so we use a workaround

        if len(indices) == 1:
            # Single job, set index via environment
            env = environment.copy() if environment else {}
            env["AWS_BATCH_JOB_ARRAY_INDEX"] = str(indices[0])
            return self.submit_job(
                job_name=job_name,
                job_definition=job_definition,
                job_queue=job_queue,
                array_size=None,
                environment=env,
                timeout_seconds=timeout_seconds,
                retry_attempts=retry_attempts,
            )
        else:
            # For multiple indices, we pass them as a comma-separated list
            # The worker will pick its index from this list based on array index
            env = environment.copy() if environment else {}
            env["BATCH_RETRY_INDICES"] = ",".join(str(i) for i in indices)
            return self.submit_job(
                job_name=job_name,
                job_definition=job_definition,
                job_queue=job_queue,
                array_size=len(indices),
                environment=env,
                timeout_seconds=timeout_seconds,
                retry_attempts=retry_attempts,
            )

    def describe_job(self, job_id: str) -> dict:
        """Get details for a specific job.

        Args:
            job_id: AWS Batch job ID

        Returns:
            Job details dictionary

        Raises:
            BatchError: If job not found
        """
        try:
            response = self.batch.describe_jobs(jobs=[job_id])
            if not response.get("jobs"):
                raise BatchError(f"Job not found: {job_id}")
            return response["jobs"][0]
        except ClientError as e:
            raise BatchError(f"Failed to describe job: {e}")

    def get_array_job_status(self, job_id: str) -> ArrayJobStatus:
        """Get aggregated status for an array job.

        Args:
            job_id: AWS Batch job ID (parent array job)

        Returns:
            ArrayJobStatus with counts for each status
        """
        job = self.describe_job(job_id)

        if "arrayProperties" not in job:
            # Single job, not an array
            status = job.get("status", "UNKNOWN")
            return ArrayJobStatus(
                total=1,
                pending=1 if status == "PENDING" else 0,
                runnable=1 if status == "RUNNABLE" else 0,
                starting=1 if status == "STARTING" else 0,
                running=1 if status == "RUNNING" else 0,
                succeeded=1 if status == "SUCCEEDED" else 0,
                failed=1 if status == "FAILED" else 0,
            )

        # Get status summary from array properties
        status_summary = job.get("arrayProperties", {}).get("statusSummary", {})

        return ArrayJobStatus(
            total=job.get("arrayProperties", {}).get("size", 0),
            pending=status_summary.get("PENDING", 0),
            runnable=status_summary.get("RUNNABLE", 0),
            starting=status_summary.get("STARTING", 0),
            running=status_summary.get("RUNNING", 0),
            succeeded=status_summary.get("SUCCEEDED", 0),
            failed=status_summary.get("FAILED", 0),
        )

    def get_job_statuses_batch(self, job_ids: list[str]) -> dict[str, str]:
        """Get status for multiple jobs in a single API call.

        AWS Batch allows up to 100 job IDs per describe_jobs call.
        This method handles batching for larger lists.

        Args:
            job_ids: List of AWS Batch job IDs

        Returns:
            Dictionary mapping job_id -> status string
            Status will be one of: SUBMITTED, PENDING, RUNNABLE, STARTING,
            RUNNING, SUCCEEDED, FAILED, or "UNKNOWN" if not found.
            For array jobs, derives overall status from child statuses.
        """
        if not job_ids:
            return {}

        results = {}
        batch_size = 100  # AWS Batch limit

        for i in range(0, len(job_ids), batch_size):
            batch = job_ids[i : i + batch_size]
            try:
                response = self.batch.describe_jobs(jobs=batch)
                for job in response.get("jobs", []):
                    job_id = job.get("jobId")
                    status = job.get("status", "UNKNOWN")

                    # For array jobs, derive overall status from children
                    if "arrayProperties" in job:
                        summary = job["arrayProperties"].get("statusSummary", {})
                        total = job["arrayProperties"].get("size", 0)
                        succeeded = summary.get("SUCCEEDED", 0)
                        failed = summary.get("FAILED", 0)

                        if succeeded + failed == total:
                            # All children complete
                            status = "SUCCEEDED" if failed == 0 else "FAILED"
                        elif summary.get("RUNNING", 0) > 0:
                            status = "RUNNING"
                        elif summary.get("STARTING", 0) > 0:
                            status = "STARTING"
                        elif summary.get("RUNNABLE", 0) > 0:
                            status = "RUNNABLE"
                        elif summary.get("PENDING", 0) > 0:
                            status = "PENDING"

                    results[job_id] = status
            except ClientError as e:
                logger.warning(f"Failed to describe batch of jobs: {e}")
                # Mark these as unknown
                for job_id in batch:
                    if job_id not in results:
                        results[job_id] = "UNKNOWN"

        return results

    def get_failed_indices(self, job_id: str) -> list[int]:
        """Get the array indices that failed for an array job.

        Args:
            job_id: AWS Batch job ID (parent array job)

        Returns:
            List of failed array indices
        """
        failed_indices = []

        # List child jobs with FAILED status
        try:
            paginator = self.batch.get_paginator("list_jobs")
            for page in paginator.paginate(arrayJobId=job_id, jobStatus="FAILED"):
                for job_summary in page.get("jobSummaryList", []):
                    # Extract array index from job ID (format: jobId:index)
                    child_id = job_summary.get("jobId", "")
                    if ":" in child_id:
                        index = int(child_id.split(":")[-1])
                        failed_indices.append(index)
        except ClientError as e:
            logger.warning(f"Failed to list child jobs: {e}")

        return sorted(failed_indices)

    def cancel_job(self, job_id: str, reason: str = "Cancelled by user") -> None:
        """Cancel a job.

        Args:
            job_id: AWS Batch job ID
            reason: Cancellation reason

        Raises:
            BatchError: If cancellation fails
        """
        try:
            self.batch.cancel_job(jobId=job_id, reason=reason)
            logger.info(f"Cancelled job {job_id}")
        except ClientError as e:
            raise BatchError(f"Failed to cancel job: {e}")

    def terminate_job(self, job_id: str, reason: str = "Terminated by user") -> None:
        """Terminate a running job.

        Args:
            job_id: AWS Batch job ID
            reason: Termination reason

        Raises:
            BatchError: If termination fails
        """
        try:
            self.batch.terminate_job(jobId=job_id, reason=reason)
            logger.info(f"Terminated job {job_id}")
        except ClientError as e:
            raise BatchError(f"Failed to terminate job: {e}")

    def get_log_stream_name(self, job_id: str) -> str | None:
        """Get the CloudWatch log stream name for a job.

        Args:
            job_id: AWS Batch job ID

        Returns:
            Log stream name, or None if not available
        """
        try:
            job = self.describe_job(job_id)
            container = job.get("container", {})
            return container.get("logStreamName")
        except BatchError:
            return None

    def get_logs(
        self,
        job_id: str,
        log_group: str = "/aws/batch/job",
        tail: int = 100,
        start_time: int | None = None,
        follow: bool = False,
    ) -> list[str]:
        """Get CloudWatch logs for a job.

        Args:
            job_id: AWS Batch job ID
            log_group: CloudWatch log group name
            tail: Number of lines to return (from end)
            start_time: Start time in milliseconds since epoch
            follow: If True, continue polling for new logs

        Returns:
            List of log messages
        """
        log_stream = self.get_log_stream_name(job_id)
        if not log_stream:
            return [f"No logs available for job {job_id}"]

        messages = []

        try:
            kwargs: dict[str, Any] = {
                "logGroupName": log_group,
                "logStreamName": log_stream,
                "limit": tail,
                "startFromHead": False,
            }

            if start_time:
                kwargs["startTime"] = start_time

            response = self.logs.get_log_events(**kwargs)

            for event in response.get("events", []):
                timestamp = event.get("timestamp", 0)
                message = event.get("message", "")
                # Format timestamp
                dt = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000)
                )
                messages.append(f"[{dt}] {message}")

        except ClientError as e:
            messages.append(f"Error fetching logs: {e}")

        return messages

    def wait_for_job(
        self, job_id: str, poll_interval: int = 30, timeout: int = 86400
    ) -> str:
        """Wait for a job to complete.

        Args:
            job_id: AWS Batch job ID
            poll_interval: Seconds between status checks
            timeout: Maximum seconds to wait

        Returns:
            Final job status

        Raises:
            BatchError: If timeout exceeded
        """
        start_time = time.time()

        while True:
            if time.time() - start_time > timeout:
                raise BatchError(f"Timeout waiting for job {job_id}")

            job = self.describe_job(job_id)
            status = job.get("status")

            if status in ("SUCCEEDED", "FAILED"):
                return status

            logger.info(f"Job {job_id} status: {status}")
            time.sleep(poll_interval)
