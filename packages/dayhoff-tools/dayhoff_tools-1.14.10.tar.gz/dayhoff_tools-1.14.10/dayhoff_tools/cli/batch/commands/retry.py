"""Retry command for re-running failed chunks."""

from datetime import datetime

import click

from ..aws_batch import BatchClient, BatchError
from ..job_id import generate_job_id
from ..manifest import (
    BATCH_JOBS_BASE,
    JobStatus,
    RetryInfo,
    get_job_dir,
    load_manifest,
    save_manifest,
)


@click.command()
@click.argument("job_id")
@click.option("--indices", help="Specific indices to retry (comma-separated)")
@click.option(
    "--dry-run", is_flag=True, help="Show what would be retried without submitting"
)
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def retry(job_id, indices, dry_run, base_path):
    """Retry failed chunks of a batch job.

    Identifies failed array indices and submits a new job to retry only
    those specific indices.

    \b
    Examples:
      dh batch retry dma-embed-20260109-a3f2              # Retry all failed
      dh batch retry dma-embed-20260109-a3f2 --indices 5,12,27  # Retry specific indices
      dh batch retry dma-embed-20260109-a3f2 --dry-run   # Show what would be retried
    """
    # Load manifest
    try:
        manifest = load_manifest(job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {job_id}", err=True)
        raise SystemExit(1)

    # Get failed indices
    if indices:
        # User specified indices
        retry_indices = [int(i.strip()) for i in indices.split(",")]
    else:
        # Auto-detect from .done markers
        retry_indices = _find_incomplete_chunks(job_id, base_path)

    if not retry_indices:
        click.echo("No failed or incomplete chunks found. Nothing to retry.")
        return

    click.echo(f"Found {len(retry_indices)} chunks to retry: {retry_indices}")

    if dry_run:
        click.echo()
        click.echo(click.style("Dry run - job not submitted", fg="yellow"))
        return

    # Check if we have the required info
    if not manifest.batch:
        click.echo("Job has no batch configuration.", err=True)
        raise SystemExit(1)

    # Generate retry job ID
    retry_id = f"{job_id}-r{len(manifest.retries) + 1}"

    click.echo()
    click.echo(f"Retry job ID: {retry_id}")

    # Submit retry job
    try:
        client = BatchClient()
        job_dir = get_job_dir(job_id, base_path)

        environment = {
            "JOB_DIR": str(job_dir),
            "JOB_ID": job_id,
            "BATCH_RETRY_INDICES": ",".join(str(i) for i in retry_indices),
        }

        batch_job_id = client.submit_array_job_with_indices(
            job_name=retry_id,
            job_definition=manifest.batch.job_definition or "dayhoff-embed-t5",
            job_queue=manifest.batch.queue,
            indices=retry_indices,
            environment=environment,
            timeout_seconds=6 * 3600,
            retry_attempts=3,
        )

        # Update manifest with retry info
        retry_info = RetryInfo(
            retry_id=retry_id,
            indices=retry_indices,
            batch_job_id=batch_job_id,
            created=datetime.utcnow(),
        )
        manifest.retries.append(retry_info)
        manifest.status = JobStatus.RUNNING
        save_manifest(manifest, base_path)

        click.echo()
        click.echo(click.style("✓ Retry job submitted successfully!", fg="green"))
        click.echo()
        click.echo(f"AWS Batch Job ID: {batch_job_id}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  Check status:  dh batch status {job_id}")
        click.echo(f"  View logs:     dh batch logs {job_id}")

    except BatchError as e:
        click.echo(
            click.style(f"✗ Failed to submit retry job: {e}", fg="red"), err=True
        )
        raise SystemExit(1)


def _find_incomplete_chunks(job_id: str, base_path: str) -> list[int]:
    """Find chunks that don't have .done markers."""
    job_dir = get_job_dir(job_id, base_path)
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"

    if not input_dir.exists():
        return []

    # Find all input chunks
    input_chunks = sorted(input_dir.glob("chunk_*.fasta"))
    incomplete = []

    for chunk_path in input_chunks:
        # Extract index from filename (chunk_000.fasta -> 0)
        idx_str = chunk_path.stem.split("_")[1]
        idx = int(idx_str)

        # Check for .done marker
        done_marker = output_dir / f"embed_{idx:03d}.done"
        if not done_marker.exists():
            incomplete.append(idx)

    return incomplete
