"""Job ID generation for batch jobs.

Job IDs follow the format: {username}-{pipeline}-{YYYYMMDD}-{random4}
Examples:
- dma-embed-20260109-a3f2
- josh-boltz-20260109-b7c1
- sam-batch-20260109-c9d2 (for generic submit jobs)
"""

import json
import os
import secrets
import subprocess
from datetime import datetime
from functools import lru_cache


class JobIdError(Exception):
    """Error generating job ID."""

    pass


@lru_cache(maxsize=1)
def get_aws_username() -> str:
    """Extract username from AWS SSO session.

    Attempts multiple methods in order:
    1. AWS_SSO_USER environment variable (if set by dh aws login)
    2. Parse from `aws sts get-caller-identity` ARN

    Returns:
        Username string (lowercase, alphanumeric only)

    Raises:
        JobIdError: If username cannot be determined
    """
    # Method 1: Check environment variable (fastest)
    env_user = os.environ.get("AWS_SSO_USER")
    if env_user:
        return _sanitize_username(env_user)

    # Method 2: Parse from STS caller identity
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            arn = identity.get("Arn", "")
            # ARN format: arn:aws:sts::ACCOUNT:assumed-role/AWSReservedSSO_ROLE/username
            # or: arn:aws:iam::ACCOUNT:user/username
            if "/AWSReservedSSO_" in arn:
                # SSO assumed role - username is last part
                username = arn.split("/")[-1]
                return _sanitize_username(username)
            elif ":user/" in arn:
                # IAM user
                username = arn.split("/")[-1]
                return _sanitize_username(username)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    # Method 3: Fall back to system username
    import getpass

    try:
        username = getpass.getuser()
        return _sanitize_username(username)
    except Exception:
        pass

    raise JobIdError(
        "Could not determine AWS username. "
        "Ensure you're logged in with 'dh aws login' or set AWS_SSO_USER environment variable."
    )


def _sanitize_username(username: str) -> str:
    """Sanitize username to be safe for job IDs.

    - Convert to lowercase
    - Keep only alphanumeric characters
    - Truncate to 20 characters
    """
    sanitized = "".join(c for c in username.lower() if c.isalnum())
    return sanitized[:20] if sanitized else "unknown"


def generate_job_id(pipeline: str = "batch") -> str:
    """Generate a unique job ID.

    Args:
        pipeline: Pipeline type (e.g., 'embed', 'boltz', 'batch')

    Returns:
        Job ID in format: {username}-{pipeline}-{YYYYMMDD}-{random4}

    Examples:
        >>> generate_job_id("embed")
        'dma-embed-20260109-a3f2'
        >>> generate_job_id()
        'dma-batch-20260109-b7c1'
    """
    username = get_aws_username()
    date_str = datetime.now().strftime("%Y%m%d")
    random_suffix = secrets.token_hex(2)  # 4 hex characters

    # Sanitize pipeline name
    pipeline_clean = "".join(c for c in pipeline.lower() if c.isalnum())[:10]

    return f"{username}-{pipeline_clean}-{date_str}-{random_suffix}"


def parse_job_id(job_id: str) -> dict:
    """Parse a job ID into its components.

    Args:
        job_id: Job ID string

    Returns:
        Dictionary with keys: username, pipeline, date, suffix

    Raises:
        ValueError: If job ID format is invalid
    """
    parts = job_id.split("-")
    if len(parts) < 4:
        raise ValueError(f"Invalid job ID format: {job_id}")

    # Handle usernames with dashes by taking last 3 parts as known components
    suffix = parts[-1]
    date_str = parts[-2]
    pipeline = parts[-3]
    username = "-".join(parts[:-3])

    # Validate date format
    try:
        datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        raise ValueError(f"Invalid date in job ID: {date_str}")

    return {
        "username": username,
        "pipeline": pipeline,
        "date": date_str,
        "suffix": suffix,
    }
