"""Logs command for viewing job logs."""

import click

from ..aws_batch import BatchClient, BatchError
from ..manifest import BATCH_JOBS_BASE, load_manifest


@click.command()
@click.argument("job_id")
@click.option("--index", type=int, help="Show logs for specific array index")
@click.option("--failed", is_flag=True, help="Show logs for all failed indices")
@click.option("--follow", is_flag=True, help="Stream logs in real-time")
@click.option("--tail", default=100, type=int, help="Show last N lines [default: 100]")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def logs(job_id, index, failed, follow, tail, base_path):
    """View logs for a batch job.

    Shows CloudWatch logs for the job. For array jobs, you can view logs
    for specific indices or all failed indices.

    \b
    Examples:
      dh batch logs dma-embed-20260109-a3f2              # Summary + recent logs
      dh batch logs dma-embed-20260109-a3f2 --index 27   # Specific array index
      dh batch logs dma-embed-20260109-a3f2 --failed     # All failed indices
      dh batch logs dma-embed-20260109-a3f2 --follow     # Stream live logs
    """
    # Load manifest
    try:
        manifest = load_manifest(job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {job_id}", err=True)
        raise SystemExit(1)

    if not manifest.batch or not manifest.batch.job_id:
        click.echo("Job has no AWS Batch job ID.", err=True)
        raise SystemExit(1)

    batch_job_id = manifest.batch.job_id
    client = BatchClient()

    if failed:
        _show_failed_logs(client, batch_job_id, tail)
    elif index is not None:
        _show_index_logs(client, batch_job_id, index, tail, follow)
    else:
        _show_job_logs(client, batch_job_id, tail, follow)


def _show_job_logs(client: BatchClient, batch_job_id: str, tail: int, follow: bool):
    """Show logs for the main job or first array element."""
    try:
        job = client.describe_job(batch_job_id)

        # Check if it's an array job
        if "arrayProperties" in job:
            click.echo("This is an array job. Showing parent job status:")
            click.echo()

            array_status = client.get_array_job_status(batch_job_id)
            click.echo(f"  Succeeded: {array_status.succeeded}/{array_status.total}")
            click.echo(f"  Failed:    {array_status.failed}/{array_status.total}")
            click.echo(f"  Running:   {array_status.running}")
            click.echo()

            if array_status.failed > 0:
                failed_indices = client.get_failed_indices(batch_job_id)
                if failed_indices:
                    click.echo("Failed indices:")
                    for idx in failed_indices[:10]:  # Show first 10
                        click.echo(f"  - {idx}")
                    if len(failed_indices) > 10:
                        click.echo(f"  ... and {len(failed_indices) - 10} more")
                    click.echo()
                    click.echo("To view logs for failed indices:")
                    click.echo(f"  dh batch logs {batch_job_id.split('-')[0]} --failed")
                    click.echo()
                    click.echo("To view logs for a specific index:")
                    click.echo(
                        f"  dh batch logs {batch_job_id.split('-')[0]} --index {failed_indices[0]}"
                    )
            return

        # Single job - show logs
        log_messages = client.get_logs(batch_job_id, tail=tail, follow=follow)

        if not log_messages:
            click.echo("No logs available yet.")
            return

        for msg in log_messages:
            click.echo(msg)

    except BatchError as e:
        click.echo(click.style(f"Error fetching logs: {e}", fg="red"), err=True)


def _show_index_logs(
    client: BatchClient, batch_job_id: str, index: int, tail: int, follow: bool
):
    """Show logs for a specific array index."""
    child_job_id = f"{batch_job_id}:{index}"

    click.echo(f"Logs for array index {index}:")
    click.echo()

    try:
        log_messages = client.get_logs(child_job_id, tail=tail, follow=follow)

        if not log_messages:
            click.echo("No logs available for this index.")
            return

        for msg in log_messages:
            click.echo(msg)

    except BatchError as e:
        click.echo(click.style(f"Error fetching logs: {e}", fg="red"), err=True)


def _show_failed_logs(client: BatchClient, batch_job_id: str, tail: int):
    """Show logs for all failed array indices."""
    try:
        failed_indices = client.get_failed_indices(batch_job_id)

        if not failed_indices:
            click.echo("No failed indices found.")
            return

        click.echo(f"Found {len(failed_indices)} failed indices")
        click.echo()

        for idx in failed_indices:
            click.echo(click.style(f"=== Index {idx} ===", fg="red", bold=True))

            child_job_id = f"{batch_job_id}:{idx}"
            log_messages = client.get_logs(child_job_id, tail=min(tail, 50))

            for msg in log_messages:
                click.echo(msg)

            click.echo()

    except BatchError as e:
        click.echo(click.style(f"Error fetching logs: {e}", fg="red"), err=True)
