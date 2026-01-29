"""Tests for config module."""

import os
import pytest

from dceapi.config import Config
from dceapi.errors import ValidationError


def test_config_validation():
    """测试配置验证."""
    # 有效配置
    config = Config(api_key="test_key", secret="test_secret")
    assert config.api_key == "test_key"
    assert config.secret == "test_secret"
    
    # 无效配置 - 缺少 api_key
    with pytest.raises(ValidationError) as exc_info:
        Config(api_key="", secret="test_secret")
    assert "api_key" in str(exc_info.value)
    
    # 无效配置 - 缺少 secret
    with pytest.raises(ValidationError) as exc_info:
        Config(api_key="test_key", secret="")
    assert "secret" in str(exc_info.value)


def test_config_defaults():
    """测试配置默认值."""
    config = Config(api_key="test_key", secret="test_secret")
    
    assert config.base_url == "http://www.dce.com.cn"
    assert config.timeout == 30.0
    assert config.lang == "zh"
    assert config.trade_type == 1


def test_config_from_env(monkeypatch):
    """测试从环境变量创建配置."""
    # 设置环境变量
    monkeypatch.setenv("DCE_API_KEY", "env_key")
    monkeypatch.setenv("DCE_SECRET", "env_secret")
    
    config = Config.from_env()
    assert config.api_key == "env_key"
    assert config.secret == "env_secret"


def test_config_from_env_missing(monkeypatch):
    """测试缺少环境变量时的行为."""
    # 清除环境变量
    monkeypatch.delenv("DCE_API_KEY", raising=False)
    monkeypatch.delenv("DCE_SECRET", raising=False)
    
    with pytest.raises(ValidationError):
        Config.from_env()
