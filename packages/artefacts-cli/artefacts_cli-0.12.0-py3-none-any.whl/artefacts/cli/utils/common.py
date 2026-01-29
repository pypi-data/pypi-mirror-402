from datetime import datetime, timezone
from pathlib import Path
from threading import Thread
from typing import Union
import os
import subprocess
import sys

import click
import requests
from semver import Version

import artefacts_copava as copava
from artefacts import ARTEFACTS_DEFAULT_OUTPUT_DIR

# TODO Add for type checking, but currently blocked by circular dependencies.
# from artefacts.cli import Run
from artefacts.cli.constants import LAST_RUN_MARKER_PATH, LAST_VERSION_MEMO_PATH
from artefacts.cli.i18n import localise
from artefacts.cli.errors import InvalidAPIKey


def base_version(version: str) -> str:
    """
    Extract the "base semver" from our version defined by setuptools-scm
    0.9.7.dev9 -> 0.9.7
    0.9.7      -> 0.9.7
    """
    if "dev" in version:
        return version[0 : version.rindex(".")]
    else:
        return version


def background_version_check(current: str, memo_file: Path) -> None:
    """
    Detect whether a new version of CLI is available

    In case of network or other error, this fails silently
    to avoid cluttering the CLI output.
    """
    try:
        card = requests.get(
            "https://pypi.org/simple/artefacts-cli",
            headers={"Accept": "application/vnd.pypi.simple.v1+json"},
        )
        card.raise_for_status()
        latest = sorted(card.json()["versions"])[-1]
        if Version.parse(base_version(current)) < Version.parse(base_version(latest)):
            with open(memo_file, "w") as f:
                f.write(latest)
    except:  # noqa: E722
        pass
    return None


def new_version_available(
    current: str,
    memo_file: Path = Path(LAST_VERSION_MEMO_PATH),
    threaded_best_effort: bool = True,
) -> str | None:
    """
    Report any new version available.
    """
    result = None
    if is_first_run_today():
        if memo_file.exists():
            version = None
            try:
                with open(memo_file) as f:
                    version = f.read().strip()
            except:  # noqa: E722
                pass
            # Separate try block for unlink,
            # to ensure cleanup. Silence
            # failure to avoid impacting UX.
            try:
                memo_file.unlink()
            except:  # noqa: E722
                pass
            result = version
        else:
            if threaded_best_effort:
                best_effort = Thread(
                    target=background_version_check,
                    args=(
                        current,
                        memo_file,
                    ),
                )
                best_effort.start()
            else:
                background_version_check(current, memo_file)
            result = None
    return result


def is_first_run_today(
    now: datetime = datetime.now(timezone.utc),
    marker_file: Path = Path(LAST_RUN_MARKER_PATH),
) -> bool | None:
    """
    Check if the CLI has been run today, by maintaining a marker of the
    last known run.
    """
    # End Of Today
    eot = int(datetime(now.year, now.month, now.day, 23, 59, 59).timestamp())
    try:
        if marker_file.exists():
            with open(marker_file, "r") as f:
                marker = int(f.read().strip())
            if marker < eot:
                with open(marker_file, "w") as f:
                    f.write(str(eot))
                return True
            else:
                return False
        else:
            with open(marker_file, "w") as f:
                f.write(str(eot))
            return True
    except ValueError:
        # Internal error, or someone messing with the managed file.
        # Move the offending file, and assume first run for today.
        marker_file.replace(f"{marker_file}.offending.{int(now.timestamp())}")
        return True
    except (IOError, OSError):
        # Some file related error. We cannot say much, so report unknown state.
        # Note `None` is falsy, so `if` checks will skip their block. This is
        # wanted in current usage, typically to avoid continue a run under
        # OS/IO errors.
        return None


def run_and_save_logs(
    args,
    output_path,
    shell=False,
    executable=None,
    env=None,
    cwd=None,
    with_output=False,
):
    """
    Run a command and save stdout and stderr to a file in output_path

    Note: explicitly list used named params instead of using **kwargs to avoid typing issue: https://github.com/microsoft/pyright/issues/455#issuecomment-780076232
    """
    output_file = open(output_path, "wb")

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,  # Capture stdout
        stderr=subprocess.PIPE,  # Capture stderr
        shell=shell,
        executable=executable,
        env=env,
        cwd=cwd,
    )
    # write test-process stdout and stderr into file and stdout
    stderr_content = ""
    stdout_content = ""
    if proc.stdout:
        for line in proc.stdout:
            decoded_line = line.decode()
            sys.stdout.write(decoded_line)
            output_file.write(line)
            stdout_content += decoded_line
    if proc.stderr:
        output_file.write("[STDERR]\n".encode())
        for line in proc.stderr:
            decoded_line = line.decode()
            sys.stderr.write(decoded_line)
            output_file.write(line)
            stderr_content += decoded_line
    proc.wait()
    if with_output:
        return proc.returncode, stdout_content, stderr_content
    return proc.returncode


