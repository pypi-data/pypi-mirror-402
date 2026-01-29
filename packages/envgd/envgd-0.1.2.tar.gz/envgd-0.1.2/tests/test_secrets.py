"""Tests for secret manager integrations."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from envguard import MissingEnvError, SafeEnvError, load_with_secrets


def test_aws_secrets_manager_missing_boto3():
    """Test error when boto3 is not installed."""
    with patch("envguard.secrets.boto3", None):
        with pytest.raises(ImportError, match="boto3 is required"):
            load_with_secrets(provider="aws", secret_name="test/secret")


def test_aws_secrets_manager_success():
    """Test successful loading from AWS Secrets Manager."""
    mock_secret = {
        "DATABASE_URL": "postgresql://localhost/db",
        "API_KEY": "secret-key-123",
    }

    mock_response = {"SecretString": '{"DATABASE_URL": "postgresql://localhost/db", "API_KEY": "secret-key-123"}'}

    with patch("envguard.secrets.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = mock_response
        mock_boto3.client.return_value = mock_client

        env = load_with_secrets(
            provider="aws",
            secret_name="prod/database",
            region="us-east-1",
            schema={"DATABASE_URL": str, "API_KEY": str},
        )

        assert env.DATABASE_URL == "postgresql://localhost/db"
        assert env.API_KEY == "secret-key-123"
        mock_client.get_secret_value.assert_called_once_with(SecretId="prod/database")


def test_aws_secrets_manager_not_found():
    """Test error when secret is not found."""
    from botocore.exceptions import ClientError

    error_response = {"Error": {"Code": "ResourceNotFoundException"}}
    mock_error = ClientError(error_response, "GetSecretValue")

    with patch("envguard.secrets.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = mock_error
        mock_boto3.client.return_value = mock_client

        with pytest.raises(SafeEnvError, match="not found"):
            load_with_secrets(provider="aws", secret_name="nonexistent")


def test_aws_secrets_manager_access_denied():
    """Test error when access is denied."""
    from botocore.exceptions import ClientError

    error_response = {"Error": {"Code": "AccessDeniedException"}}
    mock_error = ClientError(error_response, "GetSecretValue")

    with patch("envguard.secrets.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_client.get_secret_value.side_effect = mock_error
        mock_boto3.client.return_value = mock_client

        with pytest.raises(SafeEnvError, match="Access denied"):
            load_with_secrets(provider="aws", secret_name="restricted")


def test_vault_missing_hvac():
    """Test error when hvac is not installed."""
    with patch("envguard.secrets.hvac", None):
        with pytest.raises(ImportError, match="hvac is required"):
            load_with_secrets(provider="vault", secret_path="secret/data/app")


def test_vault_success():
    """Test successful loading from HashiCorp Vault."""
    mock_data = {
        "data": {
            "data": {
                "DATABASE_URL": "postgresql://localhost/db",
                "API_KEY": "secret-key-123",
            }
        }
    }

    with patch("envguard.secrets.hvac") as mock_hvac:
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_data
        mock_hvac.Client.return_value = mock_client

        env = load_with_secrets(
            provider="vault",
            secret_path="secret/data/app",
            vault_url="https://vault.example.com",
            vault_token="test-token",
            schema={"DATABASE_URL": str, "API_KEY": str},
        )

        assert env.DATABASE_URL == "postgresql://localhost/db"
        assert env.API_KEY == "secret-key-123"


def test_vault_not_found():
    """Test error when secret path is not found."""
    import hvac

    with patch("envguard.secrets.hvac") as mock_hvac:
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = (
            hvac.exceptions.InvalidPath()
        )
        mock_hvac.Client.return_value = mock_client

        with pytest.raises(SafeEnvError, match="not found"):
            load_with_secrets(
                provider="vault",
                secret_path="nonexistent/path",
                vault_url="https://vault.example.com",
                vault_token="test-token",
            )


def test_vault_access_denied():
    """Test error when access is denied."""
    import hvac

    with patch("envguard.secrets.hvac") as mock_hvac:
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.side_effect = (
            hvac.exceptions.Forbidden()
        )
        mock_hvac.Client.return_value = mock_client

        with pytest.raises(SafeEnvError, match="Access denied"):
            load_with_secrets(
                provider="vault",
                secret_path="restricted/path",
                vault_url="https://vault.example.com",
                vault_token="invalid-token",
            )


def test_unsupported_provider():
    """Test error when provider is not supported."""
    with pytest.raises(SafeEnvError, match="Unsupported secret manager provider"):
        load_with_secrets(provider="unsupported", secret_name="test")


def test_secrets_with_schema_validation():
    """Test schema validation with secrets."""
    mock_response = {"SecretString": '{"PORT": "8080", "DEBUG": "true"}'}

    with patch("envguard.secrets.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = mock_response
        mock_boto3.client.return_value = mock_client

        env = load_with_secrets(
            provider="aws",
            secret_name="app/config",
            schema={"PORT": int, "DEBUG": bool},
        )

        assert env.PORT == 8080
        assert env.DEBUG is True


def test_secrets_missing_required_field():
    """Test error when required field is missing from secrets."""
    mock_response = {"SecretString": '{"PORT": "8080"}'}

    with patch("envguard.secrets.boto3") as mock_boto3:
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = mock_response
        mock_boto3.client.return_value = mock_client

        with pytest.raises(MissingEnvError, match="Missing required secret"):
            load_with_secrets(
                provider="aws",
                secret_name="app/config",
                schema={"PORT": int, "API_KEY": str},
            )
