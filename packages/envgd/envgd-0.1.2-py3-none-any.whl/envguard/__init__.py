"""EnvGuard - Secure environment variable management for Python."""

from .core import BaseConfig, BaseSettings, Env, guard, load, load_with_secrets
from .crypto import decrypt_file, encrypt_file
from .exceptions import (
    AccessError,
    EnvironmentLockError,
    MissingEnvError,
    SafeEnvError,
    TamperError,
    ValidationError,
)

__all__ = [
    "load",
    "load_with_secrets",
    "Env",
    "BaseConfig",
    "BaseSettings",
    "guard",
    "encrypt_file",
    "decrypt_file",
    "SafeEnvError",
    "ValidationError",
    "MissingEnvError",
    "AccessError",
    "EnvironmentLockError",
    "TamperError",
]
