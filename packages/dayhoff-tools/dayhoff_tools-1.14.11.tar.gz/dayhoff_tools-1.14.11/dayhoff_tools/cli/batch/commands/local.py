"""Local command for debugging job chunks locally."""

import subprocess

import click

from ..manifest import BATCH_JOBS_BASE, get_job_dir, load_manifest


@click.command()
@click.argument("job_id")
@click.option("--index", required=True, type=int, help="Array index to run")
@click.option(
    "--shell",
    "run_shell",
    is_flag=True,
    help="Drop into shell instead of running command",
)
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def local(job_id, index, run_shell, base_path):
    """Run a job chunk locally for debugging.

    Runs a specific array index of a job in a local Docker container,
    allowing you to debug failed chunks or test changes.

    \b
    Examples:
      dh batch local dma-embed-20260109-a3f2 --index 27
      dh batch local dma-embed-20260109-a3f2 --index 27 --shell
    """
    # Load manifest
    try:
        manifest = load_manifest(job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {job_id}", err=True)
        raise SystemExit(1)

    # Get job directory and image
    job_dir = get_job_dir(job_id, base_path)
    image_uri = manifest.image_uri

    if not image_uri:
        click.echo("Job has no image URI, cannot run locally.", err=True)
        raise SystemExit(1)

    # Validate index
    if manifest.input and manifest.input.num_chunks:
        if index >= manifest.input.num_chunks:
            click.echo(
                f"Index {index} out of range. Job has {manifest.input.num_chunks} chunks (0-{manifest.input.num_chunks - 1}).",
                err=True,
            )
            raise SystemExit(1)

    click.echo(f"Running job {job_id} index {index} locally")
    click.echo(f"Image: {image_uri}")
    click.echo(f"Job directory: {job_dir}")
    click.echo()

    # Build Docker command
    cmd = [
        "docker",
        "run",
        "--rm",
        "--gpus",
        "all",
        "-v",
        "/primordial:/primordial",
        "-v",
        f"{job_dir}:{job_dir}",
        "-e",
        f"AWS_BATCH_JOB_ARRAY_INDEX={index}",
        "-e",
        f"JOB_DIR={job_dir}",
        "-e",
        f"JOB_ID={job_id}",
    ]

    if run_shell:
        cmd.extend(["-it", "--entrypoint", "/bin/bash"])
        click.echo("Dropping into container shell...")
        click.echo(f"  JOB_DIR={job_dir}")
        click.echo(f"  AWS_BATCH_JOB_ARRAY_INDEX={index}")
    else:
        click.echo("Running worker command...")

    cmd.append(image_uri)

    click.echo()
    click.echo(f"Command: {' '.join(cmd)}")
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
        else:
            click.echo(click.style("✓ Container completed successfully", fg="green"))
    except FileNotFoundError:
        click.echo(
            click.style(
                "Error: Docker not found. Is Docker installed and running?", fg="red"
            ),
            err=True,
        )
        raise SystemExit(1)
