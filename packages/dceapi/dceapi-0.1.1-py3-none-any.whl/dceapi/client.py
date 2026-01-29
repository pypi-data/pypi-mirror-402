"""DCE API Python SDK - 客户端入口."""

from typing import Optional

from .config import Config
from .http import BaseClient
from .services import (
    CommonService,
    DeliveryService,
    MarketService,
    MemberService,
    NewsService,
    SettleService,
    TradeService,
)
from .token import TokenManager


class Client:
    """DCE API 客户端.

    提供访问大连商品交易所 API 的统一入口。

    Attributes:
        common: 通用服务
        news: 资讯服务
        market: 行情服务
        trade: 交易服务
        settle: 结算服务
        member: 会员服务
        delivery: 交割服务
    """

    def __init__(self, config: Config) -> None:
        """初始化客户端.

        Args:
            config: 客户端配置

        Raises:
            ValidationError: 当配置无效时
        """
        self.config = config

        # 创建 Token 管理器
        self.token_manager = TokenManager(
            api_key=config.api_key,
            secret=config.secret,
            base_url=config.base_url,
            timeout=config.timeout,
        )

        # 创建基础 HTTP 客户端
        self._base_client = BaseClient(config, self.token_manager)

        # 初始化所有服务
        self.common = CommonService(self._base_client)
        self.news = NewsService(self._base_client)
        self.market = MarketService(self._base_client)
        self.trade = TradeService(self._base_client)
        self.settle = SettleService(self._base_client)
        self.member = MemberService(self._base_client)
        self.delivery = DeliveryService(self._base_client)

    @classmethod
    def from_env(cls) -> "Client":
        """从环境变量创建客户端.

        从 DCE_API_KEY 和 DCE_SECRET 环境变量读取凭证。

        Returns:
            Client: 客户端实例

        Raises:
            ValidationError: 当必需的环境变量未设置时

        Example:
            >>> client = Client.from_env()
            >>> trade_date = client.common.get_curr_trade_date()
        """
        config = Config.from_env()
        return cls(config)

    def get_config(self) -> Config:
        """获取客户端配置（只读副本）.

        Returns:
            Config: 配置副本
        """
        return Config(
            api_key=self.config.api_key,
            secret=self.config.secret,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            lang=self.config.lang,
            trade_type=self.config.trade_type,
        )

    def refresh_token(self) -> None:
        """强制刷新访问令牌.

        通常不需要手动调用，Token 管理器会自动处理刷新。

        Raises:
            AuthError: 认证失败时
            NetworkError: 网络错误时
        """
        self.token_manager.refresh()

    def clear_token(self) -> None:
        """清除缓存的访问令牌.

        下次请求时将重新获取 Token。
        """
        self.token_manager.clear()
