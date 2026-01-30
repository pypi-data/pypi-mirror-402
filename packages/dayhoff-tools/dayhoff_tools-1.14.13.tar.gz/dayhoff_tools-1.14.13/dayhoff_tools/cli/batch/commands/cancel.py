"""Cancel command for stopping running jobs."""

import re

import click

from ..aws_batch import BatchClient, BatchError
from ..manifest import (
    BATCH_JOBS_BASE,
    JobStatus,
    load_manifest,
    save_manifest,
)


def _parse_retry_job_id(job_id: str) -> tuple[str, str | None]:
    """Parse a job ID to extract parent job ID and retry suffix."""
    match = re.match(r"^(.+)(-r\d+)$", job_id)
    if match:
        return match.group(1), job_id
    return job_id, None


@click.command()
@click.argument("job_id")
@click.option("--force", is_flag=True, help="Force termination of running containers")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def cancel(job_id, force, base_path):
    """Cancel a running batch job.

    Cancels the job in AWS Batch and updates the manifest status.
    Also supports cancelling retry jobs by their ID (e.g., job-id-r1).

    \b
    Examples:
      dh batch cancel dma-embed-20260109-a3f2
      dh batch cancel dma-embed-20260109-a3f2-r1  # Cancel specific retry
      dh batch cancel dma-embed-20260109-a3f2 --force
    """
    # Check if this is a retry job ID
    parent_job_id, retry_id = _parse_retry_job_id(job_id)

    # Load manifest
    try:
        manifest = load_manifest(parent_job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {parent_job_id}", err=True)
        raise SystemExit(1)

    # If cancelling a specific retry job
    if retry_id:
        _cancel_retry_job(manifest, retry_id, force, base_path)
        return

    # Check if job can be cancelled
    if manifest.status in (
        JobStatus.SUCCEEDED,
        JobStatus.FINALIZED,
        JobStatus.CANCELLED,
    ):
        click.echo(
            f"Job {job_id} is already {manifest.status.value}, cannot cancel.", err=True
        )
        raise SystemExit(1)

    # Get Batch job ID
    if not manifest.batch or not manifest.batch.job_id:
        click.echo("Job has no AWS Batch job ID, updating status only.")
        manifest.status = JobStatus.CANCELLED
        save_manifest(manifest, base_path)
        click.echo(click.style(f"✓ Job {job_id} marked as cancelled", fg="green"))
        return

    batch_job_id = manifest.batch.job_id

    # Cancel in AWS Batch
    try:
        client = BatchClient()

        if force:
            click.echo(f"Terminating job {batch_job_id}...")
            client.terminate_job(
                batch_job_id, reason="Terminated by user via dh batch cancel --force"
            )
        else:
            click.echo(f"Cancelling job {batch_job_id}...")
            client.cancel_job(
                batch_job_id, reason="Cancelled by user via dh batch cancel"
            )

        # Update manifest
        manifest.status = JobStatus.CANCELLED
        save_manifest(manifest, base_path)

        click.echo()
        click.echo(click.style(f"✓ Job {job_id} cancelled successfully", fg="green"))

        # Handle retries too
        for retry_info in manifest.retries:
            if retry_info.batch_job_id:
                try:
                    if force:
                        client.terminate_job(
                            retry_info.batch_job_id, reason="Parent job cancelled"
                        )
                    else:
                        client.cancel_job(
                            retry_info.batch_job_id, reason="Parent job cancelled"
                        )
                    click.echo(f"  Also cancelled retry job: {retry_info.retry_id}")
                except BatchError:
                    pass  # Retry job may already be complete

    except BatchError as e:
        click.echo(click.style(f"✗ Failed to cancel job: {e}", fg="red"), err=True)
        raise SystemExit(1)


def _cancel_retry_job(manifest, retry_id: str, force: bool, base_path: str):
    """Cancel a specific retry job."""
    # Find the retry info
    retry_info = None
    for retry in manifest.retries:
        if retry.retry_id == retry_id:
            retry_info = retry
            break

    if not retry_info:
        click.echo(f"Retry job not found: {retry_id}", err=True)
        click.echo(f"Known retries: {[r.retry_id for r in manifest.retries]}", err=True)
        raise SystemExit(1)

    if not retry_info.batch_job_id:
        click.echo(f"Retry job {retry_id} has no AWS Batch job ID.", err=True)
        raise SystemExit(1)

    # Cancel in AWS Batch
    try:
        client = BatchClient()

        if force:
            click.echo(f"Terminating retry job {retry_info.batch_job_id}...")
            client.terminate_job(
                retry_info.batch_job_id,
                reason="Terminated by user via dh batch cancel --force",
            )
        else:
            click.echo(f"Cancelling retry job {retry_info.batch_job_id}...")
            client.cancel_job(
                retry_info.batch_job_id,
                reason="Cancelled by user via dh batch cancel",
            )

        click.echo()
        click.echo(click.style(f"✓ Retry job {retry_id} cancelled successfully", fg="green"))
        click.echo(f"Parent job: {manifest.job_id}")

    except BatchError as e:
        click.echo(click.style(f"✗ Failed to cancel retry job: {e}", fg="red"), err=True)
        raise SystemExit(1)
