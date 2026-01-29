"""SRM-HGA core exceptions.

These exceptions are intentionally small and stable. Higher-level layers may
wrap and re-raise with more context.
"""

from __future__ import annotations


class SRMHGAError(Exception):
    """Base class for SRM-HGA errors."""


class ValidationError(SRMHGAError, ValueError):
    """Raised when input validation fails."""


class UserConfirmationRequired(SRMHGAError):
    """Raised when a policy requires explicit user confirmation."""


class BackendError(SRMHGAError):
    """Raised when a storage backend fails."""


class NotFound(SRMHGAError, KeyError):
    """Raised when a record is not found."""
