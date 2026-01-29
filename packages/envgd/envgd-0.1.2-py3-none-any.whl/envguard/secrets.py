"""Secret manager integrations for EnvGuard."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .exceptions import SafeEnvError


def load_from_secrets(
    provider: str,
    secret_name: Optional[str] = None,
    secret_path: Optional[str] = None,
    region: Optional[str] = None,
    vault_url: Optional[str] = None,
    vault_token: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, str]:
    """Load secrets from a secret manager.

    Args:
        provider: Secret manager provider ("aws" or "vault").
        secret_name: AWS Secrets Manager secret name (for AWS provider).
        secret_path: Vault secret path (for Vault provider).
        region: AWS region (for AWS provider). Defaults to AWS_DEFAULT_REGION.
        vault_url: Vault server URL (for Vault provider).
        vault_token: Vault authentication token. Defaults to VAULT_TOKEN env var.
        **kwargs: Additional provider-specific arguments.

    Returns:
        Dictionary of secret key-value pairs.

    Raises:
        SafeEnvError: If provider is not supported or loading fails.
        ImportError: If required dependencies are not installed.
    """
    if provider.lower() == "aws":
        return _load_from_aws_secrets_manager(
            secret_name=secret_name or kwargs.get("secret_name"),
            region=region or kwargs.get("region"),
        )
    elif provider.lower() in ("vault", "hashicorp-vault"):
        return _load_from_vault(
            secret_path=secret_path or kwargs.get("secret_path"),
            vault_url=vault_url or kwargs.get("vault_url"),
            vault_token=vault_token or kwargs.get("vault_token"),
        )
    else:
        raise SafeEnvError(
            f"Unsupported secret manager provider: {provider}. "
            "Supported providers: 'aws', 'vault'"
        )


def _load_from_aws_secrets_manager(
    secret_name: Optional[str] = None,
    region: Optional[str] = None,
) -> Dict[str, str]:
    """Load secrets from AWS Secrets Manager.

    Args:
        secret_name: Name of the secret in AWS Secrets Manager.
        region: AWS region. Defaults to AWS_DEFAULT_REGION environment variable.

    Returns:
        Dictionary of secret key-value pairs.

    Raises:
        ImportError: If boto3 is not installed.
        SafeEnvError: If secret cannot be retrieved.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        raise ImportError(
            "boto3 is required for AWS Secrets Manager support. "
            "Install with 'pip install envguard[aws]' or 'pip install boto3'"
        )

    if not secret_name:
        raise SafeEnvError("secret_name is required for AWS Secrets Manager")

    region = region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ResourceNotFoundException":
            raise SafeEnvError(f"Secret '{secret_name}' not found in AWS Secrets Manager")
        elif error_code == "AccessDeniedException":
            raise SafeEnvError(
                f"Access denied to secret '{secret_name}'. "
                "Check your AWS credentials and permissions."
            )
        else:
            raise SafeEnvError(f"Failed to retrieve secret from AWS: {e}") from e
    except Exception as e:
        raise SafeEnvError(f"Failed to connect to AWS Secrets Manager: {e}") from e

    secret_string = response.get("SecretString", "")
    if not secret_string:
        raise SafeEnvError(f"Secret '{secret_name}' is empty")

    # Parse JSON secret
    try:
        import json

        secret_data = json.loads(secret_string)
        if isinstance(secret_data, dict):
            return {str(k): str(v) for k, v in secret_data.items()}
        else:
            raise SafeEnvError(
                f"Secret '{secret_name}' must contain a JSON object, "
                f"got {type(secret_data).__name__}"
            )
    except json.JSONDecodeError:
        # If not JSON, treat as plain text (single key-value pair)
        return {"SECRET": secret_string}


def _load_from_vault(
    secret_path: Optional[str] = None,
    vault_url: Optional[str] = None,
    vault_token: Optional[str] = None,
) -> Dict[str, str]:
    """Load secrets from HashiCorp Vault.

    Args:
        secret_path: Path to the secret in Vault (e.g., "secret/data/app").
        vault_url: Vault server URL. Defaults to VAULT_ADDR environment variable.
        vault_token: Vault authentication token. Defaults to VAULT_TOKEN env var.

    Returns:
        Dictionary of secret key-value pairs.

    Raises:
        ImportError: If hvac is not installed.
        SafeEnvError: If secret cannot be retrieved.
    """
    try:
        import hvac
    except ImportError:
        raise ImportError(
            "hvac is required for HashiCorp Vault support. "
            "Install with 'pip install envguard[vault]' or 'pip install hvac'"
        )

    if not secret_path:
        raise SafeEnvError("secret_path is required for HashiCorp Vault")

    vault_url = vault_url or os.environ.get("VAULT_ADDR")
    if not vault_url:
        raise SafeEnvError(
            "vault_url is required. Provide it as argument or set VAULT_ADDR "
            "environment variable"
        )

    vault_token = vault_token or os.environ.get("VAULT_TOKEN")
    if not vault_token:
        raise SafeEnvError(
            "vault_token is required. Provide it as argument or set VAULT_TOKEN "
            "environment variable"
        )

    try:
        client = hvac.Client(url=vault_url, token=vault_token)
        if not client.is_authenticated():
            raise SafeEnvError("Failed to authenticate with Vault. Check your token.")

        response = client.secrets.kv.v2.read_secret_version(path=secret_path)
    except hvac.exceptions.InvalidPath:
        raise SafeEnvError(f"Secret path '{secret_path}' not found in Vault")
    except hvac.exceptions.Forbidden:
        raise SafeEnvError(
            f"Access denied to secret path '{secret_path}'. "
            "Check your Vault token permissions."
        )
    except Exception as e:
        raise SafeEnvError(f"Failed to retrieve secret from Vault: {e}") from e

    # Extract data from Vault response
    try:
        data = response.get("data", {}).get("data", {})
        if not data:
            raise SafeEnvError(f"Secret path '{secret_path}' contains no data")

        return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        raise SafeEnvError(f"Failed to parse Vault response: {e}") from e
