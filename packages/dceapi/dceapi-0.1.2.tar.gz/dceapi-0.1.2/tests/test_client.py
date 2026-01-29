"""Tests for client module."""

import pytest

from dceapi import Client, Config
from dceapi.errors import ValidationError


def test_client_creation():
    """测试客户端创建."""
    config = Config(api_key="test_key", secret="test_secret")
    client = Client(config)
    
    assert client.config.api_key == "test_key"
    assert client.config.secret == "test_secret"
    assert client.common is not None
    assert client.news is not None
    assert client.market is not None


def test_client_from_env(monkeypatch):
    """测试从环境变量创建客户端."""
    monkeypatch.setenv("DCE_API_KEY", "env_key")
    monkeypatch.setenv("DCE_SECRET", "env_secret")
    
    client = Client.from_env()
    assert client.config.api_key == "env_key"
    assert client.config.secret == "env_secret"


def test_client_get_config():
    """测试获取配置副本."""
    config = Config(api_key="test_key", secret="test_secret")
    client = Client(config)
    
    config_copy = client.get_config()
    assert config_copy.api_key == "test_key"
    assert config_copy.secret == "test_secret"
    
    # 修改副本不应影响原始配置
    config_copy.timeout = 60.0
    assert client.config.timeout == 30.0
