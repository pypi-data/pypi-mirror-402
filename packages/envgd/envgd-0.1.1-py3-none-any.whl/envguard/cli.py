"""Command-line interface for EnvGuard encryption/decryption tools."""

import argparse
import os
import sys
import time
from typing import Optional

from cryptography.fernet import Fernet

from .crypto import decrypt_to_file, encrypt_file

def encrypt_command(args: argparse.Namespace) -> None:
    """Encrypt the environment file, print key, optionally delete original.

    Args:
        args: Parsed command-line arguments.
    """
    env_file = args.file

    if not os.path.exists(env_file):
        print(f"Error: {env_file} not found.")
        return

    key: Optional[str] = args.key
    if not key:
        existing_key = os.environ.get("SAFEENV_KEY")
        if existing_key:
            confirm = input(
                "Found existing SAFEENV_KEY in your environment. "
                "Reuse it? (y/N): "
            ).lower()
            if confirm == "y":
                key = existing_key
                print("Reusing existing key...")
            else:
                key = None

    if not key:
        print("\nKey Management")
        print("[1] Generate a new encryption key")
        print("[2] Use an existing key")
        choice = input("Select an option (default 1): ").strip()

        if choice == "2":
            key = input("Enter encryption key: ").strip()
            if not key:
                print("Error: No key entered. Exiting.")
                sys.exit(1)
        else:
            key = Fernet.generate_key().decode()

    print(f"Loading {env_file} for encryption...")

    try:
        enc_path = encrypt_file(env_file, key=key)
    except Exception as e:
        print(f"Error: Encryption failed: {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("ENCRYPTION SUCCESSFUL")
    print("=" * 60)
    print(
        "Store the following key securely. "
        "It is required for decryption."
    )
    print(f"\n{key}\n")
    print("=" * 60)

    if not args.keep:
        print(
            f"\nScheduled deletion of {env_file} in 5 seconds "
            "(Ctrl+C to cancel)"
        )
        try:
            for i in range(5, 0, -1):
                print(f"{i}...", end=" ", flush=True)
                time.sleep(1)
            print("\n")

            os.remove(env_file)
            print(f"File {env_file} removed.")
        except KeyboardInterrupt:
            print("\nDeletion cancelled by user.")
    else:
        print(f"Original {env_file} kept (as requested).")

    print(f"Encrypted file saved at: {enc_path}")

def decrypt_command(args: argparse.Namespace) -> None:
    """Decrypt an encrypted file back to plain text.

    Args:
        args: Parsed command-line arguments.
    """
    enc_file = args.file
    key: Optional[str] = args.key

    if not key:
        key = os.environ.get("SAFEENV_KEY")
        if not key:
            key = input("Enter your decryption key: ").strip()
            if not key:
                print("Error: Decryption key is required.")
                return

    if not os.path.exists(enc_file):
        print(f"Error: {enc_file} not found.")
        return

    print(f"Decrypting {enc_file}...")

    try:
        out_path = decrypt_to_file(enc_file, key=key)
        print(f"Success! File restored to: {out_path}")
    except Exception as e:
        print(f"Error: Decryption failed: {e}")
        sys.exit(1)

def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="EnvGuard CLI Tool")
    subparsers = parser.add_subparsers(
        dest="command", help="Command to run"
    )

    encrypt_parser = subparsers.add_parser(
        "encrypt", help="Encrypt an environment file"
    )
    encrypt_parser.add_argument(
        "file",
        nargs="?",
        default=".env",
        help="Path to the environment file (default: .env)",
    )
    encrypt_parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the plain text file after encryption",
    )
    encrypt_parser.add_argument(
        "--key", help="Reuse an existing encryption key"
    )

    decrypt_parser = subparsers.add_parser(
        "decrypt", help="Decrypt an environment file"
    )
    decrypt_parser.add_argument(
        "file", help="Path to the encrypted file (e.g., .env.enc)"
    )
    decrypt_parser.add_argument(
        "--key",
        "-k",
        help="The encryption key (will prompt if not provided)",
    )

    args = parser.parse_args()

    if args.command == "encrypt":
        encrypt_command(args)
    elif args.command == "decrypt":
        decrypt_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
