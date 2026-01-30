"""T5 embedding worker for AWS Batch array jobs.

This module is the container entrypoint for T5 embedding jobs.
It processes a single chunk of sequences based on AWS_BATCH_JOB_ARRAY_INDEX.

Usage:
    python -m dayhoff_tools.batch.workers.embed_t5

Environment variables:
    AWS_BATCH_JOB_ARRAY_INDEX: The chunk index to process
    JOB_DIR: Path to job directory (contains input/ and output/ subdirectories)
    BATCH_RETRY_INDICES: (optional) Comma-separated list of indices for retry mode
"""

import logging
import sys

from .base import (
    check_already_complete,
    configure_worker_logging,
    get_array_index,
    get_input_file,
    get_job_dir,
    get_output_file,
    mark_complete,
)

logger = logging.getLogger(__name__)


def main():
    """T5 embedding worker main entrypoint."""
    configure_worker_logging()
    logger.info("Starting T5 embedding worker")

    try:
        # Get configuration from environment
        index = get_array_index()
        job_dir = get_job_dir()

        logger.info(f"Worker configuration:")
        logger.info(f"  Array index: {index}")
        logger.info(f"  Job directory: {job_dir}")

        # Check idempotency - skip if already done (for spot instance retries)
        if check_already_complete(index, job_dir, prefix="embed"):
            logger.info("Exiting - chunk already processed")
            return

        # Get file paths
        input_file = get_input_file(index, job_dir, prefix="chunk")
        output_file = get_output_file(index, job_dir, prefix="embed", suffix=".h5")

        logger.info(f"  Input file: {input_file}")
        logger.info(f"  Output file: {output_file}")

        # Validate input exists
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            sys.exit(1)

        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Import and run embedder
        # Import here to avoid loading torch until needed
        logger.info("Loading T5 embedder...")
        from dayhoff_tools.embedders import T5Embedder

        embedder = T5Embedder(
            max_seq_length=4500,
            large_protein_threshold=2500,
            batch_residue_limit=4500,
            cleanup_frequency=100,
            skip_long_proteins=False,
        )

        logger.info(f"Running embedding on {input_file}...")
        embedder.run(str(input_file), str(output_file))

        # Mark as complete
        mark_complete(index, job_dir, prefix="embed")

        logger.info(f"Chunk {index} completed successfully")

    except Exception as e:
        logger.exception(f"Worker failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
