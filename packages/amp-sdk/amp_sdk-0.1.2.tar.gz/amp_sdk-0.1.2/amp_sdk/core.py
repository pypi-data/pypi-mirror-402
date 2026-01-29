from __future__ import annotations

"""
Amp Python SDK

This SDK provides a Python interface to the Amp CLI, allowing you to
run Amp programmatically in Python applications.
"""

import asyncio
import contextlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import uuid
from collections.abc import AsyncIterator
from typing import Any, Optional, Union

from .exceptions import AmpError, CLINotFoundError, JSONParseError, ProcessError
from .types import (
    AmpOptions,
    AssistantMessage,
    ErrorResultMessage,
    Permission,
    ResultMessage,
    StreamMessage,
    SystemMessage,
    TextContent,
    UserInputMessage,
    UserMessage,
)

# ============================================================================
# Constants
# ============================================================================

MESSAGE_TYPES: dict[str, type[StreamMessage]] = {
    "system": SystemMessage,
    "assistant": AssistantMessage,
    "user": UserMessage,
}

# ============================================================================
# CLI Discovery and Management
# ============================================================================


def _find_amp_cli() -> list[str]:
    """
    Find the Amp CLI executable.

    Returns:
        List of command components to execute the CLI

    Raises:
        CLINotFoundError: If the CLI cannot be found
    """
    # Check for AMP_CLI_PATH environment variable
    cli_path = os.environ.get("AMP_CLI_PATH")
    if cli_path and os.path.isfile(cli_path):
        return ["node", cli_path]

    # Try to resolve via Node.js require.resolve
    try:
        result = subprocess.run(
            ["node", "-p", "require.resolve('@sourcegraph/amp/package.json')"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2.0,
        )

        package_json_path = result.stdout.strip()
        package_dir = os.path.dirname(package_json_path)

        # Read package.json to get bin path
        with open(package_json_path) as f:
            package_data = json.load(f)

        bin_path = package_data.get("bin", {}).get("amp")
        if bin_path:
            full_bin_path = os.path.join(package_dir, bin_path)
            if os.path.isfile(full_bin_path):
                return ["node", full_bin_path]

    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        json.JSONDecodeError,
        subprocess.TimeoutExpired,
    ):
        pass

    # Fallback to amp on PATH
    if shutil.which("amp"):
        return ["amp"]

    raise CLINotFoundError(
        "Amp CLI not found. Please install it with: npm install -g @sourcegraph/amp"
    )


# ============================================================================
# Settings File Management
# ============================================================================


