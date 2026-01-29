import importlib.metadata
import platform
from fnmatch import fnmatch
from os import environ
from typing import Sequence

import logging

logger = logging.getLogger(__name__)


def log_version_info(log: bool = False) -> None:
    """Log info about the platform and installed packages.

    Args:
        log: If true, the info is sent to a logger, otherwise it's just printed. (default: False)
    """

    output = print
    if log:
        output = logger.info

    message = [
        "Platform and package information:",
        f"OS: {platform.platform()}",
        f"Python: {platform.python_implementation()} {platform.python_version()}",
    ]

    # Collection version info for installed packages. (The list are package names, not the import names)
    packages = ("pinexq-procon", "pinexq-client")
    for p in packages:
        message.append(f"{p}: {importlib.metadata.version(p)}")

    output("\n".join(message))


def remove_environment_variables(include: Sequence[str]|None=None, exclude: Sequence[str]|None=None) -> None:
    """Removes environment variables from the current environment.

    Args:
        include: A list of pattern strings that may include wildcards *.
            If an environment variable matches any of these, it will be marked for removal. (default: ["*"])
        exclude: A list of pattern strings that may include wildcards *.
            If an environment variable matches any of these, it will be exempt from removal,
            even though it might match an include pattern.
    """
    if include is None:
        include = ["*"]
    if exclude is None:
        exclude = []

    vars_to_remove = [
        name
        for name, value in environ.items()
        if any((fnmatch(name, incl_pattern) for incl_pattern in include)) and \
           not any((fnmatch(name, excl_pattern) for excl_pattern in exclude))
    ]
    for name in vars_to_remove:
       del environ[name]

    logger.debug(f"Removed environment variables: {vars_to_remove}")
