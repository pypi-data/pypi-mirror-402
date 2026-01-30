"""CLI commands for GitHub authentication.

This module provides commands for authenticating with GitHub from within
development containers using the GitHub CLI (gh).

The implementation:
1. Wraps `gh auth login` with sensible defaults for devcontainer environments
2. Automatically configures git to use GitHub CLI for credential management
3. Uses HTTPS protocol and device flow authentication (works in headless envs)
"""

import shutil
import subprocess
import sys
from typing import List, Tuple

import typer

# --- Configuration ---
# OAuth scopes to request during login:
# - repo: Full access to private/public repositories
# - read:org: Read-only access to organization membership
# - workflow: Ability to update GitHub Actions workflow files
GITHUB_SCOPES = "repo,read:org,workflow"
GITHUB_PROTOCOL = "https"

# --- Color constants for formatted output ---
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;36m"
NC = "\033[0m"  # No Color


# --- Helper Functions ---
def _find_executable(name: str) -> str:
    """Find the full path to an executable in PATH."""
    path = shutil.which(name)
    if not path:
        raise FileNotFoundError(
            f"{name} command not found. Please ensure it's installed."
        )
    return path


def _run_command(
    cmd_list: List[str],
    capture: bool = False,
    check: bool = True,
    suppress_output: bool = False,
) -> Tuple[int, str, str]:
    """Run a command and return its result.

    Args:
        cmd_list: List of command arguments
        capture: Whether to capture output
        check: Whether to raise on non-zero exit code
        suppress_output: Whether to hide output even if not captured

    Returns:
        Tuple of (return_code, stdout_str, stderr_str)
    """
    stdout_opt = (
        subprocess.PIPE if capture else subprocess.DEVNULL if suppress_output else None
    )
    stderr_opt = (
        subprocess.PIPE if capture else subprocess.DEVNULL if suppress_output else None
    )

    try:
        result = subprocess.run(
            cmd_list, stdout=stdout_opt, stderr=stderr_opt, check=check, text=True
        )
        return (
            result.returncode,
            result.stdout if capture else "",
            result.stderr if capture else "",
        )
    except subprocess.CalledProcessError as e:
        if capture:
            return (e.returncode, e.stdout or "", e.stderr or "")
        return (e.returncode, "", "")


def _is_gh_authenticated() -> bool:
    """Check if GitHub CLI is authenticated.

    Returns:
        True if `gh auth status` succeeds, False otherwise.
    """
    try:
        gh_path = _find_executable("gh")
        returncode, _, _ = _run_command(
            [gh_path, "auth", "status"],
            capture=True,
            check=False,
            suppress_output=True,
        )
        return returncode == 0
    except FileNotFoundError:
        return False


def _get_gh_user() -> str:
    """Get the currently authenticated GitHub username.

    Returns:
        The username or 'Not authenticated' if not logged in.
    """
    try:
        gh_path = _find_executable("gh")
        returncode, stdout, _ = _run_command(
            [gh_path, "auth", "status", "--show-token"],
            capture=True,
            check=False,
            suppress_output=True,
        )
        if returncode != 0:
            return "Not authenticated"

        # Parse the output to find the logged in account
        # Format: "Logged in to github.com account username (keyring)"
        for line in stdout.split("\n"):
            if "Logged in to" in line and "account" in line:
                parts = line.split("account")
                if len(parts) > 1:
                    # Extract username from "account username (keyring)" or similar
                    user_part = parts[1].strip().split()[0]
                    return user_part
        return "Unknown"
    except FileNotFoundError:
        return "gh CLI not found"


def _get_gh_scopes() -> str:
    """Get the OAuth scopes for the current GitHub authentication.

    Returns:
        Comma-separated list of scopes or 'Unknown' if not available.
    """
    try:
        gh_path = _find_executable("gh")
        returncode, stdout, _ = _run_command(
            [gh_path, "auth", "status"],
            capture=True,
            check=False,
            suppress_output=True,
        )
        if returncode != 0:
            return "N/A"

        # Parse output for scopes - format varies by gh version
        # Look for lines containing "Token scopes:" or similar
        for line in stdout.split("\n"):
            if "scopes" in line.lower():
                # Extract everything after the colon
                if ":" in line:
                    scopes = line.split(":", 1)[1].strip()
                    return scopes if scopes else "none"
        return "Unknown"
    except FileNotFoundError:
        return "N/A"


