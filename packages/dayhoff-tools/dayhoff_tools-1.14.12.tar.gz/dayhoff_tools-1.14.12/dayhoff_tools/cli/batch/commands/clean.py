"""Clean command for removing old job directories."""

import click

from ..aws_batch import BatchClient, BatchError
from ..manifest import (
    BATCH_JOBS_BASE,
    JobStatus,
    delete_job_directory,
    list_jobs as list_manifests,
)
from .status import format_time_ago, _aws_status_to_job_status


@click.command("clean")
@click.option("--user", help="Only clean jobs for this user")
@click.option(
    "--older-than",
    type=int,
    default=7,
    help="Only clean jobs older than N days [default: 7]",
)
@click.option("--dry-run", is_flag=True, help="Show what would be cleaned without deleting")
@click.option("--force", is_flag=True, help="Delete without confirmation")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def clean(user, older_than, dry_run, force, base_path):
    """Remove completed job directories to free up space.

    Only removes jobs that have SUCCEEDED or FAILED in AWS Batch.
    Jobs that are still running or pending are never removed.

    \b
    Examples:
      dh batch clean                     # Clean jobs older than 7 days
      dh batch clean --older-than 1      # Clean jobs older than 1 day
      dh batch clean --dry-run           # Show what would be cleaned
      dh batch clean --user dma          # Only clean dma's jobs
    """
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than)

    # Get all manifests
    manifests = list_manifests(
        base_path=base_path,
        user=user,
        status=None,
        pipeline=None,
        limit=500,
    )

    if not manifests:
        click.echo("No jobs found.")
        return

    # Filter to old jobs
    old_manifests = []
    for m in manifests:
        created = m.created
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created < cutoff:
            old_manifests.append(m)

    if not old_manifests:
        click.echo(f"No jobs older than {older_than} days found.")
        return

    # Get live statuses for old jobs
    batch_job_ids = []
    manifest_to_batch_id = {}
    for m in old_manifests:
        if m.batch and m.batch.job_id:
            batch_job_ids.append(m.batch.job_id)
            manifest_to_batch_id[m.job_id] = m.batch.job_id

    live_statuses = {}
    if batch_job_ids:
        try:
            client = BatchClient()
            live_statuses = client.get_job_statuses_batch(batch_job_ids)
        except BatchError as e:
            click.echo(f"Error: Could not fetch status from AWS Batch: {e}", err=True)
            click.echo("Cannot safely clean jobs without knowing their status.", err=True)
            raise SystemExit(1)

    # Find jobs that are safe to clean (SUCCEEDED or FAILED)
    safe_to_clean = []
    for manifest in old_manifests:
        if manifest.job_id in manifest_to_batch_id:
            batch_id = manifest_to_batch_id[manifest.job_id]
            aws_status = live_statuses.get(batch_id, "UNKNOWN")
            if aws_status in ("SUCCEEDED", "FAILED"):
                safe_to_clean.append((manifest, aws_status))
        elif manifest.status in (JobStatus.FINALIZED, JobStatus.CANCELLED):
            # Already finalized or cancelled - safe to clean
            safe_to_clean.append((manifest, manifest.status.value.upper()))

    if not safe_to_clean:
        click.echo(f"No completed jobs older than {older_than} days to clean.")
        return

    # Show what will be cleaned
    click.echo()
    click.echo(f"{'JOB ID':<35} {'STATUS':<12} {'CREATED':<12}")
    click.echo("-" * 65)

    for manifest, status in safe_to_clean:
        click.echo(
            f"{manifest.job_id:<35} "
            f"{status:<12} "
            f"{format_time_ago(manifest.created):<12}"
        )

    click.echo()
    click.echo(f"Found {len(safe_to_clean)} completed jobs to clean.")

    if dry_run:
        click.echo("(dry-run: no changes made)")
        return

    # Confirm before deleting
    if not force:
        if not click.confirm("Delete these job directories?"):
            click.echo("Cancelled.")
            return

    # Delete job directories
    deleted = 0
    for manifest, _ in safe_to_clean:
        try:
            delete_job_directory(manifest.job_id, base_path)
            deleted += 1
            click.echo(f"  Deleted: {manifest.job_id}")
        except Exception as e:
            click.echo(f"  Failed to delete {manifest.job_id}: {e}")

    click.echo()
    click.echo(f"Cleaned {deleted} job directories.")
