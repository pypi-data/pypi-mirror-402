"""DCE API Python SDK - Token 管理."""

import json
import threading
import time
from typing import Optional

import requests

from .errors import AuthError, NetworkError, TokenError

# 常量定义
TOKEN_EXPIRY_SECONDS = 3600
TOKEN_EXPIRY_BUFFER = 60
AUTH_ENDPOINT = "/dceapi/cms/auth/accessToken"


class TokenManager:
    """Token 管理器.

    自动管理 access token 的获取和刷新。
    线程安全，支持多线程并发使用。
    """

    def __init__(
        self,
        api_key: str,
        secret: str,
        base_url: str,
        timeout: float = 30.0,
    ) -> None:
        """初始化 Token 管理器.

        Args:
            api_key: API Key
            secret: API Secret
            base_url: API 基础 URL
            timeout: HTTP 超时时间（秒）
        """
        self.api_key = api_key
        self.secret = secret
        self.base_url = base_url
        self.timeout = timeout

        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = threading.RLock()

    def get_token(self) -> str:
        """获取有效的访问令牌.

        如果令牌不存在或已过期，将自动获取新令牌。

        Returns:
            str: 有效的访问令牌

        Raises:
            AuthError: 认证失败时
            NetworkError: 网络错误时
        """
        with self._lock:
            # 检查 token 是否有效
            if self._token and not self._is_expired():
                return self._token

            # 需要刷新 token
            self._refresh()
            if not self._token:
                raise TokenError("Failed to obtain token")
            return self._token

    def refresh(self) -> None:
        """强制刷新令牌.

        Raises:
            AuthError: 认证失败时
            NetworkError: 网络错误时
        """
        with self._lock:
            self._refresh()

    def _is_expired(self) -> bool:
        """检查 token 是否已过期（包含缓冲时间）.

        Returns:
            bool: True 如果已过期
        """
        # 提前 TOKEN_EXPIRY_BUFFER 秒认为过期
        return time.time() >= (self._expires_at - TOKEN_EXPIRY_BUFFER)

    def _refresh(self) -> None:
        """刷新令牌（内部方法，需持有锁）.

        Raises:
            AuthError: 认证失败时
            NetworkError: 网络错误时
        """
        url = self.base_url + AUTH_ENDPOINT

        # 构建认证请求体（只包含 secret）
        auth_data = {
            "secret": self.secret,
        }

        # 构建请求头（apikey 在头部）
        headers = {
            "Content-Type": "application/json",
            "apikey": self.api_key,
        }

        try:
            response = requests.post(
                url,
                json=auth_data,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise NetworkError(e)
        except requests.exceptions.RequestException as e:
            raise NetworkError(e)

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise AuthError(f"Invalid JSON response: {e}")

        # 检查响应
        if "code" in data:
            code = data.get("code")
            if code != 200:
                message = data.get("message", "Unknown error")
                raise AuthError(f"Authentication failed (code {code}): {message}")

            # 解析 token 数据
            token_data = data.get("data", {})
            if isinstance(token_data, dict):
                access_token = token_data.get("token")
                expires_in = token_data.get("expiresIn", TOKEN_EXPIRY_SECONDS)
            else:
                raise AuthError("Invalid token response format")
        else:
            # 直接返回 token 的格式
            access_token = data.get("token")
            expires_in = data.get("expiresIn", TOKEN_EXPIRY_SECONDS)

        if not access_token:
            raise AuthError("No access token in response")

        # 更新 token 和过期时间
        self._token = access_token
        self._expires_at = time.time() + expires_in

    def clear(self) -> None:
        """清除缓存的令牌."""
        with self._lock:
            self._token = None
            self._expires_at = 0