def read_config(filename: str) -> dict:
    """
    Read an Artefacts configuration file.

    Report and abort the UX if the file is not found.
    """
    try:
        return read_config_raw(filename)
    except FileNotFoundError:
        raise click.ClickException(
            localise(
                "Project config file {file_name} not found.".format(file_name=filename)
            )
        )


def read_config_raw(filename: str) -> dict:
    """
    Read an Artefacts configuration file.

    The difference with the legacy read_config is that this
    function can return a FileNotFoundError and does not
    abort the UX.
    """
    with open(filename) as f:
        return copava.parse(f.read()) or {}


# Click callback syntax
def config_validation(context: click.Context, param: str, value: str) -> str:
    if context.params.get("skip_validation", False):
        return value
    config = read_config(value)
    errors = copava.check(config)
    if len(errors) == 0:
        return value
    else:
        raise click.BadParameter(pretty_print_config_error(errors))


def pretty_print_config_error(
    errors: Union[str, list, dict], indent: int = 0, prefix: str = "", suffix: str = ""
) -> str:
    if type(errors) is str:
        header = "  " * indent
        output = header + prefix + errors + suffix
    elif type(errors) is list:
        _depth = indent + 1
        output = []
        for value in errors:
            output.append(pretty_print_config_error(value, indent=_depth, prefix="- "))
        output = os.linesep.join(output)
    elif type(errors) is dict:
        _depth = indent + 1
        output = []
        for key, value in errors.items():
            output.append(pretty_print_config_error(key, indent=indent, suffix=":"))
            output.append(pretty_print_config_error(value, indent=_depth))
        output = os.linesep.join(output)
    else:
        # Must not happen, so broad definition, but we want to know fast.
        raise Exception(f"Unacceptable data type for config error formatting: {errors}")
    return output


def add_output_from_default(run) -> None:
    """
    Add every file found under ARTEFACTS_DEFAULT_OUTPUT_DIR to the set of files
    uploaded to Artefacts for the run argument.

    The default folder is created either directly, or more generally by Artefacts
    toolkit libraries.
    """
    if ARTEFACTS_DEFAULT_OUTPUT_DIR.exists() and ARTEFACTS_DEFAULT_OUTPUT_DIR.is_dir():
        for root, dirs, files in os.walk(ARTEFACTS_DEFAULT_OUTPUT_DIR):
            for file in files:
                run.log_artifacts(Path(root) / Path(file))


def project_info_from(project_id: str) -> tuple:
    """
    Get the project information from typical project IDs used around the system to date.

    Project information consists of the project organisation and the project actual name in that organisation.

    To date, project IDs are typically org/project.
    """
    try:
        # Split and return are separated to trigger unpacking early,
        # and get ValueError when the expected unpack format does not happen.
        org, proj = project_id.split("/", maxsplit=1)
        return org, proj
    except (AttributeError, ValueError):
        raise click.ClickException(
            localise(
                'The project field must include the organization name in the format "org/project". Got: "{project_id}"'
            ).format(project_id=project_id)
        )


def ask_for_non_empty_string(message: str, secret: bool = False) -> str:
    """
    Wrapper around click.prompt to check for None and empty strings.
    """

    def non_empty_str(value):
        if value:
            vs = str(value)
            if len(vs) > 0:
                return vs
        raise InvalidAPIKey()

    return click.prompt(message, type=str, hide_input=secret, value_proc=non_empty_str)


def append_text_if_file(
    base: str, text_file_path: Path | str, join_str: str = "\n"
) -> str:
    """
    Append the content of a text file to a base string. Appending uses `join_str` to
    join base and the content.

    The function returns the `base + join_str + content` if no error.
    When the file does not exist, the function returns `base`.
    """
    try:
        with open(text_file_path) as f:
            return join_str.join([base, f.read()]).strip()
    except FileNotFoundError:
        return base
