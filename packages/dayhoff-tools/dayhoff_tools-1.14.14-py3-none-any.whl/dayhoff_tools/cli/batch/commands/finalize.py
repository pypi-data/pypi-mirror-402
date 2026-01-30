"""Finalize command for combining results and cleaning up."""

import shutil
from pathlib import Path

import click

from ..manifest import (
    BATCH_JOBS_BASE,
    JobStatus,
    delete_job_directory,
    get_job_dir,
    load_manifest,
    save_manifest,
)


@click.command()
@click.argument("job_id")
@click.option(
    "--output",
    required=True,
    type=click.Path(),
    help="Output path for combined results",
)
@click.option("--force", is_flag=True, help="Finalize even if some chunks failed")
@click.option(
    "--keep-intermediates",
    is_flag=True,
    help="Don't delete job directory after finalizing",
)
@click.option(
    "--full-output",
    is_flag=True,
    help="For Boltz: copy entire output directory (default: only essential files)",
)
@click.option(
    "--skip-dedup",
    is_flag=True,
    help="Skip deduplication step (use if input has no duplicates)",
)
@click.option("--base-path", default=BATCH_JOBS_BASE, help="Base path for job data")
def finalize(job_id, output, force, keep_intermediates, full_output, skip_dedup, base_path):
    """Combine results and clean up job intermediates.

    For embedding jobs, combines H5 files into a single output file.
    For Boltz jobs, extracts essential files (CIF structures and confidence JSON).

    \b
    Examples:
      # Embedding job - combine H5 files
      dh batch finalize dma-embed-20260109-a3f2 --output /primordial/embeddings.h5

      # Skip deduplication (faster if input has no duplicates)
      dh batch finalize dma-embed-20260109-a3f2 --output /primordial/embeddings.h5 --skip-dedup

      # Boltz job - extract essential files only (default)
      dh batch finalize dma-boltz-20260113-190a --output /primordial/structures/

      # Boltz job - copy all output files
      dh batch finalize dma-boltz-20260113-190a --output /primordial/structures/ --full-output

      # Keep job directory after finalizing
      dh batch finalize dma-embed-20260109-a3f2 --output /primordial/out.h5 --keep-intermediates
    """
    # Load manifest
    try:
        manifest = load_manifest(job_id, base_path)
    except FileNotFoundError:
        click.echo(f"Job not found: {job_id}", err=True)
        raise SystemExit(1)

    # Check job status
    if manifest.status == JobStatus.FINALIZED:
        click.echo(f"Job {job_id} is already finalized.", err=True)
        raise SystemExit(1)

    job_dir = get_job_dir(job_id, base_path)
    output_dir = job_dir / "output"
    output_path = Path(output).resolve()

    # Check completion status
    incomplete = _check_completion(job_id, base_path)
    if incomplete:
        click.echo(f"Found {len(incomplete)} incomplete chunks: {incomplete[:10]}...")
        if not force:
            click.echo()
            click.echo("Use --force to finalize anyway, or retry failed chunks:")
            click.echo(f"  dh batch retry {job_id}")
            raise SystemExit(1)
        click.echo()
        click.echo(
            click.style("Warning: Finalizing with incomplete chunks", fg="yellow")
        )

    # Update status
    manifest.status = JobStatus.FINALIZING
    save_manifest(manifest, base_path)

    # Finalize based on pipeline type
    click.echo()
    if manifest.pipeline in ("embed-t5", "embed"):
        _finalize_embeddings(output_dir, output_path, skip_dedup=skip_dedup)
    elif manifest.pipeline == "boltz":
        _finalize_boltz(output_dir, output_path, full_output=full_output)
    else:
        _finalize_generic(output_dir, output_path)

    # Update manifest
    manifest.status = JobStatus.FINALIZED
    if manifest.output:
        manifest.output.destination = str(output_path)
        manifest.output.finalized = True
    save_manifest(manifest, base_path)

    click.echo()
    click.echo(click.style(f"✓ Results saved to: {output_path}", fg="green"))

    # Clean up
    if not keep_intermediates:
        click.echo(f"Cleaning up job directory: {job_dir}")
        delete_job_directory(job_id, base_path)
        click.echo(click.style("✓ Job directory deleted", fg="green"))
    else:
        click.echo(f"Job directory preserved: {job_dir}")


