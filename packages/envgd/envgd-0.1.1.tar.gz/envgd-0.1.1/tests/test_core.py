"""Tests for core environment loading functionality."""

import os
from pathlib import Path

import pytest

from envguard import (
    AccessError,
    EnvironmentLockError,
    load,
    MissingEnvError,
    SafeEnvError,
    TamperError,
    ValidationError,
)



def test_basic_load(tmp_path: Path) -> None:
    """Test basic environment file loading."""
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\nBAZ=123")

    env = load(path=str(env_file))
    assert env.FOO == "bar"
    assert env.BAZ == "123"


def test_schema_valid_types(tmp_path: Path) -> None:
    """Test schema validation with valid types."""
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=8080\nDEBUG=true")

    env = load(path=str(env_file), schema={"PORT": int, "DEBUG": bool})
    assert env.PORT == 8080
    assert env.DEBUG is True


def test_schema_invalid_type(tmp_path: Path) -> None:
    """Test schema validation with invalid type."""
    env_file = tmp_path / ".env"
    env_file.write_text("PORT=abc")

    with pytest.raises(ValidationError):
        load(path=str(env_file), schema={"PORT": int})


def test_missing_required_var(tmp_path: Path) -> None:
    """Test error when required variable is missing."""
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar")

    with pytest.raises(MissingEnvError):
        load(path=str(env_file), schema={"BAR": str})


def test_silent_override_prevention(
    tmp_path: Path, clean_env: None
) -> None:
    """Test prevention of silent environment variable overrides."""
    os.environ["EXISTING"] = "system_value"
    env_file = tmp_path / ".env"
    env_file.write_text("EXISTING=file_value")

    with pytest.raises(SafeEnvError, match="Override not allowed"):
        load(path=str(env_file), schema={"EXISTING": str})


def test_scoped_access(tmp_path: Path) -> None:
    """Test scoped access protection."""
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=xyz")

    env = load(path=str(env_file), scoped=True)

    # Defaults to denying access
    with pytest.raises(AccessError):
        _ = env.SECRET

    with env.scope():
        assert env.SECRET == "xyz"

    with pytest.raises(AccessError):
        _ = env.SECRET


def test_env_locking(tmp_path: Path) -> None:
    """Test environment locking functionality."""
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=production")

    env = load(path=str(env_file))

    # Should pass
    env.lock("production")

    # Should fail if environment mismatch
    env_file_dev = tmp_path / ".env.dev"
    env_file_dev.write_text("APP_ENV=development")
    env_dev = load(path=str(env_file_dev))

    with pytest.raises(EnvironmentLockError):
        env_dev.lock("production")


def test_tamper_detection(tmp_path: Path) -> None:
    """Test file tamper detection."""
    env_file = tmp_path / ".env"
    env_file.write_text("A=1")

    env = load(path=str(env_file))

    # Modify file
    env_file.write_text("A=2")

    with pytest.raises(TamperError):
        env.verify()


def test_multi_environment_support(tmp_path: Path) -> None:
    """Test multi-environment file loading."""
    base_file = tmp_path / ".env"
    base_file.write_text("APP_ENV=base\nVALUE=base_value")

    prod_file = tmp_path / ".env.production"
    prod_file.write_text("APP_ENV=production\nVALUE=prod_value")

    # Load production environment
    env = load(path=str(base_file), environment="production")
    assert env.VALUE == "prod_value"
    assert env.APP_ENV == "production"

    # Load base when production doesn't exist
    dev_file = tmp_path / ".env.development"
    dev_file.write_text("APP_ENV=development\nVALUE=dev_value")

    env_dev = load(path=str(base_file), environment="development")
    assert env_dev.VALUE == "dev_value"


def test_multi_environment_fallback(tmp_path: Path) -> None:
    """Test fallback to base file when environment file doesn't exist."""
    base_file = tmp_path / ".env"
    base_file.write_text("VALUE=base_value")

    # Should fallback to base file
    env = load(
        path=str(base_file),
        environment="staging",
        fallback=str(base_file),
    )
    assert env.VALUE == "base_value"


