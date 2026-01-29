import re
from typing import Any, Callable

from pydantic import Field
from pydantic.dataclasses import dataclass

from ..core.types import UNSET, UNSETTYPE


METADATA_ANNOTATION_NAME = "__pxq_metadata__"

# Version string regex
VERSION_PATTERN = r"""
    ^(?:                                                # start of the string
        (?P<version>[0-9]{1,8}(?:\.[0-9]{1,8}){,2})     # version number
        (?:-(?P<postfix>[0-9a-zA-Z_-]+))?               # postfix string
    )$                                                  # end of the string
"""
version_regex = re.compile(VERSION_PATTERN, flags=re.VERBOSE)

# Regex pattern for just the postfix substring for pydantic
POSTFIX_PATTERN = r"^[0-9a-zA-Z_-]*$"
postfix_regex = re.compile(POSTFIX_PATTERN)

# Restrictions
# <major:int>.<minor:int>.<patch:int>-<string> mit max 40 chars
# maj/min/patch each <= 8 chars , defaults == 0

MAX_VERSION_LENGTH = 40


@dataclass
class version:
    """Decorator to attach version information to a Step function.

    Attributes:
        version: ...

    """

    version: str | UNSETTYPE = Field(default=UNSET, pattern=version_regex)
    major: int | UNSETTYPE = Field(default=UNSET, ge=0, lt=100_000_000, kw_only=True)
    minor: int | UNSETTYPE = Field(default=UNSET, ge=0, lt=100_000_000, kw_only=True)
    patch: int | UNSETTYPE = Field(default=UNSET, ge=0, lt=100_000_000, kw_only=True)
    postfix: str | UNSETTYPE = Field(default=UNSET, pattern=postfix_regex, kw_only=True)


    def __post_init__(self):
        version_was_set = self.version is not UNSET
        any_specifier_was_set = (self.major is not UNSET or self.minor is not UNSET
                                 or self.patch is not UNSET or self.postfix is not UNSET)
        if not (version_was_set or any_specifier_was_set):
            self.major = 0  # default value when no parameter was given
        elif not (version_was_set ^ any_specifier_was_set):
            raise ValueError("You have to define the version either as a string or explicitly via the "
                             "'major', 'minor', 'patch', 'postfix' keyword, but not both!")

        if not version_was_set:
            self._set_version_from_kwargs()

        if len(self.version) > MAX_VERSION_LENGTH:
            raise ValueError(f"The version string is too long! "
                             f"Max {MAX_VERSION_LENGTH} chars are allowed, but it has {len(self.version)} chars.")

    def _set_version_from_kwargs(self):
        """Generate the version string from single kwarg variables"""
        # The default string will always be "0.0.0" and all values and postfix are optional
        self.version = (f"{self.major or '0'}.{self.minor or '0'}.{self.patch or '0'}"
                        f"{f'-{self.postfix}' if self.postfix else ''}")


    def __call__(self, function: Callable[[Any], Any]):
        """Called when used as a decorator to attach metadata to 'func'."""
        metadata = function.__dict__.setdefault(METADATA_ANNOTATION_NAME, {})
        metadata["version"] = self

        return function

    def __str__(self) -> str:
        return self.version

def get_version_metadata(function: Callable[[Any], Any]) -> version:
    metadata = getattr(function, METADATA_ANNOTATION_NAME, {})
    return metadata.get("version", version())