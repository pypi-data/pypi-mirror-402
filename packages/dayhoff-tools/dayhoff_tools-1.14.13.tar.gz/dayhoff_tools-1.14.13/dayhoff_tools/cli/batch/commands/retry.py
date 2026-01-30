"""Retry command for re-running failed chunks."""

from datetime import datetime
from pathlib import Path

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
    "--queue",
    help="Override job queue (e.g., 't4-1x' for on-demand instead of spot)",
)
@click.option(
    "--reslice",
    type=int,
    help="Reslice failed chunks into N thinner chunks (reduces interruption risk)",
)
@click.option(
    "--dry-run", is_flag=True, help="Show what would be retried without submitting"
)
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def retry(job_id, indices, queue, reslice, dry_run, base_path):
    """Retry failed chunks of a batch job.

    Identifies failed array indices and submits a new job to retry only
    those specific indices. Outputs go to the same job directory, so
    finalization works normally after retries complete.

    The --reslice option concatenates failed chunks and re-splits them into
    thinner slices, reducing the time per worker and thus the risk of spot
    interruptions. Resliced outputs are named with a prefix (e.g., embed_r1_000.h5)
    and are automatically included in finalization.

    \b
    Examples:
      dh batch retry dma-embed-20260109-a3f2              # Retry all failed
      dh batch retry dma-embed-20260109-a3f2 --indices 5,12,27  # Retry specific indices
      dh batch retry dma-embed-20260109-a3f2 --queue t4-1x     # Use on-demand (no spot interruptions)
      dh batch retry dma-embed-20260109-a3f2 --reslice 40      # Reslice into 40 thinner chunks
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

    # Check if we have the required info
    if not manifest.batch:
        click.echo("Job has no batch configuration.", err=True)
        raise SystemExit(1)

    # Generate retry job ID and reslice prefix
    retry_num = len(manifest.retries) + 1
    retry_id = f"{job_id}-r{retry_num}"
    reslice_prefix = f"r{retry_num}" if reslice else None

    job_dir = get_job_dir(job_id, base_path)

    if reslice:
        # Count sequences in failed chunks to estimate split
        total_seqs = _count_sequences_in_chunks(job_dir, retry_indices)
        seqs_per_chunk = max(1, total_seqs // reslice)
        click.echo(f"Total sequences in failed chunks: {total_seqs:,}")
        click.echo(f"Reslicing into {reslice} chunks (~{seqs_per_chunk:,} seqs each)")

    if dry_run:
        click.echo()
        click.echo(click.style("Dry run - job not submitted", fg="yellow"))
        return

    click.echo()
    click.echo(f"Retry job ID: {retry_id}")

    # Handle reslicing if requested
    if reslice:
        click.echo(f"Reslice prefix: {reslice_prefix}")
        actual_chunks = _reslice_failed_chunks(
            job_dir, retry_indices, reslice_prefix, reslice
        )
        click.echo(f"Created {actual_chunks} resliced chunks")
        array_size = actual_chunks
    else:
        array_size = len(retry_indices)

    # Submit retry job
    try:
        client = BatchClient()

        environment = {
            "JOB_DIR": str(job_dir),
            "JOB_ID": job_id,
        }

        # Use provided queue or fall back to original
        job_queue = queue or manifest.batch.queue
        if queue and queue != manifest.batch.queue:
            click.echo(f"Using queue: {job_queue} (original: {manifest.batch.queue})")

        if reslice:
            # Resliced retry: use RESLICE_PREFIX, sequential indices 0..N-1
            environment["RESLICE_PREFIX"] = reslice_prefix
            batch_job_id = client.submit_job(
                job_name=retry_id,
                job_definition=manifest.batch.job_definition or "dayhoff-embed-t5",
                job_queue=job_queue,
                array_size=array_size,
                environment=environment,
                timeout_seconds=6 * 3600,
                retry_attempts=5,
            )
        else:
            # Standard retry: use BATCH_RETRY_INDICES mapping
            environment["BATCH_RETRY_INDICES"] = ",".join(str(i) for i in retry_indices)
            batch_job_id = client.submit_array_job_with_indices(
                job_name=retry_id,
                job_definition=manifest.batch.job_definition or "dayhoff-embed-t5",
                job_queue=job_queue,
                indices=retry_indices,
                environment=environment,
                timeout_seconds=6 * 3600,
                retry_attempts=5,
            )

        # Update manifest with retry info
        retry_info = RetryInfo(
            retry_id=retry_id,
            indices=retry_indices,
            batch_job_id=batch_job_id,
            reslice_prefix=reslice_prefix,
            reslice_count=array_size if reslice else None,
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

    # Find all original input chunks (not resliced ones)
    input_chunks = sorted(input_dir.glob("chunk_[0-9][0-9][0-9].fasta"))
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


def _count_sequences_in_chunks(job_dir: Path, indices: list[int]) -> int:
    """Count total sequences in the specified chunk files."""
    input_dir = job_dir / "input"
    total = 0

    for idx in indices:
        chunk_path = input_dir / f"chunk_{idx:03d}.fasta"
        if chunk_path.exists():
            with open(chunk_path) as f:
                for line in f:
                    if line.startswith(">"):
                        total += 1

    return total


def _reslice_failed_chunks(
    job_dir: Path, indices: list[int], reslice_prefix: str, num_chunks: int
) -> int:
    """Concatenate failed chunks and re-split into thinner slices.

    Creates new chunk files named chunk_{prefix}_000.fasta, etc.

    Args:
        job_dir: Job directory path
        indices: List of failed chunk indices
        reslice_prefix: Prefix for new chunk files (e.g., 'r1')
        num_chunks: Target number of new chunks

    Returns:
        Actual number of chunks created
    """
    from dayhoff_tools.fasta import split_fasta
    import tempfile

    input_dir = job_dir / "input"

    # Concatenate all failed chunks into a temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".fasta", delete=False
    ) as tmp_file:
        tmp_path = tmp_file.name
        total_seqs = 0

        for idx in indices:
            chunk_path = input_dir / f"chunk_{idx:03d}.fasta"
            if chunk_path.exists():
                with open(chunk_path) as f:
                    for line in f:
                        tmp_file.write(line)
                        if line.startswith(">"):
                            total_seqs += 1

    try:
        # Calculate sequences per chunk
        seqs_per_chunk = max(1, (total_seqs + num_chunks - 1) // num_chunks)

        # Split into new chunks with reslice prefix
        # split_fasta creates files like: chunk_r1_1.fasta, chunk_r1_2.fasta, etc.
        actual_chunks = split_fasta(
            fasta_file=tmp_path,
            target_folder=str(input_dir),
            base_name=f"chunk_{reslice_prefix}",
            sequences_per_file=seqs_per_chunk,
            max_files=num_chunks,
            show_progress=True,
        )

        # Rename to zero-padded indices (chunk_r1_000.fasta, etc.)
        for i in range(1, actual_chunks + 1):
            old_name = input_dir / f"chunk_{reslice_prefix}_{i}.fasta"
            new_name = input_dir / f"chunk_{reslice_prefix}_{i-1:03d}.fasta"
            if old_name.exists():
                old_name.rename(new_name)

        return actual_chunks

    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
