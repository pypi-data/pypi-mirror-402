import pathlib
import time
from typing import List

import click

from obvyr_cli.api_client import ObvyrAPIClient
from obvyr_cli.archive_builder import build_artifacts_tar_zst
from obvyr_cli.command_wrapper import run_command
from obvyr_cli.config import ProfileSettings, Settings, get_settings
from obvyr_cli.error_handling import handle_archive_error
from obvyr_cli.logging_config import configure_logging, get_logger
from obvyr_cli.schemas import (
    CommandExecutionConfig,
    OutputMode,
    RunCommandResponse,
)

logger = get_logger("cli")

# ===================================
# CLI Support Functions
# ===================================


def resolve_output_mode(
    output_mode: str, no_stream: bool, force_stream: bool
) -> OutputMode:
    """
    Resolve output mode from CLI flags with priority handling.

    Args:
        output_mode: Base output mode from --output-mode flag.
        no_stream: Whether --no-stream flag was used.
        force_stream: Whether --force-stream flag was used.

    Returns:
        Resolved OutputMode.

    Raises:
        click.UsageError: If conflicting flags are provided.
    """
    # Check for conflicting flags
    if no_stream and force_stream:
        raise click.UsageError(
            "Cannot use both --no-stream and --force-stream flags together."
        )

    # Priority: specific flags override --output-mode
    if no_stream:
        return OutputMode.BATCH
    if force_stream:
        return OutputMode.STREAM

    # Use specified output mode
    return OutputMode(output_mode.lower())


def is_attachment_fresh(
    attachment_path: pathlib.Path, max_age_seconds: int = 10
) -> bool:
    """
    Check if an attachment file is fresh enough to be included.

    Args:
        attachment_path: Path to the attachment file
        max_age_seconds: Maximum age in seconds for file to be considered fresh

    Returns:
        True if file exists and was modified within max_age_seconds, False otherwise
    """
    if not attachment_path.exists():
        return False

    if max_age_seconds <= 0:
        return False

    current_time = time.time()
    file_mtime = attachment_path.stat().st_mtime
    file_age_seconds = current_time - file_mtime

    return file_age_seconds < max_age_seconds


def list_available_profiles(settings: Settings) -> None:
    """
    Lists all available profiles.
    """
    profiles = settings.list_profiles()

    if len(profiles) == 0:
        click.echo("\nNo profiles available.\n")
        return

    click.echo("\nAvailable profiles:\n")
    for profile in profiles:
        click.echo(f"  - {profile}")
    click.echo("")


def show_profile_config(
    settings: Settings, profile_name: str | None = None
) -> None:
    """
    Shows the configuration for the specified or active profile.
    """
    config = settings.show_config(profile_name)

    profile_display = profile_name or "DEFAULT"
    click.echo(f"\nProfile '{profile_display}' configuration:\n")
    for key, value in config.items():
        click.echo(f"  {key}: {value}")
    click.echo("")


def has_handled_initial_options(
    command: List[str],
    list_profiles: bool,
    show_config: bool,
    settings: Settings,
    profile: str | None = None,
) -> bool:
    """Handle initial options for listing profiles or showing configuration."""
    if command:
        return False

    if list_profiles:
        list_available_profiles(settings)
        return True

    if show_config:
        show_profile_config(settings, profile)
        return True

    raise click.UsageError(
        "\n".join(
            (
                "No command provided.",
                "Usage: obvyr-cli <command> [arguments]",
                "Try 'obvyr-cli --help' for more information.",
            )
        )
    )


def fetch_active_profile(
    settings: Settings, profile_name: str | None = None
) -> ProfileSettings:
    """Retrieve the active profile from settings."""
    active_profile = settings.get_profile(profile_name)
    profile_display_name = profile_name or "DEFAULT"
    logger.debug(f"Using profile: {profile_display_name}")
    return active_profile


def display_execution_summary(response: RunCommandResponse) -> None:
    """Display the execution summary after streaming output."""
    output = (
        f"\nExecuted by {click.style(response.user, fg='green')} "
        f"in {click.style(f'{response.execution_time:.2f}s', fg='blue')}\n"
    )
    click.echo(output)


def display_output(response: RunCommandResponse) -> None:
    """Display the command's output (legacy function for backward compatibility)."""
    if response.output:
        click.echo(f"\n{response.output}")
    display_execution_summary(response)


