"""Core environment loading and validation functionality."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Dict, Optional, Set, Type, Union

from .crypto import calculate_hash_sum, decrypt_file
from .exceptions import (
    AccessError,
    EnvironmentLockError,
    MissingEnvError,
    SafeEnvError,
    TamperError,
    ValidationError,
)

try:
    from .secrets import load_from_secrets
except ImportError:
    load_from_secrets = None

class Env:
    """Environment variable container with security features."""

    def __init__(
        self,
        data: Dict[str, Any],
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
        scoped_mode: bool = False,
    ) -> None:
        """Initialize Env instance.

        Args:
            data: Dictionary of environment variables.
            file_path: Path to the source file, if any.
            file_hash: Initial hash of the file for tamper detection.
            scoped_mode: Enable scoped access protection.
        """
        self._data = data
        self._file_path = file_path
        self._initial_hash = file_hash
        self._scoped_mode = scoped_mode
        self._in_scope = False
        self._locked_env: Optional[str] = None

    def to_pydantic(self, model_cls: Type[Any]) -> Any:
        """Cast loaded environment variables to a Pydantic model.

        Args:
            model_cls: Pydantic model class to instantiate.

        Returns:
            Instance of the Pydantic model with loaded data.
        """
        return model_cls(**self._data)

    def __getattr__(self, name: str) -> Any:
        """Get environment variable by name.

        Args:
            name: Variable name to retrieve.

        Returns:
            Variable value.

        Raises:
            AccessError: If scoped mode is enabled and not in scope.
            AttributeError: If variable doesn't exist.
        """
        if self._scoped_mode and not self._in_scope:
            raise AccessError(
                f"Access to '{name}' denied outside of scope."
            )

        if name in self._data:
            return self._data[name]

        raise AttributeError(f"'Env' object has no attribute '{name}'")

    @contextmanager
    def scope(self) -> Any:
        """Context manager to temporarily enable access to variables.

        Yields:
            Self for chaining.
        """
        token = self._in_scope
        self._in_scope = True
        try:
            yield self
        finally:
            self._in_scope = token

    def status(self) -> None:
        """Display security status report to stdout.

        Information includes the configuration source, item count, and active
        security features (Tamper Protection, Environment Locking). Sensitive
        keys are automatically masked.
        """
        print("\nEnvGuard Security Report")
        print("-" * 40)
        print(f"Source: {self._file_path or 'System Environment'}")
        print(f"Items Protected: {len(self._data)}")

        secret_keywords = ["KEY", "SECRET", "PASS", "TOKEN"]
        for key, value in list(self._data.items())[:3]:
            is_secret = any(
                keyword in key.upper() for keyword in secret_keywords
            )
            masked_value = "********" if is_secret else value
            print(f"  - {key}: {masked_value}")

        if len(self._data) > 3:
            print(f"  ... (+{len(self._data) - 3} more)")

        if self._initial_hash:
            print("Tamper Protection: Active")
        if self._locked_env:
            print(f"Environment Lock: {self._locked_env}")
        print("-" * 40 + "\n")

    def lock(self, environment: str) -> None:
        """Lock the environment to a specific value.

        If the loaded configuration implies a different environment,
        raises EnvironmentLockError.

        This checks if 'APP_ENV', 'ENVIRONMENT', or 'ENV' matches the
        locked value.

        Args:
            environment: Environment name to lock to.

        Raises:
            EnvironmentLockError: If environment mismatch detected.
        """
        env_keys = [
            "APP_ENV",
            "ENVIRONMENT",
            "ENV",
            "FLASK_ENV",
            "DJANGO_ENV",
        ]
        found_env = None
        for key in env_keys:
            if key in self._data:
                found_env = self._data[key]
                break

        if found_env and found_env != environment:
            raise EnvironmentLockError(
                f"Environment locked to '{environment}' but loaded "
                f"configuration indicates '{found_env}'"
            )

        self._locked_env = environment

    def verify(self) -> None:
        """Verify if the source file has been modified since load.

        Raises:
            TamperError: If file hash doesn't match initial hash.
        """
        if not self._file_path or not self._initial_hash:
            return

        from .crypto import calculate_file_hash

        current_hash = calculate_file_hash(self._file_path)
        if current_hash != self._initial_hash:
            raise TamperError("Environment file modified after load")

class BaseConfig:
    """Lightweight base class for class-based environment configuration.

    Provides a way to load environment variables into class attributes
    without external dependencies like Pydantic.
    """

    @classmethod
    def load(
        cls,
        path: str = ".env",
        encrypted: bool = False,
        scoped: bool = False,
        environment: Optional[str] = None,
        fallback: Optional[str] = None,
        template: Optional[str] = None,
        use_template_defaults: bool = False,
    ) -> BaseConfig:
        """Load and validate configuration, returning a populated instance.

        Args:
            path: Path to the environment file.
            encrypted: Whether the file is encrypted.
            scoped: Enable scoped access protection.
            environment: Environment name for multi-environment support.
            fallback: Fallback path if environment file not found.
            template: Path to template file for validation.
            use_template_defaults: Use template values as defaults.

        Returns:
            Populated instance of the config class.
        """
        schema = getattr(cls, "__annotations__", {})
        env = load(
            path=path,
            schema=schema,
            encrypted=encrypted,
            scoped=scoped,
            environment=environment,
            fallback=fallback,
            template=template,
            use_template_defaults=use_template_defaults,
        )

        instance = cls()
        for key, value in env._data.items():
            object.__setattr__(instance, key, value)

        object.__setattr__(instance, "_env_guard", env)
        return instance

    def verify(self) -> None:
        """Verify integrity of the loaded environment.

        Raises:
            TamperError: If file has been modified.
        """
        if hasattr(self, "_env_guard"):
            self._env_guard.verify()

try:
    from pydantic import BaseModel

    HAS_PYDANTIC = True
except ImportError:
    # Placeholder for type checking when Pydantic is not installed
    class BaseModel:  # noqa: N801
        """Placeholder BaseModel when Pydantic is not installed."""

        pass

    HAS_PYDANTIC = False


class BaseSettings(BaseModel):
    """Pydantic-style settings class with automatic environment loading.

    Automatically loads and secures environment variables using EnvGuard.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize settings class, loading data from the environment.

        Args:
            **kwargs: Overrides for configuration or environment variables.
                Special keys: _env_file, _env_lock, _encrypted, _scoped.

        Raises:
            ImportError: If Pydantic is not installed.
        """
        if not HAS_PYDANTIC:
            raise ImportError(
                "Pydantic is required for BaseSettings. "
                "Install with 'pip install envguard[pydantic]'"
            )

        config = getattr(self, "model_config", {}) or getattr(
            self, "Config", {}
        )

        env_file = kwargs.pop("_env_file", config.get("env_file", ".env"))
        env_lock = kwargs.pop("_env_lock", config.get("env_lock", None))
        encrypted = kwargs.pop("_encrypted", config.get("encrypted", False))
        scoped = kwargs.pop("_scoped", config.get("scoped", False))
        environment = kwargs.pop("_environment", config.get("environment", None))
        fallback = kwargs.pop("_fallback", config.get("fallback", None))
        template = kwargs.pop("_template", config.get("template", None))
        use_template_defaults = kwargs.pop(
            "_use_template_defaults", config.get("use_template_defaults", False)
        )

        env = load(
            path=env_file,
            schema=self.__class__,
            encrypted=encrypted,
            scoped=scoped,
            environment=environment,
            fallback=fallback,
            template=template,
            use_template_defaults=use_template_defaults,
        )

        if env_lock:
            env.lock(env_lock)

        data = {**env._data, **kwargs}
        super().__init__(**data)
        object.__setattr__(self, "_env_guard", env)

    def verify(self) -> None:
        """Verify the health of the loaded configuration.

        Raises:
            TamperError: If file has been modified.
        """
        if hasattr(self, "_env_guard"):
            self._env_guard.verify()

def load(
    path: str = ".env",
    schema: Optional[Union[Dict[str, Any], Type[Any]]] = None,
    encrypted: bool = False,
    scoped: bool = False,
    environment: Optional[str] = None,
    fallback: Optional[str] = None,
    template: Optional[str] = None,
    use_template_defaults: bool = False,
) -> Env:
    """Load environment variables from a file with validation and protection.

    Args:
        path: Path to the environment file.
        schema: A dictionary or class defining the expected environment
            structure.
        encrypted: Whether the file is AES encrypted.
        scoped: Whether to enable scoped access protection.
        environment: Environment name (e.g., "production", "development").
            If provided, loads path with environment suffix (e.g., .env.production).
        fallback: Fallback path if environment-specific file not found.
            Defaults to original path if None.
        template: Path to template file (e.g., ".env.template").
            Used for validation and documentation of required variables.
        use_template_defaults: If True, use template values as defaults
            for missing variables. Defaults to False.

    Returns:
        An Env object containing the validated data.

    Raises:
        SafeEnvError: For override violations or general errors.
        MissingEnvError: If a required variable is missing.
        ValidationError: If a variable fails type validation.
    """
    # Multi-environment file support
    actual_path = _resolve_environment_path(path, environment, fallback, encrypted)
    
    # Load template if provided
    template_vars: Dict[str, str] = {}
    if template:
        template_vars = _load_template(template)

    if isinstance(schema, type) and issubclass(schema, BaseConfig):
        return schema.load(path=actual_path, encrypted=encrypted, scoped=scoped)

    required_fields: Optional[Set[str]] = None

    if isinstance(schema, type):
        if hasattr(schema, "model_fields") or hasattr(schema, "__fields__"):
            if hasattr(schema, "model_fields"):
                schema_items = schema.model_fields
                required_fields = {
                    k for k, v in schema_items.items() if v.is_required()
                }
                schema = {k: v.annotation for k, v in schema_items.items()}
            else:
                schema_items = schema.__fields__
                required_fields = {
                    k for k, v in schema_items.items() if v.required
                }
                schema = {k: v.type_ for k, v in schema_items.items()}
        elif issubclass(schema, BaseConfig):
            return schema.load(path=actual_path, encrypted=encrypted, scoped=scoped)

    if required_fields is None:
        if isinstance(schema, dict):
            required_fields = set(schema.keys())
        else:
            required_fields = set()

    if encrypted:
        content = decrypt_file(actual_path)
    else:
        try:
            with open(actual_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            content = ""

    parsed_vars = _parse_env_content(content)
    
    # Merge template defaults if enabled
    if template_vars and use_template_defaults:
        for key, value in template_vars.items():
            if key not in parsed_vars:
                parsed_vars[key] = value
    
    # Validate against template
    if template_vars:
        missing_vars = set(template_vars.keys()) - set(parsed_vars.keys())
        if missing_vars and not use_template_defaults:
            raise MissingEnvError(
                f"Missing required variables from template: {', '.join(sorted(missing_vars))}"
            )
    
    file_hash: Optional[str] = None
    if os.path.exists(actual_path):
        with open(actual_path, "rb") as f:
            file_hash = calculate_hash_sum(f.read())

    final_data: Dict[str, Any] = {}

    if schema:
        for key, type_or_validator in schema.items():
            if key in os.environ:
                if key in parsed_vars:
                    raise SafeEnvError(
                        f"{key} already exists in system environment. "
                        "Override not allowed."
                    )

                val = os.environ[key]
            else:
                if key not in parsed_vars:
                    if required_fields is not None and key in required_fields:
                        raise MissingEnvError(
                            f"Missing required environment variable {key}"
                        )
                    continue
                val = parsed_vars[key]

            try:
                if isinstance(type_or_validator, type):
                    if type_or_validator is bool:
                        val_lower = str(val).lower()
                        if val_lower in ("true", "1", "yes", "on"):
                            val = True
                        elif val_lower in ("false", "0", "no", "off"):
                            val = False
                        else:
                            raise ValueError(f"Invalid boolean value: {val}")
                    else:
                        val = type_or_validator(val)
                elif callable(type_or_validator):
                    val = type_or_validator(val)
            except (ValueError, TypeError) as e:
                type_name = (
                    type_or_validator.__name__
                    if hasattr(type_or_validator, "__name__")
                    else "type"
                )
                raise ValidationError(
                    f"{key} must be valid {type_name}: {e}"
                ) from e

            final_data[key] = val

    else:
        for key, val in parsed_vars.items():
            if key in os.environ:
                raise SafeEnvError(
                    f"{key} already exists in system environment. "
                    "Override not allowed."
                )
            final_data[key] = val

    return Env(
        data=final_data,
        file_path=actual_path,
        file_hash=file_hash,
        scoped_mode=scoped,
    )

def guard(
    schema: Optional[Union[Dict[str, Any], Type[Any]]] = None,
    verbose: bool = True,
    **kwargs: Any,
) -> Union[Env, Any]:
    """Primary entry point for creating a secured environment.

    Returns either an Env object or a populated Pydantic/BaseSettings
    instance based on the provided schema/class.

    Args:
        schema: Optional schema or class for validation.
        verbose: If true, prints a security status report.
        **kwargs: Arguments passed to the loading engine.
            Supported: path, encrypted, scoped, environment, fallback

    Returns:
        Env object or Pydantic/BaseSettings instance.

    Examples:
        ```python
        # Basic usage
        config = guard(Config)

        # With multi-environment support
        config = guard(Config, environment="production")

        # With all options
        config = guard(
            Config,
            path=".env",
            environment="production",
            encrypted=False,
            scoped=False,
            verbose=False
        )
        ```
    """
    if isinstance(schema, type):
        if issubclass(schema, BaseSettings):
            instance = schema(**kwargs)
            if verbose and hasattr(instance, "_env_guard"):
                instance._env_guard.status()
            return instance

        if hasattr(schema, "model_fields") or hasattr(schema, "__fields__"):
            env = load(schema=schema, **kwargs)
            if verbose:
                env.status()
            return env.to_pydantic(schema)

    env = load(schema=schema, **kwargs)
    if verbose:
        env.status()
    return env


def load_with_secrets(
    provider: str,
    schema: Optional[Union[Dict[str, Any], Type[Any]]] = None,
    secret_name: Optional[str] = None,
    secret_path: Optional[str] = None,
    region: Optional[str] = None,
    vault_url: Optional[str] = None,
    vault_token: Optional[str] = None,
    scoped: bool = False,
    **kwargs: Any,
) -> Env:
    """Load environment variables from a secret manager.

    Args:
        provider: Secret manager provider ("aws" or "vault").
        schema: Optional schema or class for validation.
        secret_name: AWS Secrets Manager secret name (for AWS provider).
        secret_path: Vault secret path (for Vault provider).
        region: AWS region (for AWS provider).
        vault_url: Vault server URL (for Vault provider).
        vault_token: Vault authentication token.
        scoped: Whether to enable scoped access protection.
        **kwargs: Additional arguments.

    Returns:
        An Env object containing the validated secrets.

    Raises:
        SafeEnvError: If provider is not supported or loading fails.
        ImportError: If required dependencies are not installed.

    Examples:
        ```python
        # AWS Secrets Manager
        env = load_with_secrets(
            provider="aws",
            secret_name="prod/database",
            region="us-east-1",
            schema={"DATABASE_URL": str}
        )

        # HashiCorp Vault
        env = load_with_secrets(
            provider="vault",
            secret_path="secret/data/app",
            vault_url="https://vault.example.com",
            schema={"API_KEY": str}
        )
        ```
    """
    if load_from_secrets is None:
        raise ImportError(
            "Secret manager support requires secrets module. "
            "This should not happen in normal usage."
        )

    secrets = load_from_secrets(
        provider=provider,
        secret_name=secret_name,
        secret_path=secret_path,
        region=region,
        vault_url=vault_url,
        vault_token=vault_token,
        **kwargs,
    )

    if schema:
        required_fields: Optional[Set[str]] = None

        if isinstance(schema, type):
            if hasattr(schema, "model_fields") or hasattr(schema, "__fields__"):
                if hasattr(schema, "model_fields"):
                    schema_items = schema.model_fields
                    required_fields = {
                        k for k, v in schema_items.items() if v.is_required()
                    }
                    schema_dict = {k: v.annotation for k, v in schema_items.items()}
                else:
                    schema_items = schema.__fields__
                    required_fields = {
                        k for k, v in schema_items.items() if v.required
                    }
                    schema_dict = {k: v.type_ for k, v in schema_items.items()}
            else:
                schema_dict = {}
        else:
            schema_dict = schema if isinstance(schema, dict) else {}
            required_fields = set(schema_dict.keys()) if schema_dict else None

        final_data: Dict[str, Any] = {}

        for key, type_or_validator in schema_dict.items():
            if key not in secrets:
                if required_fields and key in required_fields:
                    raise MissingEnvError(
                        f"Missing required secret '{key}' from secret manager"
                    )
                continue

            val = secrets[key]

            try:
                if isinstance(type_or_validator, type):
                    if type_or_validator is bool:
                        val_lower = str(val).lower()
                        if val_lower in ("true", "1", "yes", "on"):
                            val = True
                        elif val_lower in ("false", "0", "no", "off"):
                            val = False
                        else:
                            raise ValueError(f"Invalid boolean value: {val}")
                    else:
                        val = type_or_validator(val)
                elif callable(type_or_validator):
                    val = type_or_validator(val)
            except (ValueError, TypeError) as e:
                type_name = (
                    type_or_validator.__name__
                    if hasattr(type_or_validator, "__name__")
                    else "type"
                )
                raise ValidationError(
                    f"{key} must be valid {type_name}: {e}"
                ) from e

            final_data[key] = val

        return Env(data=final_data, file_path=None, scoped_mode=scoped)
    else:
        return Env(data=secrets, file_path=None, scoped_mode=scoped)


def _resolve_environment_path(
    path: str,
    environment: Optional[str],
    fallback: Optional[str],
    encrypted: bool,
) -> str:
    """Resolve the actual file path based on environment parameter.

    Args:
        path: Base path to the environment file.
        environment: Environment name (e.g., "production").
        fallback: Fallback path if environment file not found.
        encrypted: Whether the file is encrypted.

    Returns:
        Resolved file path.
    """
    if not environment:
        return path

    # Determine file extension
    ext = ".enc" if encrypted else ""
    base_path = path.replace(".enc", "")

    # Try environment-specific file
    env_path = f"{base_path}.{environment}{ext}"
    if os.path.exists(env_path):
        return env_path

    # Fall back to original path or specified fallback
    fallback_path = fallback if fallback else path
    if os.path.exists(fallback_path):
        return fallback_path

    # If neither exists, return environment-specific path
    # (will be handled by FileNotFoundError in caller)
    return env_path


def _parse_env_content(content: str) -> Dict[str, str]:
    """Parse .env file content into a dictionary with variable interpolation.

    Args:
        content: Raw content of the .env file.

    Returns:
        Dictionary of key-value pairs with interpolated values.
    """
    env_vars: Dict[str, str] = {}
    lines = content.splitlines()

    # First pass: collect all variables
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]

            env_vars[key] = value

    # Second pass: interpolate variables
    return _interpolate_variables(env_vars)


def _interpolate_variables(env_vars: Dict[str, str]) -> Dict[str, str]:
    """Interpolate variable references in values.

    Supports ${VAR} and ${VAR:-default} syntax.
    Also checks os.environ for missing variables.

    Args:
        env_vars: Dictionary of environment variables.

    Returns:
        Dictionary with interpolated values.

    Raises:
        SafeEnvError: If referenced variable doesn't exist or circular reference.
    """
    import re

    result: Dict[str, str] = {}
    pattern = re.compile(r"\$\{([^}:-]+)(?::-([^}]*))?\}")
    processing: Set[str] = set()

    def resolve_value(key: str, value: str, depth: int = 0) -> str:
        """Recursively resolve variable references.

        Args:
            key: Variable name being processed.
            value: Variable value to resolve.
            depth: Recursion depth to detect circular references.

        Returns:
            Resolved value.

        Raises:
            SafeEnvError: If circular reference or variable not found.
        """
        if depth > 10:
            raise SafeEnvError(
                f"Circular reference detected or too deep nesting in '{key}'"
            )

        if not value:
            return value

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) else None

            # Detect circular reference
            if var_name == key:
                raise SafeEnvError(
                    f"Circular reference detected: '{key}' references itself"
                )

            # Check in already resolved variables
            if var_name in result:
                return result[var_name]

            # Check in original env_vars (may need further interpolation)
            if var_name in env_vars:
                if var_name in processing:
                    raise SafeEnvError(
                        f"Circular reference detected involving '{var_name}'"
                    )
                processing.add(var_name)
                resolved = resolve_value(var_name, env_vars[var_name], depth + 1)
                processing.remove(var_name)
                return resolved

            # Check in system environment
            if var_name in os.environ:
                return os.environ[var_name]

            # Use default if provided
            if default_value is not None:
                return default_value

            # Raise error if variable not found
            raise SafeEnvError(
                f"Variable '{var_name}' referenced in '{key}' but not defined"
            )

        return pattern.sub(replace_var, value)

    # Process variables in order
    for key, value in env_vars.items():
        processing.add(key)
        result[key] = resolve_value(key, value)
        processing.remove(key)

    return result


def _load_template(template_path: str) -> Dict[str, str]:
    """Load environment variable template file.

    Args:
        template_path: Path to the template file.

    Returns:
        Dictionary of template variables with their default values.

    Raises:
        SafeEnvError: If template file cannot be read.
    """
    if not os.path.exists(template_path):
        raise SafeEnvError(f"Template file not found: {template_path}")

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise SafeEnvError(f"Failed to read template file: {e}") from e

    return _parse_env_content(content)
