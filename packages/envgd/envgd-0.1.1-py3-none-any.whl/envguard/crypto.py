"""Cryptographic utilities for file encryption and hashing."""

import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet

from .exceptions import SafeEnvError


def calculate_hash_sum(content: bytes) -> str:
    """Calculate the SHA-256 hash of the given bytes.

    Args:
        content: Bytes to hash.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(content).hexdigest()


def calculate_file_hash(path: str) -> str:
    """Calculate the SHA-256 hash of a file's content.

    Args:
        path: Path to the file.

    Returns:
        Hexadecimal hash string, or empty string if file doesn't exist.
    """
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return calculate_hash_sum(f.read())

def decrypt_file(path: str, key: Optional[str] = None) -> str:
    """Decrypt an AES-encrypted file and return its content as a string.

    Args:
        path: Path to the encrypted file.
        key: AES encryption key (Fernet). If None, checks SAFEENV_KEY
            environment variable.

    Returns:
        Decrypted file content as a string.

    Raises:
        SafeEnvError: If key is missing or decryption fails.
        FileNotFoundError: If the encrypted file doesn't exist.
    """
    if not key:
        key = os.environ.get("SAFEENV_KEY")
        if not key:
            raise SafeEnvError(
                "SAFEENV_KEY environment variable required for decryption."
            )

    if not os.path.exists(path):
        raise FileNotFoundError(f"Encrypted file {path} not found.")

    with open(path, "rb") as f:
        encrypted_data = f.read()

    cipher = Fernet(key.encode() if isinstance(key, str) else key)
    try:
        decrypted_data = cipher.decrypt(encrypted_data)
        return decrypted_data.decode("utf-8")
    except Exception as e:
        raise SafeEnvError(f"Decryption failed: {e}") from e

def decrypt_to_file(
    path: str, key: str, out_path: Optional[str] = None
) -> str:
    """Decrypt an encrypted file and save the result to a plain text file.

    Args:
        path: Path to the encrypted file.
        key: AES encryption key.
        out_path: Optional output path. If None, auto-generates based on
            input path.

    Returns:
        Path to the decrypted file.

    Raises:
        SafeEnvError: If decryption fails.
        FileNotFoundError: If the encrypted file doesn't exist.
    """
    content = decrypt_file(path, key=key)

    if not out_path:
        if path.endswith(".enc"):
            out_path = path[:-4]
        else:
            out_path = path + ".dec"

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    return out_path


def encrypt_file(path: str, key: Optional[str] = None) -> str:
    """Encrypt a file and save it with a '.enc' extension.

    Args:
        path: Path to the plain text file.
        key: Optional AES key. If None, a new key is generated.

    Returns:
        The path to the newly created encrypted file.

    Raises:
        FileNotFoundError: If the input file doesn't exist.
    """
    if not key:
        key_bytes = Fernet.generate_key()
        key = key_bytes.decode()
    else:
        key_bytes = key.encode() if isinstance(key, str) else key

    with open(path, "rb") as f:
        data = f.read()

    cipher = Fernet(key_bytes)
    encrypted_data = cipher.encrypt(data)

    new_path = path + ".enc"
    with open(new_path, "wb") as f:
        f.write(encrypted_data)

    return new_path
