"""DCE API Python SDK - 通用服务."""

from typing import TYPE_CHECKING, List, Optional

from ..models import TradeDate, Variety

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_CURR_TRADE_DATE = "/dceapi/forward/publicweb/maxTradeDate"
PATH_GET_VARIETY_LIST = "/dceapi/forward/publicweb/variety"


class CommonService:
    """通用服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化通用服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_curr_trade_date(
        self, trade_type: Optional[int] = None, lang: Optional[str] = None
    ) -> TradeDate:
        """获取当前交易日期.

        Args:
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            TradeDate: 交易日期

        Raises:
            APIError: API 错误
            NetworkError: 网络错误
        """
        result = self.client.do_request(
            method="GET",
            path=PATH_GET_CURR_TRADE_DATE,
            result_type=TradeDate,
            trade_type=trade_type,
            lang=lang,
        )
        return result

    def get_variety_list(
        self, trade_type: Optional[int] = None, lang: Optional[str] = None
    ) -> List[Variety]:
        """获取品种列表.

        Args:
            trade_type: 交易类型（1=期货，2=期权）
            lang: 语言（覆盖配置）

        Returns:
            List[Variety]: 品种列表

        Raises:
            APIError: API 错误
            NetworkError: 网络错误
        """
        result = self.client.do_request(
            method="GET",
            path=PATH_GET_VARIETY_LIST,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        # 将结果转换为 Variety 对象列表
        if isinstance(result, list):
            varieties = []
            for item in result:
                if isinstance(item, dict):
                    variety = Variety(
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        variety_english_name=item.get("varietyEnglishName", ""),
                        pic=item.get("pic", ""),
                        variety_type=item.get("varietyType", ""),
                        quot_type=item.get("quotType"),
                    )
                    varieties.append(variety)
            return varieties

        return []
