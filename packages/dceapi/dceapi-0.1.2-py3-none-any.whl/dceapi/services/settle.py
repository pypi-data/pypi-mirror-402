"""DCE API Python SDK - 结算服务."""

from typing import TYPE_CHECKING, List, Optional

from ..errors import ValidationError
from ..models import SettleParam, SettleParamRequest

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_SETTLE_PARAM = "/dceapi/forward/publicweb/tradepara/futAndOptSettle"


class SettleService:
    """结算服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化结算服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_settle_param(
        self,
        request: SettleParamRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[SettleParam]:
        """获取结算参数.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[SettleParam]: 结算参数列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_SETTLE_PARAM,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_settle_params(result)

    def _parse_settle_params(self, data: List) -> List[SettleParam]:
        """解析结算参数数据.

        Args:
            data: 原始数据列表

        Returns:
            List[SettleParam]: SettleParam 对象列表
        """
        if not isinstance(data, list):
            return []

        params = []
        for item in data:
            if isinstance(item, dict):
                param = SettleParam(
                    variety=item.get("variety", ""),
                    variety_order=item.get("varietyOrder", ""),
                    contract_id=item.get("contractId", ""),
                    clear_price=item.get("clearPrice", ""),
                    open_fee=item.get("openFee", ""),
                    offset_fee=item.get("offsetFee", ""),
                    short_open_fee=item.get("shortOpenFee", ""),
                    short_offset_fee=item.get("shortOffsetFee", ""),
                    style=item.get("style", ""),
                    spec_buy_rate=item.get("specBuyRate", ""),
                    spec_sell_rate=item.get("specSellRate", ""),
                    hedge_buy_rate=item.get("hedgeBuyRate", ""),
                    hedge_sell_rate=item.get("hedgeSellRate", ""),
                    # 新增套保手续费字段
                    hedge_open_fee=item.get("hedgeOpenFee"),
                    hedge_offset_fee=item.get("hedgeOffsetFee"),
                    hedge_short_open_fee=item.get("hedgeShortOpenFee"),
                    hedge_short_offset_fee=item.get("hedgeShortOffsetFee"),
                )
                params.append(param)
        return params