def test_variable_interpolation(tmp_path: Path) -> None:
    """Test variable interpolation in environment files."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BASE_URL=https://api.example.com\n"
        "API_URL=${BASE_URL}/v1\n"
        "VERSION=1.0\n"
        "FULL_URL=${API_URL}?version=${VERSION}"
    )

    env = load(path=str(env_file))
    assert env.BASE_URL == "https://api.example.com"
    assert env.API_URL == "https://api.example.com/v1"
    assert env.FULL_URL == "https://api.example.com/v1?version=1.0"


def test_variable_interpolation_with_default(tmp_path: Path) -> None:
    """Test variable interpolation with default values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "EXISTING=value\n"
        "USES_DEFAULT=${MISSING:-default_value}\n"
        "USES_EXISTING=${EXISTING:-should_not_use_this}"
    )

    env = load(path=str(env_file))
    assert env.EXISTING == "value"
    assert env.USES_DEFAULT == "default_value"
    assert env.USES_EXISTING == "value"


def test_variable_interpolation_from_system_env(tmp_path: Path, clean_env: None) -> None:
    """Test variable interpolation from system environment."""
    os.environ["SYSTEM_VAR"] = "system_value"
    env_file = tmp_path / ".env"
    env_file.write_text("LOCAL_VAR=${SYSTEM_VAR}/local")

    env = load(path=str(env_file))
    assert env.LOCAL_VAR == "system_value/local"


def test_variable_interpolation_circular_reference(tmp_path: Path) -> None:
    """Test detection of circular references."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR1=${VAR2}\nVAR2=${VAR1}")

    with pytest.raises(SafeEnvError, match="Circular reference"):
        load(path=str(env_file))


def test_variable_interpolation_self_reference(tmp_path: Path) -> None:
    """Test detection of self-referencing variables."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR=${VAR}")

    with pytest.raises(SafeEnvError, match="references itself"):
        load(path=str(env_file))


def test_variable_interpolation_missing_var(tmp_path: Path) -> None:
    """Test error when referenced variable doesn't exist."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR=${MISSING}")

    with pytest.raises(SafeEnvError, match="not defined"):
        load(path=str(env_file))


def test_template_validation(tmp_path: Path) -> None:
    """Test template validation."""
    template_file = tmp_path / ".env.template"
    template_file.write_text("DATABASE_URL=postgresql://localhost/dbname\nAPI_KEY=your-api-key")

    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://prod/db\nAPI_KEY=secret123")

    # Should pass validation
    env = load(path=str(env_file), template=str(template_file))
    assert env.DATABASE_URL == "postgresql://prod/db"
    assert env.API_KEY == "secret123"


def test_template_missing_variables(tmp_path: Path) -> None:
    """Test error when variables from template are missing."""
    template_file = tmp_path / ".env.template"
    template_file.write_text("DATABASE_URL=postgresql://localhost/dbname\nAPI_KEY=your-api-key")

    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://prod/db")

    with pytest.raises(MissingEnvError, match="Missing required variables from template"):
        load(path=str(env_file), template=str(template_file))


def test_template_with_defaults(tmp_path: Path) -> None:
    """Test using template values as defaults."""
    template_file = tmp_path / ".env.template"
    template_file.write_text("DATABASE_URL=postgresql://localhost/dbname\nAPI_KEY=default-key")

    env_file = tmp_path / ".env"
    env_file.write_text("DATABASE_URL=postgresql://prod/db")

    env = load(
        path=str(env_file),
        template=str(template_file),
        use_template_defaults=True,
    )
    assert env.DATABASE_URL == "postgresql://prod/db"
    assert env.API_KEY == "default-key"


def test_template_file_not_found(tmp_path: Path) -> None:
    """Test error when template file doesn't exist."""
    env_file = tmp_path / ".env"
    env_file.write_text("VAR=value")

    with pytest.raises(SafeEnvError, match="Template file not found"):
        load(path=str(env_file), template="nonexistent.template")
