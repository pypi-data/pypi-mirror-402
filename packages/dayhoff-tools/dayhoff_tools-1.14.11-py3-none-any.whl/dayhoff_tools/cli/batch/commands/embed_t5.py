"""T5 embedding pipeline command."""

import os
import shutil
import subprocess
from pathlib import Path

import click

from ..aws_batch import BatchClient, BatchError
from ..job_id import generate_job_id
from ..manifest import (
    BATCH_JOBS_BASE,
    BatchConfig,
    InputConfig,
    JobManifest,
    JobStatus,
    OutputConfig,
    create_job_directory,
    get_job_dir,
    save_manifest,
)


# Default settings for T5 embedding
DEFAULT_QUEUE = "t4-1x-spot"
DEFAULT_WORKERS = 50
DEFAULT_SEQS_PER_CHUNK = 5000
DEFAULT_JOB_DEFINITION = "dayhoff-embed-t5"
DEFAULT_IMAGE_URI = "074735440724.dkr.ecr.us-east-1.amazonaws.com/dayhoff:embed-latest"


@click.command()
@click.argument("input_fasta", type=click.Path(exists=True))
@click.option(
    "--workers",
    default=DEFAULT_WORKERS,
    type=int,
    help=f"Number of parallel workers [default: {DEFAULT_WORKERS}]",
)
@click.option(
    "--queue", default=DEFAULT_QUEUE, help=f"Batch queue [default: {DEFAULT_QUEUE}]"
)
@click.option(
    "--seqs-per-chunk",
    default=DEFAULT_SEQS_PER_CHUNK,
    type=int,
    help=f"Sequences per chunk [default: {DEFAULT_SEQS_PER_CHUNK}]",
)
@click.option(
    "--local",
    "run_local",
    is_flag=True,
    help="Run single chunk locally instead of Batch",
)
@click.option(
    "--shell", "run_shell", is_flag=True, help="Drop into container shell for debugging"
)
@click.option("--dry-run", is_flag=True, help="Show plan without submitting")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def embed_t5(
    input_fasta,
    workers,
    queue,
    seqs_per_chunk,
    run_local,
    run_shell,
    dry_run,
    base_path,
):
    """Generate T5 protein embeddings for a FASTA file.

    Splits the input FASTA into chunks and processes them in parallel using
    AWS Batch array jobs. Each worker generates embeddings for its chunk
    and writes an H5 file.

    \b
    Examples:
      # Submit to AWS Batch with 50 workers
      dh batch embed-t5 /primordial/proteins.fasta --workers 50

      # Use a faster queue with more workers
      dh batch embed-t5 /primordial/big.fasta --workers 100 --queue a10g-1x-spot

      # Test locally with a single chunk
      dh batch embed-t5 /primordial/test.fasta --local

      # Debug by dropping into container shell
      dh batch embed-t5 /primordial/test.fasta --shell

    \b
    After job completes:
      dh batch status <job-id>                      # Check status
      dh batch finalize <job-id> --output out.h5   # Combine results
    """
    input_path = Path(input_fasta).resolve()

    if run_shell:
        _run_shell_mode(input_path)
        return

    if run_local:
        _run_local_mode(input_path)
        return

    # Batch submission mode
    _submit_batch_job(input_path, workers, queue, seqs_per_chunk, dry_run, base_path)


def _count_sequences(fasta_path: Path) -> int:
    """Count sequences in a FASTA file (fast, just counts > lines)."""
    count = 0
    with open(fasta_path) as f:
        for line in f:
            if line.startswith(">"):
                count += 1
    return count


