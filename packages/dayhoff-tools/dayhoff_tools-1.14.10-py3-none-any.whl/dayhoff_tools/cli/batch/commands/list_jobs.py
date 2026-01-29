"""List command for showing recent jobs."""

import click

from ..aws_batch import BatchClient, BatchError
from ..manifest import BATCH_JOBS_BASE, JobStatus, list_jobs as list_manifests
from .status import format_status, format_time_ago, _aws_status_to_job_status


@click.command("list")
@click.option("--user", help="Filter by username")
@click.option(
    "--status",
    "status_filter",
    type=click.Choice([s.value for s in JobStatus]),
    help="Filter by status",
)
@click.option("--pipeline", help="Filter by pipeline type")
@click.option(
    "--limit", default=20, type=int, help="Maximum number of jobs to show [default: 20]"
)
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def list_jobs(user, status_filter, pipeline, limit, base_path):
    """List recent batch jobs.

    Shows a table of recent jobs with their status, pipeline type, and creation time.
    Status is fetched live from AWS Batch.

    \b
    Examples:
      dh batch list                      # All recent jobs
      dh batch list --user dma           # Filter by user
      dh batch list --status running     # Filter by status
      dh batch list --pipeline embed-t5  # Filter by pipeline type
      dh batch list --limit 50           # Show more jobs
    """
    status_enum = JobStatus(status_filter) if status_filter else None

    # Fetch more manifests than requested to allow filtering by live status
    manifests = list_manifests(
        base_path=base_path,
        user=user,
        status=None,  # Don't filter by status yet - will filter after getting live status
        pipeline=pipeline,
        limit=limit * 3,  # Fetch extra to account for status filtering
    )

    if not manifests:
        click.echo("No jobs found.")
        if user or status_filter or pipeline:
            click.echo("Try removing filters to see all jobs.")
        return

    # Collect AWS Batch job IDs for live status lookup
    batch_job_ids = []
    manifest_to_batch_id = {}
    for m in manifests:
        if m.batch and m.batch.job_id:
            batch_job_ids.append(m.batch.job_id)
            manifest_to_batch_id[m.job_id] = m.batch.job_id

    # Fetch live statuses from AWS Batch
    live_statuses = {}
    if batch_job_ids:
        try:
            client = BatchClient()
            live_statuses = client.get_job_statuses_batch(batch_job_ids)
        except BatchError as e:
            click.echo(f"Warning: Could not fetch live status from AWS Batch: {e}")

    # Build display data with live status
    display_data = []
    for manifest in manifests:
        # Use live status if available, otherwise fall back to manifest status
        if manifest.job_id in manifest_to_batch_id:
            batch_id = manifest_to_batch_id[manifest.job_id]
            aws_status = live_statuses.get(batch_id)
            if aws_status:
                live_status = _aws_status_to_job_status(aws_status)
            else:
                live_status = manifest.status
        else:
            live_status = manifest.status

        # Apply status filter if specified
        if status_enum and live_status != status_enum:
            continue

        display_data.append((manifest, live_status))

        # Stop once we have enough
        if len(display_data) >= limit:
            break

    if not display_data:
        click.echo("No jobs found matching filters.")
        return

    # Print header
    click.echo()
    click.echo(
        f"{'JOB ID':<35} {'STATUS':<12} {'PIPELINE':<12} {'USER':<10} {'CREATED':<12}"
    )
    click.echo("-" * 85)

    for manifest, live_status in display_data:
        click.echo(
            f"{manifest.job_id:<35} "
            f"{format_status(live_status):<21} "  # Extra space for ANSI color codes
            f"{manifest.pipeline:<12} "
            f"{manifest.user:<10} "
            f"{format_time_ago(manifest.created):<12}"
        )

    click.echo()
    click.echo(f"Showing {len(display_data)} jobs.")

    # Show filter hints
    hints = []
    if not user:
        hints.append("--user <name>")
    if not status_filter:
        hints.append("--status <status>")
    if not pipeline:
        hints.append("--pipeline <type>")

    if hints:
        click.echo(f"Filter with: {' '.join(hints)}")
