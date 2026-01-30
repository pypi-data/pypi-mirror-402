"""Boltz structure prediction worker for AWS Batch array jobs.

This module contains:
1. BoltzProcessor - Core processor class for running Boltz predictions
2. Worker entrypoint for AWS Batch array jobs

The worker processes a single YAML config file based on AWS_BATCH_JOB_ARRAY_INDEX.

Usage:
    python -m dayhoff_tools.batch.workers.boltz

Environment variables:
    AWS_BATCH_JOB_ARRAY_INDEX: The index of the input file to process
    JOB_DIR: Path to job directory (contains input/ and output/ subdirectories)
    BOLTZ_CACHE: Path to Boltz model cache (default: /primordial/.cache/boltz)
    MSA_DIR: Path to global MSA cache (default: /primordial/.cache/msas)
    BOLTZ_OPTIONS: Additional Boltz command-line options
    BATCH_RETRY_INDICES: (optional) Comma-separated list of indices for retry mode
"""

import logging
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


class BoltzProcessor:
    """Processor for running Boltz structure predictions.

    This class wraps the Boltz prediction tool to predict protein structures
    from YAML configuration files containing sequence data.

    Attributes:
        num_workers: Number of CPU workers for Boltz internal parallelization
        boltz_options: Additional command-line options for Boltz
        msa_folder: Path to folder containing pre-computed MSA files (.a3m)
        cache_dir: Path to Boltz model cache directory
    """

    def __init__(
        self,
        num_workers: int | None = None,
        boltz_options: str | None = None,
        msa_folder: str | None = None,
        cache_dir: str | None = None,
    ):
        """Initialize the BoltzProcessor.

        Args:
            num_workers: Number of worker threads for Boltz. If None, uses CPU count - 1.
            boltz_options: Additional command-line options to pass to Boltz
                          (e.g., "--recycling_steps 3 --sampling_steps 200")
            msa_folder: Path to folder containing MSA files (.a3m format).
                       If provided, searches for MSAs matching protein IDs.
            cache_dir: Path to Boltz model cache. Defaults to /primordial/.cache/boltz
        """
        if num_workers is None:
            num_workers = max(1, (os.cpu_count() or 4) - 1)

        self.num_workers = num_workers
        self.boltz_options = boltz_options
        self.msa_folder = msa_folder
        self.cache_dir = cache_dir or "/primordial/.cache/boltz"

    def _extract_protein_id_from_filename(self, filename: str) -> str | None:
        """Extract protein ID from input filename.

        Supports multiple filename formats:
        - {number}_{PROTEIN_ID}_{suffix}.yaml (e.g., '567_IR0041_p.yaml' -> 'IR0041')
        - {PROTEIN_ID}.yaml (e.g., 'IR0041.yaml' -> 'IR0041')
        - {PROTEIN_ID}_{suffix}.yaml (e.g., 'IR0041_2mer.yaml' -> 'IR0041')

        Args:
            filename: The input filename (without path)

        Returns:
            The extracted protein ID, or None if pattern doesn't match
        """
        base_name = os.path.splitext(filename)[0]

        # Pattern 1: number_PROTEINID_suffix
        pattern1 = r"^\d+_([A-Za-z0-9]+)_.+$"
        match = re.match(pattern1, base_name)
        if match:
            protein_id = match.group(1)
            logger.debug(
                f"Extracted protein ID '{protein_id}' from '{filename}' (pattern 1)"
            )
            return protein_id

        # Pattern 2: PROTEINID_suffix (no leading number)
        pattern2 = r"^([A-Za-z0-9]+)_\d*mer$"
        match = re.match(pattern2, base_name)
        if match:
            protein_id = match.group(1)
            logger.debug(
                f"Extracted protein ID '{protein_id}' from '{filename}' (pattern 2)"
            )
            return protein_id

        # Pattern 3: Just PROTEINID (no suffix)
        pattern3 = r"^([A-Za-z0-9]+)$"
        match = re.match(pattern3, base_name)
        if match:
            protein_id = match.group(1)
            logger.debug(
                f"Extracted protein ID '{protein_id}' from '{filename}' (pattern 3)"
            )
            return protein_id

        logger.debug(f"Could not extract protein ID from filename '{filename}'")
        return None

    def _find_msa_file(self, protein_id: str) -> str | None:
        """Find MSA file for a given protein ID.

        Searches for files in the format: {protein_id}.a3m

        Args:
            protein_id: The protein ID to search for

        Returns:
            Full path to the MSA file, or None if not found
        """
        if not self.msa_folder or not os.path.exists(self.msa_folder):
            return None

        msa_filename = f"{protein_id}.a3m"
        msa_path = os.path.join(self.msa_folder, msa_filename)

        if os.path.exists(msa_path):
            logger.info(f"Found MSA file for protein {protein_id}: {msa_path}")
            return msa_path
        else:
            logger.debug(f"MSA file not found: {msa_path}")
            return None

    def _enhance_yaml_with_msa(self, input_file: str) -> tuple[str, bool, str | None]:
        """Enhance input YAML file with MSA information if available.

        Modifies the input YAML file in place, adding MSA paths to protein entries.
        Returns the original content so it can be restored later.

        Args:
            input_file: Path to the input YAML file to modify

        Returns:
            Tuple of (input file path, whether MSA was added, original content for restoration)
        """
        try:
            from ruamel.yaml import YAML
        except ImportError:
            logger.warning("ruamel.yaml not available, skipping MSA enhancement")
            return input_file, False, None

        filename = os.path.basename(input_file)
        protein_id = self._extract_protein_id_from_filename(filename)

        if not protein_id:
            logger.debug(f"No protein ID extracted from {filename}")
            return input_file, False, None

        msa_path = self._find_msa_file(protein_id)
        if not msa_path:
            return input_file, False, None

        # Read original content for backup
        try:
            with open(input_file, "r") as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"Error reading YAML file {input_file}: {e}")
            return input_file, False, None

        # Parse and modify YAML
        yaml_parser = YAML()
        yaml_parser.preserve_quotes = True
        yaml_parser.width = 4096

        try:
            with open(input_file, "r") as f:
                yaml_data = yaml_parser.load(f)
        except Exception as e:
            logger.error(f"Error parsing YAML file {input_file}: {e}")
            return input_file, False, None

        # Add MSA path to protein entries
        msa_added = False
        if "sequences" in yaml_data and isinstance(yaml_data["sequences"], list):
            for sequence in yaml_data["sequences"]:
                if "protein" in sequence and isinstance(sequence["protein"], dict):
                    sequence["protein"]["msa"] = msa_path
                    logger.info(f"Added MSA path {msa_path} to protein in YAML")
                    msa_added = True

        if not msa_added:
            return input_file, False, None

        # Write modified YAML
        try:
            with open(input_file, "w") as f:
                yaml_parser.dump(yaml_data, f)
            return input_file, True, original_content
        except Exception as e:
            logger.error(f"Error writing enhanced YAML: {e}")
            return input_file, False, None

    def run(self, input_file: str, output_dir: str | None = None) -> str:
        """Run Boltz prediction on the input file.

        Args:
            input_file: Path to input YAML file containing sequences
            output_dir: Optional output directory. If None, uses boltz_results_{basename}

        Returns:
            Path to the output directory created by Boltz

        Raises:
            subprocess.CalledProcessError: If Boltz prediction fails
            FileNotFoundError: If input file doesn't exist
        """
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Enhance with MSA if available
        enhanced_input_file, msa_found, original_yaml_data = (
            self._enhance_yaml_with_msa(input_file)
        )

        # Determine output directory
        # Boltz always creates boltz_results_{input_name} inside --out_dir
        input_base = os.path.splitext(os.path.basename(input_file))[0]
        
        if output_dir is None:
            # No output_dir specified, boltz creates in current directory
            expected_output_dir = f"boltz_results_{input_base}"
            out_dir_arg = None
        else:
            # output_dir specified - use its parent for --out_dir
            # and expect boltz_results_{input_base} inside it
            parent_dir = os.path.dirname(output_dir)
            expected_output_dir = os.path.join(parent_dir, f"boltz_results_{input_base}")
            out_dir_arg = parent_dir if parent_dir else None

        logger.info(f"Running Boltz prediction for {input_file}")
        logger.info(f"Output directory: {expected_output_dir}")

        # Build command
        cmd = ["boltz", "predict", input_file]

        # Add output directory if specified
        if out_dir_arg:
            cmd.extend(["--out_dir", out_dir_arg])

        # Add cache directory
        cmd.extend(["--cache", self.cache_dir])

        # Parse additional options
        additional_args = []
        num_workers_in_opts = False
        use_msa_server_in_opts = False

        if self.boltz_options:
            try:
                parsed_opts = shlex.split(self.boltz_options)
                additional_args.extend(parsed_opts)
                num_workers_in_opts = "--num_workers" in parsed_opts
                use_msa_server_in_opts = "--use_msa_server" in parsed_opts
            except ValueError as e:
                logger.error(f"Error parsing boltz_options '{self.boltz_options}': {e}")

        # Handle MSA server option
        if msa_found:
            if use_msa_server_in_opts:
                additional_args = [
                    arg for arg in additional_args if arg != "--use_msa_server"
                ]
                logger.info("Removed --use_msa_server since local MSA was found")
        else:
            if not use_msa_server_in_opts:
                additional_args.append("--use_msa_server")
                logger.info("Added --use_msa_server since no local MSA found")

        # Add num_workers if not in options
        if not num_workers_in_opts:
            cmd.extend(["--num_workers", str(self.num_workers)])

        # Disable cuequivariance kernels - they require cuda-devel image
        # which is much larger. The performance difference is modest.
        # TODO: Consider switching to cuda-devel base image if perf is critical
        cmd.append("--no_kernels")

        cmd.extend(additional_args)

        # Log and run command
        logger.info(f"Running command: {shlex.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        if process.stdout:
            for line in iter(process.stdout.readline, ""):
                logger.info(f"BOLTZ: {line.rstrip()}")

        return_code = process.wait()
        if return_code != 0:
            logger.error(f"Boltz prediction failed with exit code {return_code}")
            raise subprocess.CalledProcessError(return_code, cmd)

        logger.info(f"Boltz prediction completed successfully")

        # Restore original YAML if modified
        if original_yaml_data is not None:
            try:
                with open(input_file, "w") as f:
                    f.write(original_yaml_data)
                logger.debug(f"Restored original YAML content")
            except Exception as e:
                logger.warning(f"Failed to restore original YAML: {e}")

        # Copy input config to output directory
        try:
            config_dest = os.path.join(
                expected_output_dir, os.path.basename(input_file)
            )
            shutil.copy2(input_file, config_dest)
            logger.debug(f"Copied input config to results: {config_dest}")
        except Exception as e:
            logger.warning(f"Failed to copy input config: {e}")

        return expected_output_dir


def _get_done_marker_for_file(job_dir: Path, file_stem: str) -> Path:
    """Get the done marker path for a specific input file."""
    return job_dir / "output" / f"boltz_{file_stem}.done"


def _check_file_complete(job_dir: Path, file_stem: str) -> bool:
    """Check if a specific file has been processed."""
    return _get_done_marker_for_file(job_dir, file_stem).exists()


def _mark_file_complete(job_dir: Path, file_stem: str):
    """Mark a specific file as complete."""
    done_marker = _get_done_marker_for_file(job_dir, file_stem)
    done_marker.parent.mkdir(parents=True, exist_ok=True)
    done_marker.touch()
    logger.info(f"File {file_stem} marked complete: {done_marker}")


def main():
    """Boltz worker main entrypoint for AWS Batch array jobs.

    Each worker processes multiple files based on array index and total workers.
    With N files and M workers, worker i processes files where file_index % M == i.
    """
    from .base import (
        configure_worker_logging,
        get_array_index,
        get_job_dir,
        mark_complete,
    )

    configure_worker_logging()
    logger.info("Starting Boltz prediction worker")

    try:
        # Get configuration from environment
        index = get_array_index()
        job_dir = get_job_dir()
        array_size = int(os.environ.get("BATCH_ARRAY_SIZE", "1"))
        num_files = int(os.environ.get("BATCH_NUM_FILES", "0"))

        logger.info(f"Worker configuration:")
        logger.info(f"  Array index: {index}")
        logger.info(f"  Array size: {array_size}")
        logger.info(f"  Total files: {num_files}")
        logger.info(f"  Job directory: {job_dir}")

        # Find all input files
        input_dir = job_dir / "input"
        input_files = sorted(input_dir.glob("*.yaml"))
        total_files = len(input_files)

        if total_files == 0:
            logger.error("No input files found")
            raise RuntimeError("No input files found")

        # Calculate which files this worker should process
        # Worker i processes files where file_index % array_size == index
        my_files = [f for i, f in enumerate(input_files) if i % array_size == index]

        logger.info(f"  Files assigned to this worker: {len(my_files)}")

        if not my_files:
            logger.info("No files assigned to this worker, exiting successfully")
            mark_complete(index, job_dir, prefix="boltz")
            return

        # Get MSA directories (shared across all files)
        job_msa_dir = job_dir / "msas"
        global_msa_dir = Path(os.environ.get("MSA_DIR", "/primordial/.cache/msas"))

        if job_msa_dir.exists():
            msa_folder = str(job_msa_dir)
            logger.info(f"  Using job-specific MSAs: {msa_folder}")
        elif global_msa_dir.exists():
            msa_folder = str(global_msa_dir)
            logger.info(f"  Using global MSA cache: {msa_folder}")
        else:
            msa_folder = None
            logger.info("  No MSA folder available, will use MSA server")

        # Get cache directory
        cache_dir = os.environ.get("BOLTZ_CACHE", "/primordial/.cache/boltz")
        logger.info(f"  Cache directory: {cache_dir}")

        # Get additional options
        boltz_options = os.environ.get("BOLTZ_OPTIONS")
        if boltz_options:
            logger.info(f"  Boltz options: {boltz_options}")

        # Create processor (reused for all files)
        processor = BoltzProcessor(
            num_workers=None,  # Auto-detect
            boltz_options=boltz_options,
            msa_folder=msa_folder,
            cache_dir=cache_dir,
        )

        # Process each assigned file
        completed = 0
        failed = 0

        for file_idx, input_file in enumerate(my_files):
            file_stem = input_file.stem

            # Check if this file is already complete (idempotency)
            if _check_file_complete(job_dir, file_stem):
                logger.info(
                    f"[{file_idx + 1}/{len(my_files)}] {file_stem}: "
                    "already complete, skipping"
                )
                completed += 1
                continue

            logger.info(
                f"[{file_idx + 1}/{len(my_files)}] Processing {file_stem}..."
            )

            try:
                # Determine output directory
                output_dir = job_dir / "output" / file_stem
                output_dir.parent.mkdir(parents=True, exist_ok=True)

                result_dir = processor.run(str(input_file), str(output_dir))

                # Mark this file as complete
                _mark_file_complete(job_dir, file_stem)

                logger.info(
                    f"[{file_idx + 1}/{len(my_files)}] {file_stem}: "
                    f"completed successfully -> {result_dir}"
                )
                completed += 1

            except Exception as e:
                logger.error(
                    f"[{file_idx + 1}/{len(my_files)}] {file_stem}: "
                    f"failed with error: {e}"
                )
                failed += 1
                # Continue processing other files even if one fails

        # Summary
        logger.info(f"Worker {index} finished: {completed} completed, {failed} failed")

        # Mark worker as complete
        mark_complete(index, job_dir, prefix="boltz")

        if failed > 0:
            logger.warning(f"{failed} file(s) failed to process")
            # Don't exit with error - some files succeeded and are marked complete
            # The failed files can be retried later

    except Exception as e:
        logger.exception(f"Worker failed with error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
