"""Entry file for the CLI, which aggregates and aliases all commands."""

import sys
from importlib.metadata import PackageNotFoundError, version

import typer
from dayhoff_tools.cli.cloud_commands import aws_app, gcp_app
from dayhoff_tools.cli.github_commands import gh_app
from dayhoff_tools.cli.engine1 import (
    engine_app as engine1_app,
    studio_app as studio1_app,
)
from dayhoff_tools.cli.utility_commands import (
    add_dependency,
    build_and_upload_wheel,
    delete_local_branch,
    remove_dependency,
    sync_with_toml,
    test_github_actions_locally,
    update_dependencies,
)
from dayhoff_tools.warehouse import (
    _warn_if_gcp_default_sa,
    add_to_warehouse_typer,
    get_ancestry,
    get_from_warehouse_typer,
    import_from_warehouse_typer,
)


def _get_dht_version() -> str:
    try:
        return version("dayhoff-tools")
    except PackageNotFoundError:
        # Fallback to package __version__ if running from source
        try:
            from dayhoff_tools import __version__  # type: ignore

            return __version__
        except Exception:
            return "unknown"


app = typer.Typer(
    help=f"Dayhoff Tools (dh) v{_get_dht_version()}\n\nUse 'dh --version' to print version and exit."
)

# Utility commands
app.command("clean")(delete_local_branch)

# Dependency Management
app.command(
    "tomlsync",
    help="Sync environment with platform-specific TOML manifest (install/update dependencies).",
)(sync_with_toml)
app.command("add", help="Add a dependency to all platform manifests.")(add_dependency)
app.command("remove", help="Remove a dependency from all platform manifests.")(
    remove_dependency
)
app.command("update", help="Update dayhoff-tools (or all deps) and sync environment.")(
    update_dependencies
)

# Other Utilities
app.command("gha")(test_github_actions_locally)
app.command("wadd")(add_to_warehouse_typer)
app.command("wancestry")(get_ancestry)
app.command("wget")(get_from_warehouse_typer)
app.command("wimport")(import_from_warehouse_typer)

# Cloud commands
app.add_typer(gcp_app, name="gcp", help="Manage GCP authentication and impersonation.")
app.add_typer(aws_app, name="aws", help="Manage AWS SSO authentication.")
app.add_typer(gh_app, name="gh", help="Manage GitHub authentication.")


# Engine and Studio commands (v2 - new default with progress tracking)
# These use Click instead of Typer, so we need a passthrough wrapper
@app.command(
    "engine",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def engine_cmd(ctx: typer.Context):
    """Manage compute engines for development."""
    from dayhoff_tools.cli.engines_studios import engine_cli

    # Pass arguments directly to Click CLI
    engine_cli(ctx.args, standalone_mode=False)


@app.command(
    "studio",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def studio_cmd(ctx: typer.Context):
    """Manage persistent development studios."""
    from dayhoff_tools.cli.engines_studios import studio_cli

    # Pass arguments directly to Click CLI
    studio_cli(ctx.args, standalone_mode=False)


# Batch job management (Click-based CLI)
@app.command(
    "batch",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def batch_cmd(ctx: typer.Context):
    """Manage batch jobs on AWS Batch."""
    from dayhoff_tools.cli.batch import batch_cli

    # Pass arguments directly to Click CLI
    batch_cli(ctx.args, standalone_mode=False)


# Engine and Studio commands (v1 - legacy, uses old infrastructure)
app.add_typer(engine1_app, name="engine1", help="[Legacy v1] Manage engines.")
app.add_typer(studio1_app, name="studio1", help="[Legacy v1] Manage studios.")


# Backward compatibility aliases for v2 commands (engine2/studio2 -> engine/studio)
@app.command(
    "engine2",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
    hidden=True,  # Hide from help, but still works
)
def engine2_cmd(ctx: typer.Context):
    """[Alias] Use 'dh engine' instead."""
    from dayhoff_tools.cli.engines_studios import engine_cli

    engine_cli(ctx.args, standalone_mode=False)


@app.command(
    "studio2",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
    hidden=True,  # Hide from help, but still works
)
def studio2_cmd(ctx: typer.Context):
    """[Alias] Use 'dh studio' instead."""
    from dayhoff_tools.cli.engines_studios import studio_cli

    studio_cli(ctx.args, standalone_mode=False)


@app.callback(invoke_without_command=True)
def _version_option(
    ctx: typer.Context,
    version_flag: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Print version and exit.",
        is_eager=True,
    ),
):
    """Global options for the dh CLI (e.g., version)."""
    if version_flag:
        typer.echo(_get_dht_version())
        raise typer.Exit()
    # If no subcommand provided, show help instead of 'Missing command'
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


@app.command("wheel")
def build_and_upload_wheel_command(
    bump: str = typer.Option(
        "patch",
        "--bump",
        "-b",
        help="Which part of the version to bump: 'major', 'minor', or 'patch'.",
        case_sensitive=False,
    )
):
    """Build wheel, bump version, and upload to PyPI."""
    build_and_upload_wheel(bump_part=bump)


# Use lazy loading for slow-loading swarm commands
@app.command("reset")
def reset_wrapper(
    firestore_collection: str = typer.Option(prompt=True),
    old_status: str = typer.Option(default="failed", prompt=True),
    new_status: str = typer.Option(default="available", prompt=True),
    delete_old: bool = typer.Option(default=True, prompt=True),
):
    """Find all the documents in the database with a given status, and
    make a new document with the same name and a new status."""
    from dayhoff_tools.cli.swarm_commands import reset_failed_cards

    reset_failed_cards(firestore_collection, old_status, new_status, delete_old)


@app.command("zombie")
def zombie_wrapper(
    firestore_collection: str = typer.Option(prompt=True),
    delete_old: bool = typer.Option(default=True, prompt=True),
    minutes_threshold: int = typer.Option(default=60, prompt=True),
):
    """Find all the documents in the database with status "assigned", and "last_updated"
    older than a specified threshold, and make a new "available" document for them."""
    from dayhoff_tools.cli.swarm_commands import reset_zombie_cards

    reset_zombie_cards(firestore_collection, delete_old, minutes_threshold)


@app.command("status")
def status_wrapper(
    firestore_collection: str = typer.Argument(),
):
    """Count the various statuses of items in a given collection."""
    from dayhoff_tools.cli.swarm_commands import get_firestore_collection_status

    get_firestore_collection_status(firestore_collection)


# Deployment commands - use lazy loading but preserve argument passing
@app.command("deploy")
def deploy_command(
    mode: str = typer.Argument(help="Deployment mode. Options: local, shell, batch"),
    config_path: str = typer.Argument(help="Path to the YAML configuration file"),
):
    """Unified deployment command."""
    # Check GCP credentials if deploying in batch mode with GCP
    # Do this early to fail fast before importing deployment code
    if mode == "batch":
        try:
            # Check cloud provider in config
            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            if config.get("cloud") == "gcp":
                _warn_if_gcp_default_sa(force_prompt=True)
        except Exception as e:
            # Don't block deployment if config can't be read or other errors occur
            print(f"Warning: Could not check GCP credentials: {e}", file=sys.stderr)

    from dayhoff_tools.deployment.base import deploy

    deploy(mode, config_path)


@app.command("job")
def run_job_command(
    mode: str = typer.Argument(
        default="setup_and_execute",
        help="Mode to run in: setup (setup only), execute (execute only), or setup_and_execute (both)",
    )
):
    """Run a job."""
    from dayhoff_tools.deployment.job_runner import run_job

    run_job(mode)


if __name__ == "__main__":
    app()
