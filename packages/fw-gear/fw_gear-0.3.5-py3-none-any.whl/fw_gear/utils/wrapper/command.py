"""Wrapper for executing shell commands using Python's subprocess library.



This module provides a streamlined interface for constructing and executing
command-line processes. It simplifies handling subprocess calls by dynamically
building command-line arguments from configuration parameters (e.g., `config.json`),
managing environment variables, and providing structured error handling.

Features:
- Builds command-line arguments dynamically from key-value parameter mappings.
- Executes shell commands with logging, error handling, and real-time output streaming.
- Supports dry-run mode for debugging without executing commands.
- Captures `stdout` and `stderr`, raising an exception for non-zero exit codes.

Examples:
    >>> command = ["ls"]
    >>> param_list = {"l": True, "a": True, "h": True}
    >>> command = build_command_list(command, param_list)
    >>> command
    ["ls", "-l", "-a", "-h"]
    >>> exec_command(command)

    Another example using parameters with values:
    >>> command = ["du"]
    >>> params = {"a": True, "human-readable": True, "max-depth": 3}
    >>> command = build_command_list(command, params)
    >>> command
    ["du", "-a", "--human-readable", "--max-depth=3"]
    >>> params = {"dir1": ".", "dir2": "/tmp"}
    >>> command = build_command_list(command, params, include_keys=False)
    >>> command
    ["du", ".", "/tmp"]
    >>> exec_command(command)

These examples demonstrate how command-line parameters can be dynamically
constructed and executed from gear configuration options.
"""

import contextlib
import logging
import os
import re
import shlex
import subprocess as sp
import time
import typing as t

log = logging.getLogger(__name__)

# literal shell tokens we allow unquoted when shell=True
_SHELL_REDIRECT_TOKENS = {
    ">",
    ">>",
    "<",
    "1>",
    "1>>",
    "2>",
    "2>>",
    "2>&1",
    "1>&2",
}
# generic "important" line detector (override via env in Docker image if you want)
_ALWAYS_PRINT_RE = re.compile(
    os.getenv(
        "EXEC_ALWAYS_PRINT_RE",
        r"\b(error|fatal|exception|critical|traceback|segfault|segv|abort|oom|"
        r"out\s+of\s+memory|warn(?:ing)?|failed)\b",
    ),
    re.I,
)