def _check_completion(job_id: str, base_path: str) -> list[int]:
    """Check which chunks are incomplete (no .done marker).

    Handles both original chunks (chunk_000.fasta) and resliced chunks
    (chunk_r1_000.fasta). For original chunks that were resliced in a retry,
    checks if all resliced chunks completed.
    """
    job_dir = get_job_dir(job_id, base_path)
    input_dir = job_dir / "input"
    output_dir = job_dir / "output"

    if not input_dir.exists():
        return []

    # Load manifest to check for resliced retries
    try:
        manifest = load_manifest(job_id, base_path)
        resliced_indices: set[int] = set()
        reslice_info: dict[str, int] = {}  # prefix -> expected count

        for retry in manifest.retries:
            if retry.reslice_prefix and retry.reslice_count:
                resliced_indices.update(retry.indices)
                reslice_info[retry.reslice_prefix] = retry.reslice_count
    except FileNotFoundError:
        resliced_indices = set()
        reslice_info = {}

    incomplete = []

    # Check original chunks (chunk_000.fasta pattern)
    for chunk_path in sorted(input_dir.glob("chunk_[0-9][0-9][0-9].fasta")):
        idx_str = chunk_path.stem.split("_")[1]
        idx = int(idx_str)

        # Check for original done marker
        done_marker = output_dir / f"embed_{idx:03d}.done"
        if done_marker.exists():
            continue

        # Check if this chunk was resliced
        if idx in resliced_indices:
            # Find which retry covered this index and check if complete
            is_covered = False
            for retry in manifest.retries:
                if (
                    retry.reslice_prefix
                    and retry.reslice_count
                    and idx in retry.indices
                ):
                    # Check if all resliced chunks for this retry completed
                    done_count = len(
                        list(output_dir.glob(f"embed_{retry.reslice_prefix}_*.done"))
                    )
                    if done_count >= retry.reslice_count:
                        is_covered = True
                        break
            if is_covered:
                continue

        incomplete.append(idx)

    return incomplete


def _finalize_embeddings(output_dir: Path, output_path: Path, skip_dedup: bool = False):
    """Combine H5 embedding files into a single output."""
    h5_files = sorted(output_dir.glob("embed_*.h5"))

    if not h5_files:
        click.echo("No H5 files found in output directory.", err=True)
        raise SystemExit(1)

    click.echo(f"Found {len(h5_files)} H5 files to combine")
    if skip_dedup:
        click.echo("Skipping deduplication (--skip-dedup)")

    # Check if output already exists
    if output_path.exists():
        click.echo(f"Output file already exists: {output_path}", err=True)
        raise SystemExit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from dayhoff_tools.h5 import (
            combine_h5_files,
            deduplicate_h5_file,
            optimize_protein_embedding_chunks,
        )
        import tempfile

        if len(h5_files) == 1:
            # Single file - just copy, no need to combine/dedup/optimize
            click.echo("Single chunk - copying directly...")
            shutil.copy2(h5_files[0], output_path)
        else:
            # Multiple files - combine and optionally deduplicate
            with tempfile.TemporaryDirectory() as tmpdir:
                combined_path = Path(tmpdir) / "combined.h5"

                # Combine H5 files
                click.echo("Combining H5 files...")
                h5_file_paths = [str(f) for f in h5_files]
                combine_h5_files(
                    input_files=h5_file_paths,
                    output_file=str(combined_path),
                )

                if skip_dedup:
                    # Skip dedup - optimize directly from combined
                    click.echo("Optimizing chunks...")
                    optimize_protein_embedding_chunks(str(combined_path), str(output_path))
                else:
                    # Full pipeline: combine -> dedup -> optimize
                    deduped_path = Path(tmpdir) / "deduped.h5"
                    click.echo("Deduplicating...")
                    deduplicate_h5_file(str(combined_path), str(deduped_path))
                    click.echo("Optimizing chunks...")
                    optimize_protein_embedding_chunks(str(deduped_path), str(output_path))

        click.echo(click.style("✓ H5 files combined successfully", fg="green"))

    except ImportError:
        # Fall back to simple concatenation
        click.echo("h5 module not available, using simple copy...")
        if len(h5_files) == 1:
            shutil.copy2(h5_files[0], output_path)
        else:
            # For multiple files without h5 module, just copy first file
            # This is a fallback - the h5 module should be available
            click.echo(
                click.style(
                    "Warning: Cannot combine multiple H5 files without dayhoff_tools.h5 module. "
                    "Only copying first file.",
                    fg="yellow",
                )
            )
            shutil.copy2(h5_files[0], output_path)


