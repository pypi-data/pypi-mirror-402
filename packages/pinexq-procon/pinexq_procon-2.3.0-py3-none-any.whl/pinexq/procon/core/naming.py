import string


ALLOWED_VERSION_CHARS = set(string.ascii_letters + string.digits + '-_.')

def is_valid_version_string(to_check: str) -> bool:
    """
    Checks if the non-empty input string contains ONLY allowed characters.
    Allowed characters are: ASCII letters, numbers, '-', '_', and '.'.

    Args:
        to_check: The string to validate.

    Returns:
        True if all characters in the string are allowed, False otherwise.
    """

    if not to_check:
        return False

    for char in to_check:
        if char not in ALLOWED_VERSION_CHARS:
            return False
    return True

def escape_version_string(string_to_escape: str) -> str:
    """
    Replaces all occurrences of '.' with '|' in the given string.

    Args:
        string_to_escape: The string to modify.

    Returns:
        A new string with all dots replaced by pipes.
    """
    return string_to_escape.replace('.', '/')