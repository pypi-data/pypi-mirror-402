"""Base utilities for batch workers.

These utilities are shared across all worker implementations.
"""

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def configure_worker_logging():
    """Configure logging for batch workers.

    Sets up logging to output to stdout with timestamps and log levels,
    which CloudWatch will capture.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_array_index() -> int:
    """Get the array index for this worker.

    For array jobs, reads AWS_BATCH_JOB_ARRAY_INDEX.
    For retry jobs, maps from BATCH_RETRY_INDICES.
    For resliced retry jobs, uses the raw array index (chunks are renumbered).
    For single jobs (array_size=1), defaults to 0.

    Returns:
        The array index this worker should process
    """
    # For resliced retries, use raw array index (chunks are renumbered 0..N-1)
    if os.environ.get("RESLICE_PREFIX"):
        array_idx = os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX", "0")
        return int(array_idx)

    # Check for retry mode (non-resliced)
    retry_indices = os.environ.get("BATCH_RETRY_INDICES")
    if retry_indices:
        # In retry mode, we have a list of indices and use array index to pick
        indices = [int(i) for i in retry_indices.split(",")]
        array_idx = int(os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX", "0"))
        if array_idx >= len(indices):
            raise RuntimeError(
                f"Array index {array_idx} out of range for retry indices {indices}"
            )
        return indices[array_idx]

    # Standard array job mode - default to 0 for single jobs
    # Note: When array_size=1, AWS Batch runs a single job (not an array),
    # so AWS_BATCH_JOB_ARRAY_INDEX is not set. Default to 0.
    array_idx = os.environ.get("AWS_BATCH_JOB_ARRAY_INDEX", "0")
    return int(array_idx)


def get_job_dir() -> Path:
    """Get the job directory from environment.

    Returns:
        Path to the job directory

    Raises:
        RuntimeError: If JOB_DIR is not set
    """
    job_dir = os.environ.get("JOB_DIR")
    if not job_dir:
        raise RuntimeError("JOB_DIR environment variable not set")
    return Path(job_dir)


def get_reslice_prefix() -> str | None:
    """Get the reslice prefix from environment if set.

    When RESLICE_PREFIX is set (e.g., 'r1'), files are named like:
    - Input: chunk_r1_000.fasta
    - Output: embed_r1_000.h5
    - Done marker: embed_r1_000.done

    Returns:
        The reslice prefix or None if not in reslice mode
    """
    return os.environ.get("RESLICE_PREFIX")


def get_input_file(index: int, job_dir: Path, prefix: str = "chunk") -> Path:
    """Get the input file path for a given index.

    Args:
        index: Array index
        job_dir: Job directory path
        prefix: File prefix (default: 'chunk')

    Returns:
        Path to input file
    """
    reslice = get_reslice_prefix()
    if reslice:
        return job_dir / "input" / f"{prefix}_{reslice}_{index:03d}.fasta"
    return job_dir / "input" / f"{prefix}_{index:03d}.fasta"


def get_output_file(
    index: int, job_dir: Path, prefix: str = "embed", suffix: str = ".h5"
) -> Path:
    """Get the output file path for a given index.

    Args:
        index: Array index
        job_dir: Job directory path
        prefix: File prefix (default: 'embed')
        suffix: File suffix (default: '.h5')

    Returns:
        Path to output file
    """
    reslice = get_reslice_prefix()
    if reslice:
        return job_dir / "output" / f"{prefix}_{reslice}_{index:03d}{suffix}"
    return job_dir / "output" / f"{prefix}_{index:03d}{suffix}"


def get_done_marker(index: int, job_dir: Path, prefix: str = "embed") -> Path:
    """Get the done marker path for a given index.

    Args:
        index: Array index
        job_dir: Job directory path
        prefix: File prefix (default: 'embed')

    Returns:
        Path to done marker file
    """
    reslice = get_reslice_prefix()
    if reslice:
        return job_dir / "output" / f"{prefix}_{reslice}_{index:03d}.done"
    return job_dir / "output" / f"{prefix}_{index:03d}.done"


def check_already_complete(index: int, job_dir: Path, prefix: str = "embed") -> bool:
    """Check if this chunk is already complete (idempotency).

    Args:
        index: Array index
        job_dir: Job directory path
        prefix: File prefix (default: 'embed')

    Returns:
        True if already complete, False otherwise
    """
    done_marker = get_done_marker(index, job_dir, prefix)
    if done_marker.exists():
        logger.info(f"Chunk {index} already complete (found {done_marker}), skipping")
        return True
    return False


def mark_complete(index: int, job_dir: Path, prefix: str = "embed"):
    """Mark a chunk as complete by creating the done marker.

    Args:
        index: Array index
        job_dir: Job directory path
        prefix: File prefix (default: 'embed')
    """
    done_marker = get_done_marker(index, job_dir, prefix)
    done_marker.parent.mkdir(parents=True, exist_ok=True)
    done_marker.touch()
    logger.info(f"Chunk {index} marked complete: {done_marker}")