# --- Typer Application ---
gh_app = typer.Typer(help="Manage GitHub authentication using the gh CLI.")


@gh_app.command("status")
def gh_status():
    """Show current GitHub authentication status."""
    print(f"{BLUE}--- GitHub Authentication Status ---{NC}")

    try:
        gh_path = _find_executable("gh")
    except FileNotFoundError:
        print(f"{RED}Error: GitHub CLI (gh) is not installed.{NC}")
        print(
            f"Install it with: {YELLOW}brew install gh{NC} (Mac) or see https://cli.github.com"
        )
        sys.exit(1)

    if _is_gh_authenticated():
        user = _get_gh_user()
        print(f"  Status: {GREEN}Authenticated{NC}")
        print(f"  User: {GREEN}{user}{NC}")

        # Show detailed status
        print(f"\n{BLUE}Detailed status:{NC}")
        _run_command([gh_path, "auth", "status"], check=False)
    else:
        print(f"  Status: {RED}Not authenticated{NC}")
        print(f"\nTo authenticate, run:")
        print(f"  {YELLOW}dh gh login{NC}")


@gh_app.command("login")
def gh_login():
    """Authenticate with GitHub and configure git credential helper.

    This command:
    1. Authenticates with GitHub using device flow (works in headless environments)
    2. Requests scopes: repo, read:org, workflow
    3. Configures git to use the GitHub CLI for credential management
    """
    try:
        gh_path = _find_executable("gh")
    except FileNotFoundError:
        print(f"{RED}Error: GitHub CLI (gh) is not installed.{NC}")
        print(
            f"Install it with: {YELLOW}brew install gh{NC} (Mac) or see https://cli.github.com"
        )
        sys.exit(1)

    # Step 1: Authenticate with GitHub
    print(f"{BLUE}Authenticating with GitHub...{NC}")
    print(f"{YELLOW}Requesting scopes: {GITHUB_SCOPES}{NC}")
    print(f"{YELLOW}Using protocol: {GITHUB_PROTOCOL}{NC}")
    print()

    login_cmd = [
        gh_path,
        "auth",
        "login",
        "--web",  # Use device flow (works in devcontainers)
        "--git-protocol",
        GITHUB_PROTOCOL,
        "--scopes",
        GITHUB_SCOPES,
    ]

    returncode, _, _ = _run_command(login_cmd, capture=False, check=False)

    if returncode != 0:
        print(f"\n{RED}Authentication failed. Please check the output above.{NC}")
        sys.exit(1)

    # Step 2: Configure git credential helper
    print(f"\n{BLUE}Configuring git to use GitHub CLI for credentials...{NC}")
    setup_cmd = [gh_path, "auth", "setup-git"]
    setup_rc, _, setup_err = _run_command(setup_cmd, capture=True, check=False)

    if setup_rc != 0:
        print(
            f"{YELLOW}Warning: Failed to configure git credential helper: {setup_err}{NC}"
        )
        print(f"You may need to run manually: {YELLOW}gh auth setup-git{NC}")
    else:
        print(f"{GREEN}Git credential helper configured.{NC}")

    # Step 3: Show final status
    print(f"\n{GREEN}GitHub authentication complete!{NC}")
    print(f"\n{BLUE}--- Current Status ---{NC}")
    gh_status()


@gh_app.command("logout")
def gh_logout():
    """Log out from GitHub and clear credentials.

    This removes the GitHub authentication token and unconfigures
    the git credential helper.
    """
    try:
        gh_path = _find_executable("gh")
    except FileNotFoundError:
        print(f"{RED}Error: GitHub CLI (gh) is not installed.{NC}")
        sys.exit(1)

    if not _is_gh_authenticated():
        print(f"{YELLOW}Not currently authenticated with GitHub.{NC}")
        return

    print(f"{BLUE}Logging out from GitHub...{NC}")

    # Log out from github.com
    logout_cmd = [gh_path, "auth", "logout", "--hostname", "github.com"]
    returncode, _, _ = _run_command(logout_cmd, capture=False, check=False)

    if returncode != 0:
        print(f"{RED}Logout may have failed. Check the output above.{NC}")
        sys.exit(1)

    print(f"\n{GREEN}Successfully logged out from GitHub.{NC}")
    print(f"\n{BLUE}To log back in:{NC}")
    print(f"  {YELLOW}dh gh login{NC}")
