"""Boltz structure prediction pipeline command."""

import os
import shutil
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

# Default settings for Boltz
# NOTE: A10G would be preferred (24GB vs 16GB VRAM) but has a bug.
# Using T4 until A10G is debugged. See new_batch.md Known Issues.
DEFAULT_QUEUE = "t4-1x-spot"
DEFAULT_WORKERS = 50
DEFAULT_JOB_DEFINITION = "dayhoff-boltz"
DEFAULT_IMAGE_URI = "074735440724.dkr.ecr.us-east-1.amazonaws.com/dayhoff:boltz-latest"


@click.command()
@click.argument("input_dir", type=click.Path(exists=True))
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
    "--msa-dir",
    type=click.Path(exists=True),
    help="Path to pre-computed MSA files (optional)",
)
@click.option(
    "--local",
    "run_local",
    is_flag=True,
    help="Run single complex locally instead of Batch",
)
@click.option(
    "--shell", "run_shell", is_flag=True, help="Drop into container shell for debugging"
)
@click.option("--dry-run", is_flag=True, help="Show plan without submitting")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def boltz(input_dir, workers, queue, msa_dir, run_local, run_shell, dry_run, base_path):
    """Predict protein structures with Boltz.

    Processes a directory of YAML config files, each defining a protein complex.
    Each YAML file is processed independently in parallel using AWS Batch array jobs.

    \b
    Examples:
      # Submit to AWS Batch with 100 workers
      dh batch boltz /primordial/complexes/ --workers 100

      # Include pre-computed MSA files
      dh batch boltz /primordial/complexes/ --workers 50 --msa-dir /primordial/msas/

      # Test locally with a single complex
      dh batch boltz /primordial/complexes/ --local

      # Debug by dropping into container shell
      dh batch boltz /primordial/complexes/ --shell

    \b
    After job completes:
      dh batch status <job-id>                          # Check status
      dh batch finalize <job-id> --output /primordial/structures/  # Move results

    \b
    YAML config format:
      version: 1
      sequences:
        - protein:
            id: A
            sequence: MKTVRQERLKSIVRILERSKEPVSGAQ...
        - ligand:
            id: B
            smiles: CCO
    """
    input_path = Path(input_dir).resolve()

    if run_shell:
        _run_shell_mode(input_path)
        return

    if run_local:
        _run_local_mode(input_path)
        return

    # Batch submission mode
    _submit_batch_job(input_path, workers, queue, msa_dir, dry_run, base_path)


def _count_yaml_files(input_path: Path) -> int:
    """Count YAML files in directory."""
    return len(list(input_path.glob("*.yaml")))


def _copy_inputs_to_job_dir(input_path: Path, job_dir: Path) -> int:
    """Copy input YAML files to job directory.

    Returns:
        Number of files copied
    """
    input_dir = job_dir / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for yaml_file in sorted(input_path.glob("*.yaml")):
        dest = input_dir / yaml_file.name
        shutil.copy2(yaml_file, dest)
        count += 1

    return count


