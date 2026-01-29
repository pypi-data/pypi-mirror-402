"""
Custom exceptions for the compressor package.
"""


class InterruptedByUserError(Exception):
    """Used to interrupt the compression process in real-time."""

    pass


class CompressorWarning(Warning):
    """Custom warning for non-critical issues."""

    pass


class RecoverableError(Exception):
    """For errors that might be fixable or retried."""

    pass


class FatalError(Exception):
    """For errors that should terminate the operation."""

    pass


class DependencyError(Exception):
    """For missing dependencies."""

    pass
