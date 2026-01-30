"""Status command for viewing job status."""

import click

from ..aws_batch import BatchClient, BatchError
from ..manifest import (
    BATCH_JOBS_BASE,
    JobStatus,
    list_jobs as list_manifests,
    load_manifest,
)


def format_status(status: JobStatus) -> str:
    """Format status with color."""
    colors = {
        JobStatus.PENDING: "yellow",
        JobStatus.SUBMITTED: "yellow",
        JobStatus.RUNNING: "cyan",
        JobStatus.SUCCEEDED: "green",
        JobStatus.FAILED: "red",
        JobStatus.CANCELLED: "magenta",
        JobStatus.FINALIZING: "cyan",
        JobStatus.FINALIZED: "green",
    }
    return click.style(status.value, fg=colors.get(status, "white"))


def format_time_ago(dt) -> str:
    """Format a datetime as a relative time string."""
    from datetime import datetime, timezone

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - dt

    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        mins = int(seconds / 60)
        return f"{mins}m ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds / 86400)
        return f"{days}d ago"


@click.command()
@click.argument("job_id", required=False)
@click.option("--user", help="Filter by username")
@click.option(
    "--status",
    "status_filter",
    type=click.Choice([s.value for s in JobStatus]),
    help="Filter by status",
)
@click.option("--pipeline", help="Filter by pipeline type")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def status(job_id, user, status_filter, pipeline, base_path):
    """Show job status.

    Without JOB_ID, shows a summary of recent jobs.
    With JOB_ID, shows detailed status for that job.

    \b
    Examples:
      dh batch status                          # List recent jobs
      dh batch status dma-embed-20260109-a3f2  # Show specific job
      dh batch status --user dma               # Filter by user
      dh batch status --status running         # Filter by status
    """
    if job_id:
        _show_job_details(job_id, base_path)
    else:
        _show_job_list(user, status_filter, pipeline, base_path)


def _aws_status_to_job_status(aws_status: str) -> JobStatus:
    """Convert AWS Batch status to JobStatus enum."""
    mapping = {
        "SUBMITTED": JobStatus.SUBMITTED,
        "PENDING": JobStatus.PENDING,
        "RUNNABLE": JobStatus.RUNNING,  # Runnable means waiting for compute
        "STARTING": JobStatus.RUNNING,
        "RUNNING": JobStatus.RUNNING,
        "SUCCEEDED": JobStatus.SUCCEEDED,
        "FAILED": JobStatus.FAILED,
    }
    return mapping.get(aws_status, JobStatus.SUBMITTED)


def _show_job_list(user, status_filter, pipeline, base_path):
    """Show a list of recent jobs."""
    status_enum = JobStatus(status_filter) if status_filter else None
    manifests = list_manifests(
        base_path=base_path,
        user=user,
        status=None,  # Don't filter yet - we'll filter after getting live status
        pipeline=pipeline,
        limit=50,  # Fetch more, filter later
    )

    if not manifests:
        click.echo("No jobs found.")
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

    if not display_data:
        click.echo("No jobs found matching filters.")
        return

    # Limit to 20 after filtering
    display_data = display_data[:20]

    # Print header
    click.echo()
    click.echo(
        f"{'JOB ID':<35} {'STATUS':<12} {'PIPELINE':<12} {'USER':<10} {'CREATED':<12}"
    )
    click.echo("-" * 85)

    for manifest, live_status in display_data:
        click.echo(
            f"{manifest.job_id:<35} "
            f"{format_status(live_status):<21} "  # Extra space for color codes
            f"{manifest.pipeline:<12} "
            f"{manifest.user:<10} "
            f"{format_time_ago(manifest.created):<12}"
        )

    click.echo()
    click.echo(f"Showing {len(display_data)} most recent jobs.")
    click.echo("Use 'dh batch status <job-id>' for details.")


def _parse_retry_job_id(job_id: str) -> tuple[str, str | None]:
    """Parse a job ID to extract parent job ID and retry suffix.

    Args:
        job_id: Job ID like 'dma-embed-20260120-63ec' or 'dma-embed-20260120-63ec-r1'

    Returns:
        Tuple of (parent_job_id, retry_id or None)
    """
    import re

    # Check for retry suffix like -r1, -r2, etc.
    match = re.match(r"^(.+)(-r\d+)$", job_id)
    if match:
        return match.group(1), job_id
    return job_id, None


