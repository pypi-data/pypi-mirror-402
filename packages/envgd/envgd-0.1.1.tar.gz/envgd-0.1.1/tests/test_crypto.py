"""Tests for cryptographic functionality."""

import os
from pathlib import Path

import pytest

from envguard import SafeEnvError, load
from envguard.crypto import decrypt_file, encrypt_file

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


@pytest.mark.skipif(Fernet is None, reason="cryptography not installed")
def test_encryption_flow(tmp_path: Path, clean_env: None) -> None:
    """Test complete encryption and decryption flow."""
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=my_precious")

    key = Fernet.generate_key().decode()
    os.environ["SAFEENV_KEY"] = key

    # Encrypt
    enc_path = encrypt_file(str(env_file), key=key)
    assert os.path.exists(enc_path)
    assert enc_path.endswith(".enc")

    # Check it's not plain text
    with open(enc_path, "rb") as f:
        content = f.read()
        assert b"my_precious" not in content

    # Load encrypted
    env = load(path=enc_path, encrypted=True)
    assert env.SECRET == "my_precious"


@pytest.mark.skipif(Fernet is None, reason="cryptography not installed")
def test_missing_key(tmp_path: Path, clean_env: None) -> None:
    """Test error when decryption key is missing."""
    env_file = tmp_path / ".env"
    env_file.write_text("A=1")

    # We need a key to encrypt first
    key = Fernet.generate_key().decode()
    enc_path = encrypt_file(str(env_file), key=key)

    # Ensure no key in env
    if "SAFEENV_KEY" in os.environ:
        del os.environ["SAFEENV_KEY"]

    with pytest.raises(SafeEnvError):
        load(path=enc_path, encrypted=True)