def send_to_api(
    active_profile: ProfileSettings, data: RunCommandResponse
) -> None:
    """
    Sends execution data to the Obvyr API.

    :param active_profile: Profile configuration to use for API submission.
    :param data: Command execution result to be sent to the API.
    """

    if not active_profile.API_KEY:
        logger.debug("API submission disabled: No API key configured.")
        return

    archive_path = None
    try:
        # Create archive from command execution data
        attachment_paths = None
        if active_profile.ATTACHMENT_PATHS:
            fresh_paths = []
            for path_str in active_profile.ATTACHMENT_PATHS:
                path = pathlib.Path(path_str)
                if is_attachment_fresh(
                    path, active_profile.ATTACHMENT_MAX_AGE_SECONDS
                ):
                    fresh_paths.append(path)
                    logger.debug(f"Including fresh attachment: {path}")
                else:
                    logger.debug(f"Skipping stale attachment: {path}")

            # Only set attachment_paths if we have fresh files
            if fresh_paths:
                attachment_paths = fresh_paths

        # Build archive with or without attachments
        archive_path = build_artifacts_tar_zst(
            data, attachment_paths=attachment_paths, tags=active_profile.TAGS
        )

        with ObvyrAPIClient(
            api_key=active_profile.API_KEY,
            base_url=active_profile.API_URL,
            timeout=active_profile.TIMEOUT,
            verify_ssl=active_profile.VERIFY_SSL,
        ) as client:
            start_time = time.time()
            response = client.send_archive("/collect", archive_path)
            end_time = time.time()

            logger.debug(f"API request time: {end_time - start_time:.2f}s")

            if response:
                logger.debug(f"Successfully sent data to API: {response}")
            else:
                logger.warning(
                    "Failed to send data to API. Check your configuration."
                )

    except OSError as e:
        handle_archive_error(e)
    except Exception as e:
        # Other errors are already handled by the API client's centralised error handling
        logger.error(f"Unexpected error during API submission: {e}")
    finally:
        # Always clean up the temporary archive file
        if archive_path and archive_path.exists():
            archive_path.unlink()


# ===================================
# Click CLI
# ===================================


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("command", nargs=-1, required=False, type=click.UNPROCESSED)
@click.option(
    "--list-profiles",
    "list_profiles",
    is_flag=True,
    help="List all available profiles.",
)
@click.option(
    "--show-config",
    "show_config",
    is_flag=True,
    help="Show config for active profile.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging (debug mode).",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Enable quiet mode (errors only).",
)
@click.option(
    "--profile",
    "-p",
    help="Specify which profile configuration to use.",
)
@click.option(
    "--output-mode",
    type=click.Choice(["auto", "stream", "batch"], case_sensitive=False),
    default="auto",
    help="Output mode: auto (CI detection), stream (force streaming), batch (force batch).",
)
@click.option(
    "--no-stream",
    is_flag=True,
    help="Disable streaming output (equivalent to --output-mode=batch).",
)
@click.option(
    "--force-stream",
    is_flag=True,
    help="Force streaming output (equivalent to --output-mode=stream).",
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable color output (don't set FORCE_COLOR environment variable).",
)
def cli_run_process(
    command: List[str],
    list_profiles: bool,
    show_config: bool,
    verbose: bool,
    quiet: bool,
    profile: str | None,
    output_mode: str,
    no_stream: bool,
    force_stream: bool,
    no_color: bool,
) -> None:
    """
    Executes a system command while using the Obvyr CLI profile configuration.
    """
    # Configure logging based on CLI flags
    configure_logging(verbose=verbose, quiet=quiet)

    # Resolve output mode from flags
    resolved_output_mode = resolve_output_mode(
        output_mode, no_stream, force_stream
    )

    # Create command execution configuration
    # force_color=True by default, --no-color flag disables it
    execution_config = CommandExecutionConfig(
        output_mode=resolved_output_mode,
        force_color=not no_color,  # Default True, disabled by --no-color flag
        preserve_ansi=True,
    )

    try:
        settings = get_settings()

        if has_handled_initial_options(
            command, list_profiles, show_config, settings, profile
        ):
            return

        active_profile = fetch_active_profile(settings, profile)

        # Create streaming callback for real-time output display
        def stream_output(line: str) -> None:
            """Stream output line-by-line to console."""
            click.echo(line)

        response: RunCommandResponse = run_command(
            list(command),
            stream_callback=stream_output,
            config=execution_config,
        )

        if active_profile.API_URL and active_profile.API_KEY:
            send_to_api(active_profile, response)

        display_execution_summary(response)

        if response.returncode != 0:
            raise click.exceptions.Exit(response.returncode)

    except Exception as e:
        raise click.ClickException(str(e)) from e