async def _build_settings_file(
    options: AmpOptions, session_id: str
) -> tuple[Optional[str], Optional[str]]:
    """
    Build a temporary settings file if permissions or skills are provided.

    Args:
        options: Amp configuration options
        session_id: Unique session identifier

    Returns:
        Tuple of (settings_file_path, temp_dir_path)
        Both are None if no settings need to be written
    """
    # Check if we need to create a temp settings file
    if not options.permissions and not options.skills:
        return None, None

    # Read existing settings file if provided
    merged_settings: dict[str, Any] = {}
    if options.settings_file:
        # Validate settings file path to prevent path traversal
        settings_path = os.path.realpath(options.settings_file)
        if not os.path.isfile(settings_path):
            raise AmpError(f"Settings file not found or not a file: {options.settings_file}")

        try:
            with open(settings_path, encoding="utf-8") as f:
                merged_settings = json.load(f)
        except json.JSONDecodeError as e:
            raise AmpError(f"Invalid JSON in settings file {options.settings_file}: {e}") from e
        except OSError as e:
            raise AmpError(f"Failed to read settings file {options.settings_file}: {e}") from e

    # Add permissions to settings with amp. prefix
    if options.permissions:
        # Convert Permission objects to dicts
        permissions_data = [
            p.model_dump(exclude_none=True) if hasattr(p, "model_dump") else p
            for p in options.permissions
        ]
        merged_settings["amp.permissions"] = permissions_data

    # Add skills path
    if options.skills:
        merged_settings["amp.skills.path"] = options.skills

    # Create secure temp directory with restrictive permissions (0o700)
    temp_dir = tempfile.mkdtemp(prefix="amp-")
    os.chmod(temp_dir, 0o700)

    # Write settings file with restrictive permissions (0o600)
    temp_settings_path = os.path.join(temp_dir, "settings.json")
    fd = os.open(temp_settings_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(merged_settings, f, indent=2)

    return temp_settings_path, temp_dir


# ============================================================================
# Environment Variable Management
# ============================================================================


def _build_environment_variables(options: Optional[AmpOptions] = None) -> dict[str, str]:
    """
    Build environment variables for the Amp CLI process.

    Args:
        options: Amp configuration options

    Returns:
        Dictionary of environment variables
    """
    if not options:
        options = AmpOptions()

    # Start with user-provided env variables (coerced to strings)
    env = {key: str(value) for key, value in options.env.items()} if options.env else {}

    # System env variables override user-provided ones
    env.update(os.environ.copy())

    # Set Options env variables
    if options.toolbox:
        env["AMP_TOOLBOX"] = options.toolbox

    # Set static env variables, set during build
    from . import __version__

    env["AMP_SDK_VERSION"] = os.environ.get("AMP_SDK_VERSION", __version__)

    return env


# ============================================================================
# CLI Process Management
# ============================================================================


def _build_cli_args(options: Optional[AmpOptions] = None) -> list[str]:
    """
    Build CLI arguments from options.

    Args:
        options: Amp configuration options
        settings_file_override: Override settings file path (used for permissions temp file)

    Returns:
        List of CLI arguments
    """
    args = []

    if not options:
        options = AmpOptions()

    # Handle continue option
    if options.continue_thread is True:
        args.extend(["threads", "continue"])
    elif isinstance(options.continue_thread, str):
        args.extend(["threads", "continue", options.continue_thread])

    # Always add execute and stream JSON flags
    args.extend(["--execute", "--stream-json"])

    # Add optional flags
    if options.dangerously_allow_all:
        args.append("--dangerously-allow-all")

    if options.visibility:
        args.extend(["--visibility", options.visibility])

    if options.settings_file:
        args.extend(["--settings-file", options.settings_file])

    if options.log_level:
        args.extend(["--log-level", options.log_level])

    if options.log_file:
        args.extend(["--log-file", options.log_file])

    if options.mcp_config:
        config_str: str
        if isinstance(options.mcp_config, str):
            config_str = options.mcp_config
        elif hasattr(options.mcp_config, "to_json_string"):
            config_str = options.mcp_config.to_json_string()
        elif hasattr(options.mcp_config, "model_dump_json"):
            config_str = options.mcp_config.model_dump_json()
        elif hasattr(options.mcp_config, "dict"):
            config_str = json.dumps(options.mcp_config.dict())
        else:
            config_str = json.dumps(options.mcp_config)

        args.extend(["--mcp-config", config_str])

    if options.mode:
        args.extend(["--mode", options.mode])

    return args


# ============================================================================
# Stream Processing
# ============================================================================


async def _handle_streaming_input(
    proc: asyncio.subprocess.Process, prompt: AsyncIterator[UserInputMessage]
) -> None:
    """
    Handle streaming input to the CLI process.

    Args:
        proc: The subprocess
        prompt: Async iterator of user messages
    """
    if not proc.stdin:
        return

    try:
        async for message in prompt:
            # Validate message structure
            message_dict = message.model_dump()
            json_line = json.dumps(message_dict) + "\n"

            proc.stdin.write(json_line.encode("utf-8"))
            await proc.stdin.drain()

    except Exception as e:
        raise AmpError(f"Error writing streaming input: {e}") from e
    finally:
        proc.stdin.close()
        await proc.stdin.wait_closed()


async def _handle_string_input(proc: asyncio.subprocess.Process, prompt: str) -> None:
    """
    Handle simple string input to the CLI process.

    Args:
        proc: The subprocess
        prompt: The prompt string
    """
    if not proc.stdin:
        return

    try:
        input_data = f"{prompt}\n"
        proc.stdin.write(input_data.encode("utf-8"))
        await proc.stdin.drain()
    except Exception as e:
        raise AmpError(f"Error writing string input: {e}") from e
    finally:
        proc.stdin.close()
        await proc.stdin.wait_closed()


async def _read_process_output(proc: asyncio.subprocess.Process) -> AsyncIterator[StreamMessage]:
    """
    Read and parse JSON output from the CLI process.

    Args:
        proc: The subprocess

    Yields:
        Parsed stream messages
    """
    if not proc.stdout:
        return

    while True:
        line = await proc.stdout.readline()
        if not line:
            break

        line_str = line.decode("utf-8").strip()
        if not line_str:
            continue

        try:
            message_data = json.loads(line_str)
            msg_type = message_data.get("type")

            if msg_type == "result":
                is_error = message_data.get("is_error")
                message_class: type[StreamMessage] = (
                    ErrorResultMessage if is_error else ResultMessage
                )
            elif msg_type in MESSAGE_TYPES:
                message_class = MESSAGE_TYPES[msg_type]
            else:
                continue

            yield message_class(**message_data)

        except json.JSONDecodeError as e:
            raise JSONParseError(f"Invalid JSON output: {e}", raw_line=line_str) from e
        except Exception as e:
            raise AmpError(f"Error parsing message: {e}") from e


async def _wait_for_process(proc: asyncio.subprocess.Process) -> None:
    """Wait for process completion and handle errors."""
    await proc.wait()

    if proc.returncode == 0:
        return

    # Read stderr if available
    stderr = ""
    if proc.stderr:
        stderr_bytes = await proc.stderr.read()
        stderr = stderr_bytes.decode("utf-8", errors="replace")

    # Handle signal vs exit code
    returncode = proc.returncode or 1
    if returncode < 0:
        try:
            sig_name = signal.Signals(-returncode).name
        except ValueError:
            sig_name = str(-returncode)

        raise ProcessError(
            f"Process killed by signal {sig_name}",
            exit_code=returncode,
            stderr=stderr,
            signal=sig_name,
        )

    raise ProcessError(
        f"Process exited with code {returncode}", exit_code=returncode, stderr=stderr
    )


# ============================================================================
# Main Execute Function
# ============================================================================


async def execute(
    prompt: Union[str, AsyncIterator[UserInputMessage]],
    options: Optional[AmpOptions] = None,
) -> AsyncIterator[StreamMessage]:
    """
    Execute Amp with the given prompt and options.

    Args:
        prompt: The user prompt as a string or async iterator of user input messages
        options: Optional configuration options for Amp execution

    Yields:
        Stream messages from Amp

    Raises:
        CLINotFoundError: If the Amp CLI cannot be found
        ProcessError: If the CLI process fails
        AmpError: For other errors

    Note:
        For timeout and cancellation, use standard asyncio patterns:

        # Timeout
        await asyncio.wait_for(execute("..."), timeout=30.0)

        # Manual cancellation
        task = asyncio.create_task(execute("..."))
        task.cancel()
    """
    # Normalize options
    amp_options = AmpOptions() if options is None else options

    # Find CLI command
    cli_cmd = _find_amp_cli()

    # Generate session ID for temp files
    session_id = str(uuid.uuid4())

    # Build settings file if permissions are provided
    temp_settings_file, temp_dir = await _build_settings_file(amp_options, session_id)

    # Update options settings_file
    if temp_settings_file:
        amp_options.settings_file = temp_settings_file

    # Build arguments
    cli_args = _build_cli_args(amp_options)

    # Build environment variables
    env = _build_environment_variables(amp_options)

    # Set working directory
    cwd = amp_options.cwd if amp_options and amp_options.cwd else os.getcwd()

    # Determine if we're streaming input
    is_streaming = hasattr(prompt, "__aiter__")
    if is_streaming:
        cli_args.append("--stream-json-input")

    # Build full command
    full_cmd = cli_cmd + cli_args

    # Debug logging
    if os.environ.get("AMP_DEBUG") or (amp_options and amp_options.log_level == "debug"):
        print(f"[DEBUG] Executing: {' '.join(full_cmd)}", file=sys.stderr)
        if cwd:
            print(f"[DEBUG] Working directory: {cwd}", file=sys.stderr)

    # Start process
    try:
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
        )
    except FileNotFoundError as e:
        raise CLINotFoundError(f"Failed to start CLI: {e}") from e
    except Exception as e:
        raise AmpError(f"Failed to start process: {e}") from e

    try:
        # Handle input in the background
        if is_streaming:
            input_task = asyncio.create_task(
                _handle_streaming_input(proc, prompt)  # type: ignore
            )
        else:
            input_task = asyncio.create_task(
                _handle_string_input(proc, prompt)  # type: ignore
            )

        # Start process monitoring
        process_task = asyncio.create_task(_wait_for_process(proc))

        # Read and yield output
        async for message in _read_process_output(proc):
            yield message

        # Wait for input and process tasks
        await input_task
        await process_task

    except asyncio.CancelledError:
        # Clean up process on cancellation
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        raise
    except Exception:
        # Clean up process on error
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        raise
    finally:
        # Clean up temporary directory
        if temp_dir:
            with contextlib.suppress(Exception):
                shutil.rmtree(temp_dir)


