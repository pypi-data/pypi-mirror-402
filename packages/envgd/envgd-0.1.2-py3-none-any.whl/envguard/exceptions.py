"""Custom exceptions for EnvGuard."""

class SafeEnvError(Exception):
    """Base exception for EnvGuard errors."""


class ValidationError(SafeEnvError):
    """Validation failed for a variable."""


class MissingEnvError(SafeEnvError):
    """Required variable is missing."""


class AccessError(SafeEnvError):
    """Access denied to environment variable."""


class EnvironmentLockError(SafeEnvError):
    """Environment locking violation."""


class TamperError(SafeEnvError):
    """File tamper detection triggered."""
