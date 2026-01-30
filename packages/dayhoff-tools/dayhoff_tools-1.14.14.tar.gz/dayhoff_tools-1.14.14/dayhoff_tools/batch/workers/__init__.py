"""Worker entrypoints for AWS Batch jobs.

These modules are designed to run inside containers as the main entrypoint.
They use AWS_BATCH_JOB_ARRAY_INDEX for work distribution.

Available workers:
- embed_t5: T5 protein sequence embedding
- boltz: Boltz protein structure prediction
- base: Common utilities for all workers
"""

__all__ = ["embed_t5", "boltz", "base"]