# ============================================================================
# Utility Functions
# ============================================================================


def create_user_message(text: str) -> UserInputMessage:
    """
    Helper function to create streaming input messages.

    Args:
        text: The message text

    Returns:
        UserInputMessage ready for streaming
    """
    from .types import _UserInputMessageDetails

    return UserInputMessage(
        type="user",
        message=_UserInputMessageDetails(
            role="user", content=[TextContent(type="text", text=text)]
        ),
    )


def create_permission(
    tool: str, action: str, options: Optional[dict[str, Any]] = None
) -> Permission:
    """
    Create a permission object for controlling tool usage.

    Args:
        tool: The name of the tool to which this entry applies
        action: How Amp should proceed ('allow', 'reject', 'ask', 'delegate')
        options: Optional configuration with:
            - matches: Match conditions for tool arguments
            - context: Only apply in this context ('thread' or 'subagent')
            - to: Command to delegate to (required when action is 'delegate')

    Returns:
        Permission object

    Raises:
        ValueError: If delegate action is used without 'to' option

    Example:
        # Allow a specific tool
        create_permission('edit_file', 'allow')

        # Delegate to another command
        create_permission('Bash', 'delegate', {'to': 'bash -c'})

        # Match specific arguments
        create_permission('Read', 'ask', {
            'matches': {'path': '/secret/*'}
        })
    """
    if options is None:
        options = {}

    # Validate delegate action
    if action == "delegate" and not options.get("to"):
        raise ValueError('delegate action requires "to" option')

    # Build permission dict
    permission_data: dict[str, Any] = {"tool": tool, "action": action}

    if "matches" in options:
        permission_data["matches"] = options["matches"]

    if "context" in options:
        permission_data["context"] = options["context"]

    if "to" in options:
        permission_data["to"] = options["to"]

    return Permission(**permission_data)