def _show_job_details(job_id: str, base_path: str):
    """Show detailed status for a specific job."""
    # Check if this is a retry job ID
    parent_job_id, retry_id = _parse_retry_job_id(job_id)

    try:
        manifest = load_manifest(parent_job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {job_id}", err=True)
        click.echo(f"Looking in: {base_path}/{parent_job_id}/manifest.json", err=True)
        raise SystemExit(1)

    # If showing a retry job, show retry-specific details
    if retry_id:
        _show_retry_details(manifest, retry_id)
        return

    click.echo()
    click.echo(f"Job ID:    {manifest.job_id}")
    click.echo(f"Status:    {format_status(manifest.status)}")
    click.echo(f"Pipeline:  {manifest.pipeline}")
    click.echo(f"User:      {manifest.user}")
    click.echo(
        f"Created:   {manifest.created.isoformat()} ({format_time_ago(manifest.created)})"
    )
    click.echo(
        f"Updated:   {manifest.updated.isoformat()} ({format_time_ago(manifest.updated)})"
    )

    if manifest.input:
        click.echo()
        click.echo("Input:")
        click.echo(f"  Source:     {manifest.input.source}")
        if manifest.input.num_sequences:
            click.echo(f"  Sequences:  {manifest.input.num_sequences:,}")
        if manifest.input.num_chunks:
            click.echo(f"  Chunks:     {manifest.input.num_chunks}")

    if manifest.batch:
        click.echo()
        click.echo("Batch:")
        click.echo(f"  Queue:      {manifest.batch.queue}")
        if manifest.batch.job_id:
            click.echo(f"  AWS Job ID: {manifest.batch.job_id}")
        if manifest.batch.job_definition:
            click.echo(f"  Definition: {manifest.batch.job_definition}")
        if manifest.batch.array_size:
            click.echo(f"  Array Size: {manifest.batch.array_size}")

            # Try to get live status from AWS Batch
            if manifest.batch.job_id:
                _show_array_status(manifest.batch.job_id)

    if manifest.output:
        click.echo()
        click.echo("Output:")
        if manifest.output.destination:
            click.echo(f"  Destination: {manifest.output.destination}")
        click.echo(f"  Finalized:   {manifest.output.finalized}")

    if manifest.error_message:
        click.echo()
        click.echo(click.style("Error:", fg="red"))
        click.echo(f"  {manifest.error_message}")

    if manifest.retries:
        click.echo()
        click.echo("Retries:")
        for retry in manifest.retries:
            reslice_info = ""
            if retry.reslice_prefix:
                reslice_info = f" (resliced to {retry.reslice_count} chunks)"
            click.echo(f"  - {retry.retry_id}: {len(retry.indices)} indices{reslice_info}")
            click.echo(f"    Indices: {retry.indices}")
            if retry.batch_job_id:
                # Show brief status for retry job
                try:
                    client = BatchClient()
                    array_status = client.get_array_job_status(retry.batch_job_id)
                    if array_status.is_complete:
                        pct = array_status.success_rate * 100
                        color = "green" if pct == 100 else "yellow" if pct > 90 else "red"
                        click.echo(
                            f"    Status: Complete - {click.style(f'{pct:.0f}%', fg=color)} "
                            f"({array_status.succeeded}/{array_status.total} succeeded)"
                        )
                    else:
                        click.echo(
                            f"    Status: Running - {array_status.succeeded}/{array_status.total} done, "
                            f"{array_status.running} running"
                        )
                except BatchError:
                    click.echo(f"    Status: (could not fetch)")
            click.echo(f"    Details: dh batch status {retry.retry_id}")

    # Suggest next steps
    click.echo()
    if manifest.status == JobStatus.RUNNING:
        click.echo("Next steps:")
        click.echo(f"  View logs:   dh batch logs {job_id}")
        click.echo(f"  Cancel job:  dh batch cancel {job_id}")
    elif manifest.status == JobStatus.FAILED:
        click.echo("Next steps:")
        click.echo(f"  View logs:   dh batch logs {job_id} --failed")
        click.echo(f"  Retry:       dh batch retry {job_id}")
    elif manifest.status == JobStatus.SUCCEEDED:
        click.echo("Next steps:")
        click.echo(
            f"  Finalize:    dh batch finalize {job_id} --output /primordial/output.h5"
        )


def _show_array_status(batch_job_id: str):
    """Show live array job status from AWS Batch."""
    try:
        client = BatchClient()
        array_status = client.get_array_job_status(batch_job_id)

        click.echo()
        click.echo("  Array Status:")
        click.echo(f"    Pending:   {array_status.pending}")
        click.echo(f"    Runnable:  {array_status.runnable}")
        click.echo(f"    Starting:  {array_status.starting}")
        click.echo(f"    Running:   {array_status.running}")
        click.echo(
            f"    Succeeded: {click.style(str(array_status.succeeded), fg='green')}"
        )
        click.echo(f"    Failed:    {click.style(str(array_status.failed), fg='red')}")

        if array_status.is_complete:
            pct = array_status.success_rate * 100
            color = "green" if pct == 100 else "yellow" if pct > 90 else "red"
            click.echo(
                f"    Complete:  {click.style(f'{pct:.1f}%', fg=color)} success rate"
            )
        else:
            pct = array_status.completed / array_status.total * 100
            click.echo(
                f"    Progress:  {pct:.1f}% ({array_status.completed}/{array_status.total})"
            )

    except BatchError as e:
        click.echo(f"    (Could not fetch live status: {e})")


def _show_retry_details(manifest, retry_id: str):
    """Show detailed status for a retry job."""
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

    click.echo()
    click.echo(f"Retry Job:   {retry_id}")
    click.echo(f"Parent Job:  {manifest.job_id}")
    click.echo(f"Pipeline:    {manifest.pipeline}")
    click.echo(f"User:        {manifest.user}")
    click.echo(
        f"Created:     {retry_info.created.isoformat()} ({format_time_ago(retry_info.created)})"
    )

    click.echo()
    click.echo("Retry Config:")
    click.echo(f"  Indices:   {retry_info.indices}")
    if retry_info.reslice_prefix:
        click.echo(f"  Reslice:   {retry_info.reslice_prefix} ({retry_info.reslice_count} chunks)")
    else:
        click.echo(f"  Reslice:   No (retrying original chunks)")

    if retry_info.batch_job_id:
        click.echo()
        click.echo("Batch:")
        click.echo(f"  AWS Job ID: {retry_info.batch_job_id}")

        # Get live status from AWS Batch
        _show_array_status(retry_info.batch_job_id)

    click.echo()
    click.echo("Next steps:")
    click.echo(f"  View logs:      dh batch logs {manifest.job_id}")
    click.echo(f"  Parent status:  dh batch status {manifest.job_id}")
