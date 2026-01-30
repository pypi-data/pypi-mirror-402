"""Submit command for generic batch jobs."""

import os
from pathlib import Path

import click
import yaml

from ..aws_batch import BatchClient, BatchError
from ..job_id import generate_job_id
from ..manifest import (
    BATCH_JOBS_BASE,
    BatchConfig,
    InputConfig,
    JobManifest,
    JobStatus,
    create_job_directory,
    save_manifest,
)


# Default job definition for generic jobs
DEFAULT_JOB_DEFINITION = "dayhoff-batch-base"
DEFAULT_QUEUE = "t4-1x-spot"


@click.command()
@click.option(
    "-f", "--file", "config_file", type=click.Path(exists=True), help="Config file path"
)
@click.option("--command", help="Command to run (alternative to config file)")
@click.option(
    "--queue", default=DEFAULT_QUEUE, help=f"Batch queue [default: {DEFAULT_QUEUE}]"
)
@click.option("--memory", default="30G", help="Memory limit (e.g., 30G)")
@click.option("--vcpus", default=8, type=int, help="Number of vCPUs")
@click.option("--gpus", default=1, type=int, help="Number of GPUs")
@click.option("--array", default=1, type=int, help="Number of array tasks")
@click.option("--retry", default=3, type=int, help="Retry attempts")
@click.option("--timeout", default="6h", help="Job timeout (e.g., 6h, 1d)")
@click.option("--image", help="Pre-built image URI")
@click.option("--env", multiple=True, help="Environment variables (KEY=VALUE)")
@click.option("--dry-run", is_flag=True, help="Show plan without submitting")
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def submit(
    config_file,
    command,
    queue,
    memory,
    vcpus,
    gpus,
    array,
    retry,
    timeout,
    image,
    env,
    dry_run,
    base_path,
):
    """Submit a custom batch job.

    Jobs can be defined via a config file (-f) or inline options.

    \b
    Examples:
      # Submit from config file
      dh batch submit -f config.yaml

      # Submit with inline command
      dh batch submit --command "python train.py --epochs 100" --queue a10g-1x-spot

      # Array job
      dh batch submit -f config.yaml --array 10

    \b
    Config file format (YAML):
      command: python scripts/train.py --epochs 100
      queue: t4-1x-spot
      memory: 30G
      vcpus: 8
      gpus: 1
      array: 10
      retry: 3
      timeout: 6h
      image: custom-image:tag
      env:
        MY_VAR: value
    """
    # Parse config file if provided
    config = {}
    if config_file:
        with open(config_file) as f:
            config = yaml.safe_load(f)

    # Override with command-line options
    job_command = command or config.get("command")
    if not job_command:
        raise click.UsageError(
            "Must specify --command or provide config file with 'command' field"
        )

    job_queue = queue if queue != DEFAULT_QUEUE else config.get("queue", queue)
    job_memory = memory if memory != "30G" else config.get("memory", memory)
    job_vcpus = vcpus if vcpus != 8 else config.get("vcpus", vcpus)
    job_gpus = gpus if gpus != 1 else config.get("gpus", gpus)
    job_array = array if array != 1 else config.get("array", array)
    job_retry = retry if retry != 3 else config.get("retry", retry)
    job_timeout = timeout if timeout != "6h" else config.get("timeout", timeout)
    job_image = image or config.get("image")

    # Parse environment variables
    job_env = dict(config.get("env", {}))
    for e in env:
        if "=" in e:
            key, value = e.split("=", 1)
            job_env[key] = value

    # Generate job ID
    job_id = generate_job_id("batch")

    # Parse timeout
    timeout_seconds = _parse_timeout(job_timeout)

    # Show plan
    click.echo()
    click.echo(f"Job ID:      {job_id}")
    click.echo(f"Command:     {job_command}")
    click.echo(f"Queue:       {job_queue}")
    click.echo(f"Resources:   {job_vcpus} vCPUs, {job_memory} memory, {job_gpus} GPUs")
    click.echo(f"Array Size:  {job_array}")
    click.echo(f"Retry:       {job_retry}")
    click.echo(f"Timeout:     {job_timeout} ({timeout_seconds}s)")
    if job_image:
        click.echo(f"Image:       {job_image}")
    if job_env:
        click.echo(f"Environment: {len(job_env)} variables")

    if dry_run:
        click.echo()
        click.echo(click.style("Dry run - job not submitted", fg="yellow"))
        return

    click.echo()

    # Create job directory and manifest
    job_dir = create_job_directory(job_id, base_path)
    click.echo(f"Created job directory: {job_dir}")

    manifest = JobManifest(
        job_id=job_id,
        user=job_id.split("-")[0],  # Extract username from job ID
        pipeline="batch",
        status=JobStatus.PENDING,
        command=job_command,
        image_uri=job_image,
        batch=BatchConfig(
            queue=job_queue,
            array_size=job_array if job_array > 1 else None,
        ),
    )

    # Submit to AWS Batch
    try:
        client = BatchClient()

        # Prepare environment
        submit_env = {
            "JOB_DIR": str(job_dir),
            "JOB_ID": job_id,
            **job_env,
        }

        batch_job_id = client.submit_job(
            job_name=job_id,
            job_definition=job_image or DEFAULT_JOB_DEFINITION,
            job_queue=job_queue,
            array_size=job_array if job_array > 1 else None,
            environment=submit_env,
            timeout_seconds=timeout_seconds,
            retry_attempts=job_retry,
        )

        # Update manifest with Batch job ID
        manifest.status = JobStatus.SUBMITTED
        manifest.batch.job_id = batch_job_id
        save_manifest(manifest, base_path)

        click.echo(click.style("✓ Job submitted successfully!", fg="green"))
        click.echo()
        click.echo(f"AWS Batch Job ID: {batch_job_id}")
        click.echo()
        click.echo("Next steps:")
        click.echo(f"  Check status: dh batch status {job_id}")
        click.echo(f"  View logs:    dh batch logs {job_id}")
        click.echo(f"  Cancel:       dh batch cancel {job_id}")

    except BatchError as e:
        manifest.status = JobStatus.FAILED
        manifest.error_message = str(e)
        save_manifest(manifest, base_path)
        click.echo(click.style(f"✗ Failed to submit job: {e}", fg="red"), err=True)
        raise SystemExit(1)


def _parse_timeout(timeout_str: str) -> int:
    """Parse timeout string to seconds.

    Supports formats like: 6h, 1d, 30m, 3600
    """
    timeout_str = timeout_str.strip().lower()

    if timeout_str.endswith("h"):
        return int(timeout_str[:-1]) * 3600
    elif timeout_str.endswith("d"):
        return int(timeout_str[:-1]) * 86400
    elif timeout_str.endswith("m"):
        return int(timeout_str[:-1]) * 60
    elif timeout_str.endswith("s"):
        return int(timeout_str[:-1])
    else:
        return int(timeout_str)