def _submit_batch_job(
    input_path: Path,
    workers: int,
    queue: str,
    msa_dir: str | None,
    dry_run: bool,
    base_path: str,
):
    """Submit Boltz job to AWS Batch."""
    # Count input files
    click.echo(f"Scanning {input_path} for YAML files...")
    num_files = _count_yaml_files(input_path)

    if num_files == 0:
        click.echo(
            click.style("Error: No YAML files found in input directory", fg="red"),
            err=True,
        )
        raise SystemExit(1)

    click.echo(f"Found {num_files} complexes to predict")

    # Calculate array size
    array_size = min(num_files, workers)

    # Generate job ID
    job_id = generate_job_id("boltz")

    # Show plan
    click.echo()
    click.echo(f"Job ID:           {job_id}")
    click.echo(f"Input:            {input_path}")
    click.echo(f"Complexes:        {num_files}")
    click.echo(f"Array Size:       {array_size}")
    click.echo(f"Queue:            {queue}")
    click.echo(f"Job definition:   {DEFAULT_JOB_DEFINITION}")
    if msa_dir:
        click.echo(f"MSA directory:    {msa_dir}")

    if dry_run:
        click.echo()
        click.echo(click.style("Dry run - job not submitted", fg="yellow"))
        return

    click.echo()

    # Create job directory
    job_dir = create_job_directory(job_id, base_path)
    click.echo(f"Created job directory: {job_dir}")

    # Copy input files
    click.echo("Copying input files...")
    copied = _copy_inputs_to_job_dir(input_path, job_dir)
    click.echo(f"Copied {copied} YAML files")

    # Copy or symlink MSA directory if provided
    if msa_dir:
        msa_dest = job_dir / "msas"
        msa_src = Path(msa_dir)

        # If on same filesystem (Primordial), symlink; otherwise copy
        try:
            msa_dest.symlink_to(msa_src)
            click.echo(f"Linked MSA directory: {msa_dir}")
        except OSError:
            click.echo("Copying MSA directory (this may take a while)...")
            shutil.copytree(msa_src, msa_dest)
            click.echo(f"Copied MSA directory")

    # Create manifest
    manifest = JobManifest(
        job_id=job_id,
        user=job_id.split("-")[0],
        pipeline="boltz",
        status=JobStatus.PENDING,
        image_uri=DEFAULT_IMAGE_URI,
        input=InputConfig(
            source=str(input_path),
            num_sequences=num_files,  # Using num_sequences field for num_complexes
            num_chunks=array_size,
        ),
        batch=BatchConfig(
            queue=queue,
            job_definition=DEFAULT_JOB_DEFINITION,
            array_size=array_size,
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
            "BOLTZ_CACHE": "/primordial/.cache/boltz",
            "MSA_DIR": "/primordial/.cache/msas",
            "BATCH_ARRAY_SIZE": str(array_size),
            "BATCH_NUM_FILES": str(num_files),
        }

        batch_job_id = client.submit_job(
            job_name=job_id,
            job_definition=DEFAULT_JOB_DEFINITION,
            job_queue=queue,
            array_size=array_size,
            environment=environment,
            timeout_seconds=12 * 3600,  # 12 hours (Boltz can be slow)
            retry_attempts=2,  # Fewer retries for expensive jobs
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
            f"  Finalize:      dh batch finalize {job_id} --output /primordial/structures/"
        )

    except BatchError as e:
        manifest.status = JobStatus.FAILED
        manifest.error_message = str(e)
        save_manifest(manifest, base_path)
        click.echo(click.style(f"✗ Failed to submit job: {e}", fg="red"), err=True)
        raise SystemExit(1)


def _run_local_mode(input_path: Path):
    """Run Boltz locally in a Docker container.

    This runs the boltz container with the normal entrypoint, processing
    the first YAML file (index 0) for testing purposes.
    """
    import subprocess

    click.echo("Running Boltz locally in container...")
    click.echo(f"Input directory: {input_path}")

    # Find YAML files
    yaml_files = list(input_path.glob("*.yaml"))
    if not yaml_files:
        click.echo(click.style("Error: No YAML files found", fg="red"), err=True)
        raise SystemExit(1)

    click.echo(
        f"Found {len(yaml_files)} YAML files, will process: {yaml_files[0].name}"
    )

    # Create a temporary job directory structure
    temp_job_dir = input_path / ".local_boltz_job"
    temp_input_dir = temp_job_dir / "input"
    temp_output_dir = temp_job_dir / "output"

    # Clean up any previous run
    if temp_job_dir.exists():
        shutil.rmtree(temp_job_dir)

    temp_input_dir.mkdir(parents=True)
    temp_output_dir.mkdir(parents=True)

    # Copy YAML files to input directory
    for yaml_file in yaml_files:
        shutil.copy2(yaml_file, temp_input_dir / yaml_file.name)

    click.echo(f"Output will be at: {temp_output_dir}/")
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
        "-e",
        "BOLTZ_CACHE=/primordial/.cache/boltz",
        "-e",
        "MSA_DIR=/primordial/.cache/msas",
        "-e",
        "BOLTZ_OPTIONS=--no_kernels",
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
        output_dirs = (
            list(temp_output_dir.iterdir()) if temp_output_dir.exists() else []
        )
        if output_dirs:
            click.echo()
            click.echo(click.style("✓ Prediction complete!", fg="green"))
            click.echo(f"Output directory: {temp_output_dir}")
            for d in output_dirs:
                click.echo(f"  - {d.name}")
        else:
            click.echo(click.style("Warning: No output found", fg="yellow"))

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
    import subprocess

    click.echo("Dropping into container shell...")
    click.echo(f"Input will be available at: /input/")
    click.echo()

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
        f"{input_path}:/input",
        "-e",
        "JOB_DIR=/input",
        "-e",
        "AWS_BATCH_JOB_ARRAY_INDEX=0",
        "-e",
        "BOLTZ_CACHE=/primordial/.cache/boltz",
        "-e",
        "MSA_DIR=/primordial/.cache/msas",
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
