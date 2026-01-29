"""Pytest configuration."""

import pytest


@pytest.fixture
def mock_api_key():
    """Mock API key."""
    return "test_api_key"


@pytest.fixture
def mock_secret():
    """Mock secret."""
    return "test_secret"


@pytest.fixture
def mock_config(mock_api_key, mock_secret):
    """Mock configuration."""
    from dceapi import Config
    return Config(api_key=mock_api_key, secret=mock_secret)
