"""DCE API Python SDK - 会员服务."""

from typing import TYPE_CHECKING, Dict, List, Optional

from ..errors import ValidationError
from ..models import (
    DailyRankingRequest,
    DailyRankingResponse,
    PhaseRanking,
    PhaseRankingRequest,
    Ranking,
)

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_DAILY_RANKING = "/dceapi/forward/publicweb/dailystat/memberDealPosi"
PATH_GET_PHASE_RANKING = "/dceapi/forward/publicweb/phasestat/memberDealCh"


class MemberService:
    """会员服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化会员服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_daily_ranking(
        self,
        request: DailyRankingRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> DailyRankingResponse:
        """获取日交易排名.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            DailyRankingResponse: 日排名响应

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DAILY_RANKING,
            body=request,
            result_type=dict,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_daily_ranking(result)

    def _parse_daily_ranking(self, data: Dict) -> DailyRankingResponse:
        """解析日排名数据.

        Args:
            data: 原始数据字典

        Returns:
            DailyRankingResponse: 日排名响应对象
        """
        if not isinstance(data, dict):
            return DailyRankingResponse(
                contract_id="",
                today_qty=0,
                qty_sub=0,
                today_buy_qty=0,
                buy_sub=0,
                today_sell_qty=0,
                sell_sub=0,
                qty_future_list=[],
                buy_future_list=[],
                sell_future_list=[],
            )

        def parse_ranking_list(items: List) -> List[Ranking]:
            """解析排名列表."""
            rankings = []
            for item in items:
                if isinstance(item, dict):
                    ranking = Ranking(
                        rank=str(item.get("rank", "")),
                        qty_abbr=item.get("qtyAbbr", ""),
                        today_qty=int(item.get("todayQty", 0)),
                        qty_sub=int(item.get("qtySub", 0)),
                        buy_abbr=item.get("buyAbbr", ""),
                        today_buy_qty=int(item.get("todayBuyQty", 0)),
                        buy_sub=int(item.get("buySub", 0)),
                        sell_abbr=item.get("sellAbbr", ""),
                        today_sell_qty=int(item.get("todaySellQty", 0)),
                        sell_sub=int(item.get("sellSub", 0)),
                    )
                    rankings.append(ranking)
            return rankings

        return DailyRankingResponse(
            contract_id=data.get("contractId", ""),
            today_qty=int(data.get("todayQty", 0)),
            qty_sub=int(data.get("qtySub", 0)),
            today_buy_qty=int(data.get("todayBuyQty", 0)),
            buy_sub=int(data.get("buySub", 0)),
            today_sell_qty=int(data.get("todaySellQty", 0)),
            sell_sub=int(data.get("sellSub", 0)),
            qty_future_list=parse_ranking_list(data.get("qtyFutureList", [])),
            buy_future_list=parse_ranking_list(data.get("buyFutureList", [])),
            sell_future_list=parse_ranking_list(data.get("sellFutureList", [])),
            # 新增字段 - 期权排名列表
            qty_option_up_list=parse_ranking_list(data.get("qtyOptionUpList", []))
            if data.get("qtyOptionUpList")
            else None,
            buy_option_up_list=parse_ranking_list(data.get("buyOptionUpList", []))
            if data.get("buyOptionUpList")
            else None,
            sell_option_up_list=parse_ranking_list(data.get("sellOptionUpList", []))
            if data.get("sellOptionUpList")
            else None,
            qty_option_down_list=parse_ranking_list(data.get("qtyOptionDownList", []))
            if data.get("qtyOptionDownList")
            else None,
            buy_option_down_list=parse_ranking_list(data.get("buyOptionDownList", []))
            if data.get("buyOptionDownList")
            else None,
            sell_option_down_list=parse_ranking_list(
                data.get("sellOptionDownList", [])
            )
            if data.get("sellOptionDownList")
            else None,
        )

    def get_phase_ranking(
        self,
        request: PhaseRankingRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[PhaseRanking]:
        """获取阶段交易排名.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[PhaseRanking]: 阶段排名列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_PHASE_RANKING,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_phase_ranking(result)

    def _parse_phase_ranking(self, data: List) -> List[PhaseRanking]:
        """解析阶段排名数据.

        Args:
            data: 原始数据列表

        Returns:
            List[PhaseRanking]: PhaseRanking 对象列表
        """
        if not isinstance(data, list):
            return []

        rankings = []
        for item in data:
            if isinstance(item, dict):
                ranking = PhaseRanking(
                    seq=item.get("seq", ""),
                    member_id=item.get("memberId", ""),
                    member_name=item.get("memberName", ""),
                    month_qty=float(item.get("monthQty", 0)),
                    qty_ratio=float(item.get("qtyRatio", 0)),
                    month_amt=float(item.get("monthAmt", 0)),
                    amt_ratio=float(item.get("amtRatio", 0)),
                    # 新增字段
                    amt_member_id=item.get("amtMemberId"),
                    amt_member_name=item.get("amtMemberName"),
                )
                rankings.append(ranking)
        return rankings
