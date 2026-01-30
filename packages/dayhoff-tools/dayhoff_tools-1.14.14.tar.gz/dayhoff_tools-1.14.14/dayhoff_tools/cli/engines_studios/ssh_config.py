"""SSH config management utilities for engines_studios CLI."""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .api_client import StudioManagerClient


def update_ssh_config_silent(client: "StudioManagerClient", env: str) -> bool:
    """Update SSH config with engine entries silently.

    Returns True if successful, False otherwise.
    Does not raise exceptions - intended for silent background updates.
    """
    from .auth import get_aws_username

    ssh_config_path = os.path.expanduser("~/.ssh/config")

    try:
        # Read existing config
        if os.path.exists(ssh_config_path):
            with open(ssh_config_path, "r") as f:
                lines = f.readlines()
        else:
            lines = []

        # Remove managed entries
        managed_start = "# BEGIN DAYHOFF ENGINES\n"
        managed_end = "# END DAYHOFF ENGINES\n"

        new_lines = []
        skip = False
        for line in lines:
            if line == managed_start:
                skip = True
            elif line == managed_end:
                skip = False
                continue
            elif not skip:
                new_lines.append(line)

        # Get engines
        result = client.list_engines()
        engines = result.get("engines", [])

        if not engines:
            return False

        # Generate new entries
        config_entries = [managed_start]

        try:
            current_user = get_aws_username()
        except RuntimeError:
            # Not authenticated - can't determine user, skip filtering
            current_user = None

        for engine in engines:
            user = engine.get("user", "unknown")

            # Skip engines owned by other users (unless user is unknown or we can't determine current user)
            if current_user and user != "unknown" and user != current_user:
                continue

            instance_id = engine.get("instance_id")
            name = engine.get("name", instance_id)
            state = engine.get("state", "unknown")

            # Only add running engines
            if state != "running":
                continue

            # Map environment to AWS profile
            profile = f"{env}-devaccess"

            config_entries.append(f"\nHost {name}\n")
            config_entries.append(f"    HostName {instance_id}\n")
            config_entries.append(f"    User {user}\n")
            config_entries.append(f"    ForwardAgent yes\n")
            config_entries.append(
                f"    ProxyCommand aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p' --profile {profile}\n"
            )

        config_entries.append(managed_end)

        # Write back
        new_lines.extend(config_entries)

        with open(ssh_config_path, "w") as f:
            f.writelines(new_lines)

        return True

    except Exception:
        return False
