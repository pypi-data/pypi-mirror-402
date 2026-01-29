"""DCE API Python SDK - HTTP 请求处理."""

import json
from typing import Any, Dict, Optional, TypeVar, Type

import requests

from .config import Config
from .errors import APIError, ErrorCode, NetworkError, ValidationError
from .token import TokenManager

T = TypeVar("T")


class RequestConfig:
    """请求配置."""

    def __init__(self, trade_type: Optional[int] = None, lang: Optional[str] = None) -> None:
        """初始化请求配置.

        Args:
            trade_type: 交易类型（1=期货，2=期权）
            lang: 语言（"zh" 或 "en"）
        """
        self.trade_type = trade_type
        self.lang = lang


class BaseClient:
    """基础 HTTP 客户端."""

    def __init__(
        self,
        config: Config,
        token_manager: TokenManager,
    ) -> None:
        """初始化基础客户端.

        Args:
            config: 客户端配置
            token_manager: Token 管理器
        """
        self.config = config
        self.token_manager = token_manager
        self.session = requests.Session()

    def do_request(
        self,
        method: str,
        path: str,
        body: Optional[Any] = None,
        result_type: Optional[Type[T]] = None,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> Any:
        """执行 HTTP 请求.

        Args:
            method: HTTP 方法（GET, POST 等）
            path: API 路径
            body: 请求体（会被序列化为 JSON）
            result_type: 期望的结果类型
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            Any: 响应数据

        Raises:
            APIError: API 错误
            NetworkError: 网络错误
            ValidationError: 验证错误
        """
        req_config = RequestConfig(
            trade_type=trade_type if trade_type is not None else self.config.trade_type,
            lang=lang if lang is not None else self.config.lang,
        )

        return self._do_request_with_retry(method, path, body, result_type, req_config, False)

    def _do_request_with_retry(
        self,
        method: str,
        path: str,
        body: Optional[Any],
        result_type: Optional[Type[T]],
        req_config: RequestConfig,
        is_retry: bool,
    ) -> Any:
        """执行请求，支持 Token 过期重试.

        Args:
            method: HTTP 方法
            path: API 路径
            body: 请求体
            result_type: 期望的结果类型
            req_config: 请求配置
            is_retry: 是否为重试

        Returns:
            Any: 响应数据
        """
        # 获取 Token
        token = self.token_manager.get_token()

        # 构建请求 URL
        url = self.config.base_url + path

        # 设置请求头
        headers = self._build_headers(token, req_config)

        # 准备请求体
        json_data = None
        if body is not None:
            if hasattr(body, "__dict__"):
                # 将 dataclass 转换为 dict
                json_data = self._to_camel_case_dict(body)
            elif isinstance(body, dict):
                json_data = body
            else:
                raise ValidationError("body", "Invalid request body type")

        # 发送请求
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
                timeout=self.config.timeout,
            )
        except requests.exceptions.Timeout as e:
            raise NetworkError(e)
        except requests.exceptions.RequestException as e:
            raise NetworkError(e)

        # 处理响应
        return self._handle_response(
            response, method, path, body, result_type, req_config, is_retry
        )

    def _build_headers(self, token: str, req_config: RequestConfig) -> Dict[str, str]:
        """构建请求头.

        Args:
            token: 访问令牌
            req_config: 请求配置

        Returns:
            Dict[str, str]: 请求头字典
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "apikey": self.config.api_key,
            "tradeType": str(req_config.trade_type),
        }

        if req_config.lang:
            headers["lang"] = req_config.lang

        return headers

    def _handle_response(
        self,
        response: requests.Response,
        method: str,
        path: str,
        body: Optional[Any],
        result_type: Optional[Type[T]],
        req_config: RequestConfig,
        is_retry: bool,
    ) -> Any:
        """处理 API 响应.

        Args:
            response: HTTP 响应
            method: HTTP 方法
            path: API 路径
            body: 请求体
            result_type: 期望的结果类型
            req_config: 请求配置
            is_retry: 是否为重试

        Returns:
            Any: 响应数据
        """
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            raise APIError(500, f"Invalid JSON response: {e}")

        # 检查响应码
        if "code" in data:
            code = data.get("code")
            if code == ErrorCode.TOKEN_EXPIRED and not is_retry:
                # Token 过期，刷新并重试
                self.token_manager.refresh()
                return self._do_request_with_retry(
                    method, path, body, result_type, req_config, True
                )
            elif code != ErrorCode.SUCCESS:
                message = data.get("message", "Unknown error")
                raise APIError(code, message)

        # 提取数据
        result_data = data.get("data", data)

        # 如果没有指定结果类型，直接返回数据
        if result_type is None:
            return result_data

        # 转换为指定类型
        return self._parse_response(result_data, result_type)

    def _parse_response(self, data: Any, result_type: Type[T]) -> T:
        """解析响应数据为指定类型.

        Args:
            data: 响应数据
            result_type: 目标类型

        Returns:
            T: 解析后的数据
        """
        if data is None:
            return None  # type: ignore

        # 如果是列表类型
        if isinstance(data, list):
            return data  # type: ignore

        # 如果是 dataclass
        if hasattr(result_type, "__dataclass_fields__"):
            return self._dict_to_dataclass(data, result_type)

        return data  # type: ignore

    def _dict_to_dataclass(self, data: Dict[str, Any], cls: Type[T]) -> T:
        """将字典转换为 dataclass.

        Args:
            data: 字典数据
            cls: dataclass 类型

        Returns:
            T: dataclass 实例
        """
        if not isinstance(data, dict):
            return data  # type: ignore

        # 转换键名从 camelCase 到 snake_case
        snake_data = {}
        for key, value in data.items():
            snake_key = self._to_snake_case(key)
            snake_data[snake_key] = value

        # 创建 dataclass 实例
        try:
            return cls(**snake_data)
        except TypeError:
            # 如果字段不匹配，尝试只使用匹配的字段
            fields = {f.name for f in cls.__dataclass_fields__.values()}
            filtered_data = {k: v for k, v in snake_data.items() if k in fields}
            return cls(**filtered_data)

    def _to_snake_case(self, name: str) -> str:
        """将 camelCase 转换为 snake_case.

        Args:
            name: camelCase 字符串

        Returns:
            str: snake_case 字符串
        """
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
                result.append(char.lower())
            else:
                result.append(char.lower())
        return "".join(result)

    def _to_camel_case_dict(self, obj: Any) -> Dict[str, Any]:
        """将对象转换为 camelCase 字典.

        Args:
            obj: 对象（通常是 dataclass）

        Returns:
            Dict[str, Any]: camelCase 字典
        """
        if hasattr(obj, "__dict__"):
            data = obj.__dict__
        else:
            return obj

        result = {}
        for key, value in data.items():
            if value is not None:
                camel_key = self._to_camel_case(key)
                result[camel_key] = value
        return result

    def _to_camel_case(self, name: str) -> str:
        """将 snake_case 转换为 camelCase.

        Args:
            name: snake_case 字符串

        Returns:
            str: camelCase 字符串
        """
        components = name.split("_")
        return components[0] + "".join(x.title() for x in components[1:])
