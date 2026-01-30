"""Batch job management CLI for AWS Batch.

This module provides a Click-based CLI for submitting and managing batch jobs
on AWS Batch, with support for:
- High-level pipelines (embed-t5, boltz)
- Generic job submission
- Job lifecycle management (status, logs, cancel, retry, finalize)
- Local debugging and shell access
"""

import click

from .commands.boltz import boltz
from .commands.cancel import cancel
from .commands.clean import clean
from .commands.embed_t5 import embed_t5
from .commands.finalize import finalize
from .commands.list_jobs import list_jobs
from .commands.local import local
from .commands.logs import logs
from .commands.retry import retry
from .commands.status import status
from .commands.submit import submit


@click.group()
def batch_cli():
    """Manage batch jobs on AWS Batch.

    \b
    Job Management:
      submit     Submit a custom job from config file
      status     Show job status
      cancel     Cancel a running job
      logs       View job logs
      retry      Retry failed chunks
      finalize   Combine results and clean up
      local      Run a chunk locally for debugging
      list       List recent jobs
      clean      Remove old completed job directories

    \b
    Embedding Pipelines:
      embed-t5   Generate T5 protein embeddings

    \b
    Structure Prediction:
      boltz      Predict protein structures with Boltz

    \b
    Examples:
      # Submit an embedding job
      dh batch embed-t5 /primordial/proteins.fasta --workers 50

      # Submit a structure prediction job
      dh batch boltz /primordial/complexes/ --workers 100

      # Check job status
      dh batch status dma-embed-20260109-a3f2

      # View logs for a failed chunk
      dh batch logs dma-embed-20260109-a3f2 --index 27

      # Retry failed chunks
      dh batch retry dma-embed-20260109-a3f2

      # Finalize and combine results
      dh batch finalize dma-embed-20260109-a3f2 --output /primordial/embeddings.h5
    """
    pass


# Register job management commands
batch_cli.add_command(submit)
batch_cli.add_command(status)
batch_cli.add_command(cancel)
batch_cli.add_command(logs)
batch_cli.add_command(retry)
batch_cli.add_command(finalize)
batch_cli.add_command(local)
batch_cli.add_command(list_jobs, name="list")
batch_cli.add_command(clean)

# Register pipeline commands
batch_cli.add_command(embed_t5, name="embed-t5")
batch_cli.add_command(boltz)

__all__ = ["batch_cli"]