def _remove_prohibited_values(param_list: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Removes `None` values and empty strings from a parameter dictionary.

    Args:
        param_list (Dict[str, Any]): Dictionary of command-line parameters.

    Returns:
        Dict[str, Any]: A cleaned dictionary with empty values removed.
    """
    param_list_new = param_list.copy()
    for key, value in param_list.items():
        if value is None or value == "":
            param_list_new.pop(key)
            log.warning(f'Removing parameter with empty value for key "{key}".')
    return param_list_new


def build_command_list(
    command: t.List[str], param_list: t.Dict[str, t.Any], include_keys: bool = True
) -> t.List[str]:
    """Constructs a command-line argument list for subprocess execution.

    Args:
        command (List[str]): Base command (e.g., `["ls"]`), including required parameters.
        param_list (Dict[str, any]): Dictionary of key-value pairs representing command-line arguments.
            - Boolean values (`True`) result in flags (`-k` or `--key`).
            - String/integer values are formatted as `--key=value` or `-k value`.
            - `None` or empty strings are ignored.
        include_keys (bool, optional): Whether to include parameter keys in the command list. Defaults to True.

    Returns:
        List[str]: A formatted command list suitable for `subprocess.Popen`.

    Example:
        >>> command = ["du"]
        >>> params = {"a": True, "human-readable": True, "max-depth": 3}
        >>> command = build_command_list(command, params)
        >>> command
        ["du", "-a", "--human-readable", "--max-depth=3"]
    """
    param_list = _remove_prohibited_values(param_list)
    for key in param_list.keys():
        # Single character command-line parameters are preceded by a single "-"
        if len(key) == 1:
            # If Param is boolean and true, include, else exclude
            if isinstance(param_list[key], bool) and param_list[key]:
                command.append("-" + key)
            else:
                if include_keys:
                    command.append("-" + key)
                if str(param_list[key]):
                    command.append(str(param_list[key]))
        # Multi-Character command-line parameters are preceded by a double "--"
        # If Param is boolean and true include, else exclude
        elif isinstance(param_list[key], bool):
            if param_list[key] and include_keys:
                command.append("--" + key)
        else:
            item = ""
            if include_keys:
                item = "--" + key
                item = item + "="
            item = item + str(param_list[key])
            command.append(item)
    return command


# ruff: noqa: PLR0912, PLR0915
def exec_command(
    command: t.List[str],
    dry_run: bool = False,
    environ: t.Optional[t.Dict[str, str]] = None,
    shell: bool = False,
    stream: bool = False,
    stream_mode: t.Optional[str] = None,  # "all" | "filter_only" | "throttled" | None
    throttle_sec: float = 1.0,  # used if stream_mode="throttled"
    logfile: t.Optional[t.Union[str, os.PathLike]] = None,  # tee full stream to file
) -> t.Tuple[str, str, int]:  # noqa: PLR0912, PLR0915
    """
    Executes a shell command using the subprocess module with flexible output handling.

    Args:
        command (List[str]): List of command-line arguments, starting with the command itself.
        dry_run (bool, optional): If True, logs the command without executing it. Returns ("", "", 0).
            Defaults to False.
        environ (Optional[Dict[str, str]], optional): Additional environment variables to merge with
            the current environment. Defaults to None.
        shell (bool, optional): Run via system shell (required for redirects/pipes). When True,
            only literal tokens (">", ">>", "<", "1>", "1>>", "2>", "2>>", "2>&1", "1>&2")
            are left unquoted; all other arguments are safely quoted. Defaults to False.
        stream (bool, optional): Enable live streaming of output line-by-line (deadlock-safe).
            When True, stderr is merged into stdout. Defaults to False.
        stream_mode (Optional[str], optional): Controls what is printed during streaming:
            - "all": Print every line in real-time (default)
            - "filter_only": Only print lines matching important patterns (errors, warnings, etc.)
            - "throttled": Print important lines immediately, rate-limit others
            Full output is always captured regardless of mode. Defaults to "all".
        throttle_sec (float, optional): Minimum time in seconds between printing non-important
            lines in "throttled" mode. Defaults to 1.0.
        logfile (Optional[Union[str, os.PathLike]], optional): Path to append the full unfiltered
            output stream. Works with all streaming modes. Defaults to None.

    Returns:
        Tuple[str, str, int]: A tuple containing:
            - stdout (str): Standard output from the command. When stream=True, contains
              merged stdout+stderr.
            - stderr (str): Standard error output. Empty string ("") when stream=True.
            - returncode (int): Command exit status (0 for success).

    Raises:
        RuntimeError: If the command returns a non-zero exit code, or if the logfile
            cannot be opened for writing.

    Notes:
        - Streaming is automatically disabled when shell redirection tokens are detected
        - Important lines are detected via regex pattern (configurable via EXEC_ALWAYS_PRINT_RE env var)
        - In "throttled" mode, a final suppressed line count is printed at the end
        - The logfile path is validated before command execution (fail-fast behavior)

    Example:
            >>> command = ["du"]
            >>> params = {"a": True, "human-readable": True, "max-depth":3}
            >>> command = build_command_list(command, params)
            >>> params = {"dir1":".","dir2":"/tmp"}
            >>> command = build_command_list(command, params, include_keys=False)
            >>> exec_command(command)
            # 1) Basic run (no live streaming)
            >>> stdout, stderr, rc = exec_command(command)

            # 2) Live stream only important lines; keep full transcript
            >>> stdout, stderr, rc = exec_command(
            ...     command, stream=True, stream_mode="filter_only", logfile="du.stream.log"
            ... )

            # 3) If you truly need shell redirection (no streaming)
            >>> cmd2 = command + [">>", "du.out.log", "2>&1"]
            >>> stdout, stderr, rc = exec_command(cmd2, shell=True, stream=False)
    """
    # grab env - preserve PATH etc
    env = os.environ.copy()
    if environ:
        env.update(environ)

    # sanitize shell
    if shell:
        run_command = " ".join(
            (s if s in _SHELL_REDIRECT_TOKENS else shlex.quote(s))
            for s in map(str, command)
        )
    else:
        # No shell: pass a list (no quoting).
        run_command = [str(a) for a in command]

    # Log the command that will be executed (after quoting/sanitization)
    if shell:
        log.info(f"Executing command:\n {run_command}\n\n")
    else:
        log.info(f"Executing command:\n {shlex.join(run_command)}\n\n")

    # Return dry-run immediately after logging
    if dry_run:
        return "", "", 0

    # Validate logfile if specified before running command
    if logfile is not None:
        try:
            with open(logfile, "a"):
                pass  # Just test if we can open for appending
        except (OSError, IOError) as e:
            raise RuntimeError(f"Cannot open logfile '{logfile}': {e}") from e

    # to disable streaming if redirecting
    has_redirect = shell and any(str(a) in _SHELL_REDIRECT_TOKENS for a in command)

    # merge stderr only for streaming (keeps non-streaming behavior closer to before)
    stderr_target = sp.STDOUT if stream else sp.PIPE

    result = sp.Popen(
        run_command,
        stdout=sp.PIPE,
        stderr=stderr_target,  # merge in streaming to avoid deadlock
        stdin=sp.DEVNULL,  # child won't wait for input
        universal_newlines=True,  # text=True
        env=env,
        shell=shell,
        bufsize=1,  # line-buffered for timely lines
    )

    # streaming path (live), unless redirecting (breaks streaming)
    if stream and not has_redirect:
        out_lines: t.List[str] = []

        # normalize mode (default = "all")
        mode = (stream_mode or "all").lower()
        if mode not in {"all", "filter_only", "throttled"}:
            mode = "all"

        last_print = 0.0
        suppressed = 0

        with (
            open(logfile, "a") if logfile is not None else contextlib.nullcontext(None)
        ) as lf:
            for line in iter(result.stdout.readline, ""):
                out_lines.append(line)
                if lf is not None:
                    lf.write(line)
                    lf.flush()

                # what to print
                show_now = True
                if mode == "filter_only":
                    show_now = bool(_ALWAYS_PRINT_RE.search(line))
                elif mode == "throttled":
                    if _ALWAYS_PRINT_RE.search(line):
                        # important lines - print immediately
                        if suppressed:
                            print(f"(suppressed {suppressed} lines)", flush=True)
                            suppressed = 0
                        last_print = time.monotonic()
                        show_now = True
                    else:
                        now = time.monotonic()
                        if now - last_print >= throttle_sec:
                            if suppressed:
                                print(f"(suppressed {suppressed} lines)", flush=True)
                                suppressed = 0
                            last_print = now
                            show_now = True
                        else:
                            suppressed += 1
                            show_now = False
                # mode "all": show every line

                if show_now:
                    print(line, end="", flush=True)

            if mode == "throttled" and suppressed:
                print(f"(suppressed {suppressed} lines)", flush=True)

        returncode = result.wait()
        stdout = "".join(out_lines)
        stderr = ""  # merged into stdout during streaming

    # non-streaming path - buffered, prints at end
    else:
        stdout, stderr = result.communicate()
        returncode = result.returncode
        if stdout:
            log.info(stdout)

    log.info(f"Command return code: {returncode}")

    if returncode != 0:
        # If streaming, errors may be in stdout
        err_text = stderr or stdout
        if err_text:
            log.error(err_text)
        raise RuntimeError(
            f"Command failed with exit code {returncode}: {shlex.join(map(str, command))}"
        )

    return stdout, stderr, returncode
