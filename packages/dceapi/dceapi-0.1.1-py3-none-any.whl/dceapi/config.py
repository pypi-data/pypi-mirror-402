"""DCE API Python SDK - 配置管理."""

import os
from dataclasses import dataclass, field
from typing import Optional

from .errors import ValidationError

# 常量定义
DEFAULT_BASE_URL = "http://www.dce.com.cn"
DEFAULT_TIMEOUT = 30.0
DEFAULT_LANG = "zh"
DEFAULT_TRADE_TYPE = 1

# 环境变量名
ENV_API_KEY = "DCE_API_KEY"
ENV_SECRET = "DCE_SECRET"


@dataclass
class Config:
    """客户端配置.

    Attributes:
        api_key: API Key (必需)
        secret: API Secret (必需)
        base_url: API 基础 URL，默认 "http://www.dce.com.cn"
        timeout: HTTP 超时时间（秒），默认 30.0
        lang: 语言，"zh" 或 "en"，默认 "zh"
        trade_type: 交易类型，1=期货，2=期权，默认 1
    """

    api_key: str
    secret: str
    base_url: str = DEFAULT_BASE_URL
    timeout: float = DEFAULT_TIMEOUT
    lang: str = DEFAULT_LANG
    trade_type: int = DEFAULT_TRADE_TYPE

    def __post_init__(self) -> None:
        """初始化后验证配置."""
        self.validate()

    def validate(self) -> None:
        """验证配置是否有效.

        Raises:
            ValidationError: 当配置无效时
        """
        if not self.api_key:
            raise ValidationError("api_key", "API key is required")
        if not self.secret:
            raise ValidationError("secret", "secret is required")
        if self.lang not in ("zh", "en"):
            raise ValidationError("lang", "lang must be 'zh' or 'en'")
        if self.trade_type not in (1, 2):
            raise ValidationError("trade_type", "trade_type must be 1 (futures) or 2 (options)")
        if self.timeout <= 0:
            raise ValidationError("timeout", "timeout must be positive")

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量创建配置.

        从 DCE_API_KEY 和 DCE_SECRET 环境变量读取凭证。

        Returns:
            Config: 配置实例

        Raises:
            ValidationError: 当必需的环境变量未设置时
        """
        api_key = os.getenv(ENV_API_KEY, "")
        secret = os.getenv(ENV_SECRET, "")

        if not api_key:
            raise ValidationError(
                ENV_API_KEY, f"Environment variable {ENV_API_KEY} is not set"
            )
        if not secret:
            raise ValidationError(
                ENV_SECRET, f"Environment variable {ENV_SECRET} is not set"
            )

        return cls(api_key=api_key, secret=secret)
