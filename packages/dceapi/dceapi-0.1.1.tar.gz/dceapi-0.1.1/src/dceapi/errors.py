"""DCE API Python SDK - 错误类型定义."""

from enum import IntEnum
from typing import Optional


class ErrorCode(IntEnum):
    """API 错误码."""

    SUCCESS = 200
    PARAM_ERROR = 400
    NO_PERMISSION = 401
    TOKEN_EXPIRED = 402
    SERVER_ERROR = 500
    RATE_LIMIT = 501


class DCEAPIException(Exception):
    """DCE API 基础异常类."""

    pass


class APIError(DCEAPIException):
    """API 错误."""

    def __init__(self, code: int, message: str) -> None:
        """初始化 API 错误.

        Args:
            code: 错误码
            message: 错误消息
        """
        self.code = code
        self.message = message
        super().__init__(f"API error {code}: {message}")


class AuthError(DCEAPIException):
    """认证错误."""

    def __init__(self, reason: str) -> None:
        """初始化认证错误.

        Args:
            reason: 错误原因
        """
        self.reason = reason
        super().__init__(f"authentication error: {reason}")


class NetworkError(DCEAPIException):
    """网络错误."""

    def __init__(self, error: Exception) -> None:
        """初始化网络错误.

        Args:
            error: 原始错误
        """
        self.error = error
        super().__init__(f"network error: {error}")


class ValidationError(DCEAPIException):
    """验证错误."""

    def __init__(self, field: str, message: str) -> None:
        """初始化验证错误.

        Args:
            field: 字段名
            message: 错误消息
        """
        self.field = field
        self.message = message
        super().__init__(f"validation error for field '{field}': {message}")


class TokenError(DCEAPIException):
    """Token 相关错误."""

    def __init__(self, message: str) -> None:
        """初始化 Token 错误.

        Args:
            message: 错误消息
        """
        super().__init__(f"token error: {message}")