def _split_fasta(input_path: Path, output_dir: Path, seqs_per_chunk: int) -> int:
    """Split FASTA file into chunks.

    Returns:
        Number of chunks created
    """
    from dayhoff_tools.fasta import split_fasta

    num_chunks = split_fasta(
        fasta_file=str(input_path),
        target_folder=str(output_dir),
        base_name="chunk",
        sequences_per_file=seqs_per_chunk,
        show_progress=True,
    )

    # Rename files to use zero-padded indices (chunk_000.fasta, etc.)
    for i in range(1, num_chunks + 1):
        old_name = output_dir / f"chunk_{i}.fasta"
        new_name = output_dir / f"chunk_{i-1:03d}.fasta"
        if old_name.exists():
            old_name.rename(new_name)

    return num_chunks


def _submit_batch_job(
    input_path: Path,
    workers: int,
    queue: str,
    seqs_per_chunk: int,
    dry_run: bool,
    base_path: str,
):
    """Submit embedding job to AWS Batch."""
    # Count sequences
    click.echo(f"Counting sequences in {input_path}...")
    num_sequences = _count_sequences(input_path)
    click.echo(f"Found {num_sequences:,} sequences")

    if num_sequences == 0:
        click.echo(
            click.style("Error: No sequences found in input file", fg="red"), err=True
        )
        raise SystemExit(1)

    # Calculate chunks
    num_chunks = min((num_sequences + seqs_per_chunk - 1) // seqs_per_chunk, workers)
    actual_seqs_per_chunk = (num_sequences + num_chunks - 1) // num_chunks

    # Generate job ID
    job_id = generate_job_id("embed")

    # Show plan
    click.echo()
    click.echo(f"Job ID:           {job_id}")
    click.echo(f"Input:            {input_path}")
    click.echo(f"Sequences:        {num_sequences:,}")
    click.echo(f"Chunks:           {num_chunks}")
    click.echo(f"Seqs per chunk:   ~{actual_seqs_per_chunk:,}")
    click.echo(f"Queue:            {queue}")
    click.echo(f"Job definition:   {DEFAULT_JOB_DEFINITION}")

    if dry_run:
        click.echo()
        click.echo(click.style("Dry run - job not submitted", fg="yellow"))
        return

    click.echo()

    # Create job directory
    job_dir = create_job_directory(job_id, base_path)
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"

    click.echo(f"Created job directory: {job_dir}")

    # Split FASTA into chunks
    click.echo("Splitting FASTA into chunks...")
    actual_chunks = _split_fasta(input_path, input_dir, actual_seqs_per_chunk)
    click.echo(f"Created {actual_chunks} chunks")

    # Create manifest
    manifest = JobManifest(
        job_id=job_id,
        user=job_id.split("-")[0],
        pipeline="embed-t5",
        status=JobStatus.PENDING,
        image_uri=DEFAULT_IMAGE_URI,
        input=InputConfig(
            source=str(input_path),
            num_sequences=num_sequences,
            num_chunks=actual_chunks,
            sequences_per_chunk=actual_seqs_per_chunk,
        ),
        batch=BatchConfig(
            queue=queue,
            job_definition=DEFAULT_JOB_DEFINITION,
            array_size=actual_chunks,
        ),
        output=OutputConfig(
            destination=None,
            finalized=False,
        ),
    )

    save_manifest(manifest, base_path)

    # Submit to AWS Batch
    try:
        client = BatchClient()

        environment = {
            "JOB_DIR": str(job_dir),
            "JOB_ID": job_id,
        }

        batch_job_id = client.submit_job(
            job_name=job_id,
            job_definition=DEFAULT_JOB_DEFINITION,
            job_queue=queue,
            array_size=actual_chunks,
            environment=environment,
            timeout_seconds=6 * 3600,  # 6 hours
            retry_attempts=3,
        )

        # Update manifest
        manifest.status = JobStatus.SUBMITTED
        manifest.batch.job_id = batch_job_id
        save_manifest(manifest, base_path)

        click.echo()
        click.echo(click.style("✓ Job submitted successfully!", fg="green"))
        click.echo()
        click.echo(f"AWS Batch Job ID: {batch_job_id}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  Check status:  dh batch status {job_id}")
        click.echo(f"  View logs:     dh batch logs {job_id}")
        click.echo(f"  Cancel:        dh batch cancel {job_id}")
        click.echo()
        click.echo("After completion:")
        click.echo(
            f"  Finalize:      dh batch finalize {job_id} --output /primordial/embeddings.h5"
        )

    except BatchError as e:
        manifest.status = JobStatus.FAILED
        manifest.error_message = str(e)
        save_manifest(manifest, base_path)
        click.echo(click.style(f"✗ Failed to submit job: {e}", fg="red"), err=True)
        raise SystemExit(1)


def _run_local_mode(input_path: Path):
    """Run embedding locally in a Docker container.

    This runs the embed container with the normal entrypoint, processing
    a single chunk (index 0) for testing purposes.
    """
    click.echo("Running T5 embedding locally in container...")
    click.echo(f"Input: {input_path}")

    input_dir = input_path.parent

    # Create a temporary job directory structure in the input directory
    # The worker expects JOB_DIR/input/chunk_000.fasta format
    temp_job_dir = input_dir / ".local_embed_job"
    temp_input_dir = temp_job_dir / "input"
    temp_output_dir = temp_job_dir / "output"

    # Clean up any previous run
    if temp_job_dir.exists():
        shutil.rmtree(temp_job_dir)

    temp_input_dir.mkdir(parents=True)
    temp_output_dir.mkdir(parents=True)

    # Symlink or copy the input file as chunk_000.fasta
    chunk_path = temp_input_dir / "chunk_000.fasta"
    chunk_path.symlink_to(input_path.resolve())

    click.echo(f"Output will be at: {temp_output_dir}/embed_000.h5")
    click.echo()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "-v",
        "/primordial:/primordial",
        "-v",
        f"{temp_job_dir}:{temp_job_dir}",
        "-e",
        f"JOB_DIR={temp_job_dir}",
        "-e",
        "AWS_BATCH_JOB_ARRAY_INDEX=0",
        DEFAULT_IMAGE_URI,
    ]

    click.echo(f"Running: {' '.join(cmd)}")
    click.echo()

    try:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            click.echo(
                click.style(
                    f"Container exited with code {result.returncode}", fg="red"
                ),
                err=True,
            )
            raise SystemExit(result.returncode)

        # Check for output
        output_file = temp_output_dir / "embed_000.h5"
        if output_file.exists():
            # Move output to final location
            final_output = input_path.with_suffix(".h5")
            shutil.move(str(output_file), str(final_output))
            click.echo()
            click.echo(click.style("✓ Embedding complete!", fg="green"))
            click.echo(f"Output: {final_output}")
        else:
            click.echo(click.style("Warning: No output file found", fg="yellow"))

        # Clean up temp directory
        shutil.rmtree(temp_job_dir, ignore_errors=True)

    except FileNotFoundError:
        click.echo(
            click.style(
                "Error: Docker not found. Is Docker installed and running?", fg="red"
            ),
            err=True,
        )
        raise SystemExit(1)


def _run_shell_mode(input_path: Path):
    """Drop into container shell for debugging."""
    click.echo("Dropping into container shell...")
    click.echo(f"Input will be available at: /input/{input_path.name}")
    click.echo()

    input_dir = input_path.parent

    cmd = [
        "docker",
        "run",
        "--rm",
        "-it",
        "--gpus",
        "all",
        "-v",
        "/primordial:/primordial",
        "-v",
        f"{input_dir}:/input",
        "-e",
        "JOB_DIR=/input",
        "-e",
        "AWS_BATCH_JOB_ARRAY_INDEX=0",
        "--entrypoint",
        "/bin/bash",
        DEFAULT_IMAGE_URI,
    ]

    click.echo(f"Running: {' '.join(cmd)}")
    click.echo()

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        click.echo(
            click.style(
                "Error: Docker not found. Is Docker installed and running?", fg="red"
            ),
            err=True,
        )
        raise SystemExit(1)
