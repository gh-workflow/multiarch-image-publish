"""Project-specific exceptions."""


class InputError(ValueError):
    """Raised when an action input is invalid."""


class CommandError(RuntimeError):
    """Raised when an external command fails."""
