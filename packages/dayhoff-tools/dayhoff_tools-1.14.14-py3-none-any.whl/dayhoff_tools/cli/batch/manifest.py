"""Manifest management for batch jobs.

Manifests are JSON files stored in Primordial that track job metadata,
status, and configuration. They provide the single source of truth for
job state.
"""

import json
import os
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Possible job statuses."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    FINALIZING = "finalizing"
    FINALIZED = "finalized"


class InputConfig(BaseModel):
    """Configuration for job input."""

    source: str = Field(..., description="Path to input file or directory")
    num_sequences: int | None = Field(
        None, description="Number of sequences (for FASTA)"
    )
    num_chunks: int | None = Field(None, description="Number of chunks created")
    sequences_per_chunk: int | None = Field(None, description="Sequences per chunk")


class BatchConfig(BaseModel):
    """AWS Batch job configuration."""

    job_id: str | None = Field(None, description="AWS Batch job ID")
    job_definition: str | None = Field(None, description="Job definition name:revision")
    queue: str = Field(..., description="Batch queue name")
    array_size: int | None = Field(None, description="Array job size")


class OutputConfig(BaseModel):
    """Configuration for job output."""

    destination: str | None = Field(None, description="Final output path")
    finalized: bool = Field(False, description="Whether output has been finalized")


class RetryInfo(BaseModel):
    """Information about a retry attempt."""

    retry_id: str = Field(..., description="Retry job ID")
    indices: list[int] = Field(..., description="Array indices being retried")
    batch_job_id: str | None = Field(None, description="AWS Batch job ID for retry")
    reslice_prefix: str | None = Field(
        None, description="Reslice prefix if chunks were resliced (e.g., 'r1')"
    )
    reslice_count: int | None = Field(
        None, description="Number of resliced chunks created"
    )
    created: datetime = Field(default_factory=datetime.utcnow)


class JobManifest(BaseModel):
    """Complete manifest for a batch job."""

    job_id: str = Field(..., description="Job ID")
    user: str = Field(..., description="Username who submitted the job")
    pipeline: str = Field(..., description="Pipeline type (embed-t5, boltz, batch)")
    status: JobStatus = Field(JobStatus.PENDING, description="Current job status")
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)

    input: InputConfig | None = Field(None, description="Input configuration")
    batch: BatchConfig | None = Field(None, description="Batch job configuration")
    output: OutputConfig | None = Field(None, description="Output configuration")

    retries: list[RetryInfo] = Field(default_factory=list, description="Retry history")

    # Additional metadata
    image_uri: str | None = Field(None, description="Container image URI")
    command: str | None = Field(None, description="Command to run")
    error_message: str | None = Field(None, description="Error message if failed")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Default base path for job data
BATCH_JOBS_BASE = "/primordial/.batch-jobs"


def get_job_dir(job_id: str, base_path: str = BATCH_JOBS_BASE) -> Path:
    """Get the directory path for a job.

    Args:
        job_id: Job ID
        base_path: Base path for batch jobs (default: /primordial/.batch-jobs)

    Returns:
        Path to job directory
    """
    return Path(base_path) / job_id


def get_manifest_path(job_id: str, base_path: str = BATCH_JOBS_BASE) -> Path:
    """Get the manifest file path for a job.

    Args:
        job_id: Job ID
        base_path: Base path for batch jobs

    Returns:
        Path to manifest.json
    """
    return get_job_dir(job_id, base_path) / "manifest.json"


def create_job_directory(job_id: str, base_path: str = BATCH_JOBS_BASE) -> Path:
    """Create the directory structure for a new job.

    Creates:
    - {base_path}/{job_id}/
    - {base_path}/{job_id}/input/
    - {base_path}/{job_id}/output/

    Args:
        job_id: Job ID
        base_path: Base path for batch jobs

    Returns:
        Path to job directory
    """
    job_dir = get_job_dir(job_id, base_path)
    (job_dir / "input").mkdir(parents=True, exist_ok=True)
    (job_dir / "output").mkdir(parents=True, exist_ok=True)
    return job_dir


def save_manifest(manifest: JobManifest, base_path: str = BATCH_JOBS_BASE) -> Path:
    """Save a manifest to disk atomically.

    Uses write-to-temp-then-rename for atomicity to prevent corruption
    if interrupted.

    Args:
        manifest: JobManifest to save
        base_path: Base path for batch jobs

    Returns:
        Path to saved manifest
    """
    manifest.updated = datetime.utcnow()
    manifest_path = get_manifest_path(manifest.job_id, base_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first, then rename for atomicity
    temp_fd, temp_path = tempfile.mkstemp(
        dir=manifest_path.parent, prefix=".manifest_", suffix=".json"
    )
    try:
        with os.fdopen(temp_fd, "w") as f:
            f.write(manifest.model_dump_json(indent=2))
        os.rename(temp_path, manifest_path)
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise

    return manifest_path


def load_manifest(job_id: str, base_path: str = BATCH_JOBS_BASE) -> JobManifest:
    """Load a manifest from disk.

    Args:
        job_id: Job ID
        base_path: Base path for batch jobs

    Returns:
        JobManifest

    Raises:
        FileNotFoundError: If manifest doesn't exist
        ValueError: If manifest is invalid
    """
    manifest_path = get_manifest_path(job_id, base_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found for job: {job_id}")

    with open(manifest_path) as f:
        data = json.load(f)

    return JobManifest(**data)


def update_manifest(
    job_id: str, updates: dict[str, Any], base_path: str = BATCH_JOBS_BASE
) -> JobManifest:
    """Update specific fields in a manifest.

    Args:
        job_id: Job ID
        updates: Dictionary of fields to update
        base_path: Base path for batch jobs

    Returns:
        Updated JobManifest
    """
    manifest = load_manifest(job_id, base_path)

    # Apply updates
    for key, value in updates.items():
        if hasattr(manifest, key):
            setattr(manifest, key, value)
        else:
            raise ValueError(f"Unknown manifest field: {key}")

    save_manifest(manifest, base_path)
    return manifest


def list_jobs(
    base_path: str = BATCH_JOBS_BASE,
    user: str | None = None,
    status: JobStatus | None = None,
    pipeline: str | None = None,
    limit: int = 50,
) -> list[JobManifest]:
    """List jobs from the batch jobs directory.

    Args:
        base_path: Base path for batch jobs
        user: Filter by username
        status: Filter by status
        pipeline: Filter by pipeline type
        limit: Maximum number of jobs to return

    Returns:
        List of JobManifest objects, sorted by created date (newest first)
    """
    base = Path(base_path)
    if not base.exists():
        return []

    manifests = []
    for job_dir in base.iterdir():
        if not job_dir.is_dir():
            continue

        manifest_path = job_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        try:
            with open(manifest_path) as f:
                data = json.load(f)
            manifest = JobManifest(**data)

            # Apply filters
            if user and manifest.user != user:
                continue
            if status and manifest.status != status:
                continue
            if pipeline and manifest.pipeline != pipeline:
                continue

            manifests.append(manifest)
        except (json.JSONDecodeError, ValueError):
            # Skip invalid manifests
            continue

    # Sort by created date, newest first
    manifests.sort(key=lambda m: m.created, reverse=True)

    return manifests[:limit]


def delete_job_directory(job_id: str, base_path: str = BATCH_JOBS_BASE) -> None:
    """Delete a job directory and all its contents.

    Args:
        job_id: Job ID
        base_path: Base path for batch jobs
    """
    import shutil

    job_dir = get_job_dir(job_id, base_path)
    if job_dir.exists():
        shutil.rmtree(job_dir)
