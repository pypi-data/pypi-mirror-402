"""Pytest configuration and fixtures."""

import os
from typing import Generator

import pytest


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Ensure clean environment for tests.

    Yields:
        None
    """
    old_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(old_env)
