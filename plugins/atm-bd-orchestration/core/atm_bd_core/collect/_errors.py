"""Shared failures from collector reads and decoding."""
from subprocess import SubprocessError

READ_ERRORS = (OSError, RuntimeError, SubprocessError, ValueError, TypeError, KeyError)