def _finalize_boltz(output_dir: Path, output_path: Path, full_output: bool = False):
    """Move Boltz output to destination.
    
    Args:
        output_dir: Source directory containing boltz_results_* folders
        output_path: Destination directory for outputs
        full_output: If True, copy entire output directories. If False (default),
                    extract only essential files (CIF structures and confidence JSON).
    """
    # Find all output directories (one per complex)
    complex_dirs = [d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("boltz_results_")]

    if not complex_dirs:
        click.echo("No output directories found.", err=True)
        raise SystemExit(1)

    click.echo(f"Found {len(complex_dirs)} structure predictions")
    
    if full_output:
        click.echo("Mode: Copying full output (all files)")
    else:
        click.echo("Mode: Extracting essential files only (CIF + confidence JSON)")
        click.echo("       Use --full-output to copy all files")
    
    # Confirm before proceeding
    click.echo()
    if not click.confirm(f"Copy results to {output_path}?"):
        click.echo("Cancelled.")
        raise SystemExit(0)

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    skipped_count = 0
    
    for complex_dir in complex_dirs:
        complex_name = complex_dir.name.replace("boltz_results_", "")
        dest = output_path / complex_name
        
        if dest.exists():
            click.echo(f"  Skipping {complex_name} (already exists)")
            skipped_count += 1
            continue
        
        if full_output:
            # Copy entire directory
            shutil.copytree(complex_dir, dest)
            click.echo(f"  Copied {complex_name} (full output)")
        else:
            # Extract only essential files
            _extract_essential_boltz_files(complex_dir, dest, complex_name)
            click.echo(f"  Extracted {complex_name} (essential files)")
        
        copied_count += 1

    click.echo()
    if skipped_count > 0:
        click.echo(f"Copied {copied_count} predictions, skipped {skipped_count} existing")
    else:
        click.echo(click.style(f"✓ Copied {copied_count} structure predictions successfully", fg="green"))


def _extract_essential_boltz_files(source_dir: Path, dest_dir: Path, complex_name: str):
    """Extract only essential files from Boltz output.
    
    Essential files are:
    - predictions/*/*.cif (structure files)
    - predictions/*/confidence_*.json (confidence metrics)
    
    Args:
        source_dir: Source boltz_results_* directory
        dest_dir: Destination directory to create
        complex_name: Name of the complex (for better error messages)
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    predictions_dir = source_dir / "predictions"
    if not predictions_dir.exists():
        click.echo(f"    Warning: No predictions directory found for {complex_name}", err=True)
        return
    
    # Find all subdirectories in predictions/ (usually just one named after the complex)
    for pred_subdir in predictions_dir.iterdir():
        if not pred_subdir.is_dir():
            continue
        
        # Copy CIF files (structures)
        for cif_file in pred_subdir.glob("*.cif"):
            shutil.copy2(cif_file, dest_dir / cif_file.name)
        
        # Copy confidence JSON files
        for json_file in pred_subdir.glob("confidence_*.json"):
            shutil.copy2(json_file, dest_dir / json_file.name)


def _finalize_generic(output_dir: Path, output_path: Path):
    """Generic finalization - copy output directory."""
    if output_path.exists():
        click.echo(f"Output path already exists: {output_path}", err=True)
        raise SystemExit(1)

    click.echo(f"Copying output directory to {output_path}...")
    shutil.copytree(output_dir, output_path)
    click.echo(click.style("✓ Output copied successfully", fg="green"))
