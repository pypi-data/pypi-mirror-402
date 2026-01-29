import enum
from typing import Final


class UNSETTYPE(enum.IntEnum):
    token = 0

    def __repr__(self):
        return "NOTSET"

    def __bool__(self):
        return False


UNSET: Final = UNSETTYPE.token  # noqa: E305
