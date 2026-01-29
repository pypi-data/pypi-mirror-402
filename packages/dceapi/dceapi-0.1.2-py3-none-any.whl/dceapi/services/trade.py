"""DCE API Python SDK - 交易服务."""

from typing import TYPE_CHECKING, List, Optional

from ..errors import ValidationError
from ..models import (
    ArbitrageContract,
    ArbitrageContractRequest,
    ContractInfo,
    ContractInfoRequest,
    DayTradeParamRequest,
    MainSeriesInfo,
    MainSeriesInfoRequest,
    MarginArbiPerfPara,
    MonthTradeParamItem,
    MonthTradeParamResponse,
    NewContractInfo,
    NewContractInfoRequest,
    TradeParam,
    TradingParam,
    TradingParamRequest,
)

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_DAY_TRADE_PARAM = "/dceapi/forward/publicweb/tradepara/dayTradPara"
PATH_GET_MONTH_TRADE_PARAM = "/dceapi/forward/publicweb/tradepara/monthTradPara"
PATH_GET_CONTRACT_INFO = "/dceapi/forward/publicweb/tradepara/contractInfo"
PATH_GET_ARBITRAGE_CONTRACT = "/dceapi/forward/publicweb/tradepara/arbitrageContract"
PATH_GET_TRADING_PARAM = "/dceapi/forward/publicweb/tradepara/tradingParam"
PATH_GET_MARGIN_ARBI_PERF_PARA = "/dceapi/forward/publicweb/tradepara/marginArbiPerfPara"
PATH_GET_NEW_CONTRACT_INFO = "/dceapi/forward/publicweb/tradepara/newContractInfo"
PATH_GET_MAIN_SERIES_INFO = "/dceapi/forward/publicweb/tradepara/mainSeriesInfo"


class TradeService:
    """交易服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化交易服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_day_trade_param(
        self,
        request: DayTradeParamRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[TradeParam]:
        """获取日交易参数.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[TradeParam]: 交易参数列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DAY_TRADE_PARAM,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_trade_params(result)

    def _parse_trade_params(self, data: List) -> List[TradeParam]:
        """解析交易参数数据.

        Args:
            data: 原始数据列表

        Returns:
            List[TradeParam]: TradeParam 对象列表
        """
        if not isinstance(data, list):
            return []

        params = []
        for item in data:
            if isinstance(item, dict):
                param = TradeParam(
                    contract_id=item.get("contractId", ""),
                    spec_buy_rate=float(item.get("specBuyRate", 0)),
                    spec_buy=float(item.get("specBuy", 0)),
                    hedge_buy_rate=float(item.get("hedgeBuyRate", 0)),
                    hedge_buy=float(item.get("hedgeBuy", 0)),
                    rise_limit_rate=float(item.get("riseLimitRate", 0)),
                    rise_limit=float(item.get("riseLimit", 0)),
                    fall_limit=float(item.get("fallLimit", 0)),
                    trade_date=item.get("tradeDate", ""),
                    # 新增字段
                    style=item.get("style"),
                    self_tot_buy_posi_quota=item.get("selfTotBuyPosiQuota"),
                    self_tot_buy_posi_quota_ser_limit=item.get(
                        "selfTotBuyPosiQuotaSerLimit"
                    ),
                    client_buy_posi_quota=item.get("clientBuyPosiQuota"),
                    client_buy_posi_quota_ser_limit=item.get(
                        "clientBuyPosiQuotaSerLimit"
                    ),
                    contract_limit=item.get("contractLimit"),
                    variety_limit=item.get("varietyLimit"),
                )
                params.append(param)
        return params

    def get_contract_info(
        self,
        request: ContractInfoRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[ContractInfo]:
        """获取合约信息.

        Args:
            request: 请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[ContractInfo]: 合约信息列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_CONTRACT_INFO,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_contract_info(result)

    def _parse_contract_info(self, data: List) -> List[ContractInfo]:
        """解析合约信息数据.

        Args:
            data: 原始数据列表

        Returns:
            List[ContractInfo]: ContractInfo 对象列表
        """
        if not isinstance(data, list):
            return []

        contracts = []
        for item in data:
            if isinstance(item, dict):
                contract = ContractInfo(
                    contract_id=item.get("contractId", ""),
                    variety=item.get("variety", ""),
                    variety_order=item.get("varietyOrder", ""),
                    unit=int(item.get("unit", 0)),
                    tick=item.get("tick", ""),
                    start_trade_date=item.get("startTradeDate", ""),
                    end_trade_date=item.get("endTradeDate", ""),
                    end_delivery_date=item.get("endDeliveryDate", ""),
                    trade_type=item.get("tradeType", ""),
                )
                contracts.append(contract)
        return contracts

    def get_arbitrage_contract(
        self,
        lang: str = "zh",
        trade_type: Optional[int] = None,
    ) -> List[ArbitrageContract]:
        """获取套利合约.

        Args:
            lang: 语言（"zh" 或 "en"）
            trade_type: 交易类型（覆盖配置）

        Returns:
            List[ArbitrageContract]: 套利合约列表

        Raises:
            APIError: API 错误
            NetworkError: 网络错误
        """
        req = ArbitrageContractRequest(lang=lang if lang else "zh")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_ARBITRAGE_CONTRACT,
            body=req,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_arbitrage_contracts(result)

    def _parse_arbitrage_contracts(self, data: List) -> List[ArbitrageContract]:
        """解析套利合约数据.

        Args:
            data: 原始数据列表

        Returns:
            List[ArbitrageContract]: ArbitrageContract 对象列表
        """
        if not isinstance(data, list):
            return []

        contracts = []
        for item in data:
            if isinstance(item, dict):
                contract = ArbitrageContract(
                    arbi_name=item.get("arbiName", ""),
                    variety_name=item.get("varietyName", ""),
                    arbi_contract_id=item.get("arbiContractId", ""),
                    max_hand=int(item.get("maxHand", 0)),
                    tick=float(item.get("tick", 0)),
                )
                contracts.append(contract)
        return contracts

    def get_month_trade_param(self) -> MonthTradeParamResponse:
        """获取月交易参数.

        Returns:
            MonthTradeParamResponse: 月交易参数响应

        Raises:
            APIError: API 错误
        """
        result = self.client.do_request(
            method="POST",
            path=PATH_GET_MONTH_TRADE_PARAM,
            body={},
            result_type=dict,
        )

        return self._parse_month_trade_param(result)

    def _parse_month_trade_param(self, data: dict) -> MonthTradeParamResponse:
        """解析月交易参数数据."""
        if not isinstance(data, dict):
            return MonthTradeParamResponse(
                month_date="",
                first_date="",
                tenth_date="",
                fifteenth_date="",
                list=[],
            )

        items = []
        for item in data.get("list", []):
            if isinstance(item, dict):
                items.append(
                    MonthTradeParamItem(
                        variety_id=item.get("varietyId", ""),
                        contract_id=item.get("contractId", ""),
                        first_rate=float(item.get("firstRate", 0)),
                        fifteenth_rate=float(item.get("fifteenthRate", 0)),
                        first_rate_hedge=float(item.get("firstRateHedge", 0)),
                        fifteenth_rate_hedge=float(item.get("fifteenthRateHedge", 0)),
                        delivery_rise_limit=float(item.get("deliveryRiseLimit", 0)),
                        first_self_quota=item.get("firstSelfQuota", ""),
                        first_client_quota=item.get("firstClientQuota", ""),
                        tenth_self_quota=item.get("tenthSelfQuota", ""),
                        tenth_client_quota=item.get("tenthClientQuota", ""),
                    )
                )

        return MonthTradeParamResponse(
            month_date=data.get("monthDate", ""),
            first_date=data.get("firstDate", ""),
            tenth_date=data.get("tenthDate", ""),
            fifteenth_date=data.get("fifteenthDate", ""),
            list=items,
        )

    def get_trading_param(
        self,
        request: Optional[TradingParamRequest] = None,
    ) -> List[TradingParam]:
        """获取交易参数表（品种）.

        Args:
            request: 请求参数

        Returns:
            List[TradingParam]: 交易参数列表

        Raises:
            APIError: API 错误
        """
        req = request or TradingParamRequest(lang="zh")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_TRADING_PARAM,
            body=req,
            result_type=list,
        )

        return self._parse_trading_param(result)

    def _parse_trading_param(self, data: List) -> List[TradingParam]:
        """解析交易参数表数据."""
        if not isinstance(data, list):
            return []

        params = []
        for item in data:
            if isinstance(item, dict):
                params.append(
                    TradingParam(
                        variety_id=item.get("varietyId", ""),
                        variety_name=item.get("varietyName", ""),
                        trading_margin_rate_speculation=item.get(
                            "tradingMarginRateSpeculation", ""
                        ),
                        trading_margin_rate_hedging=item.get(
                            "tradingMarginRateHedging", ""
                        ),
                        price_limit_existing_contract=item.get(
                            "priceLimitExistingContract", ""
                        ),
                        price_limit_new_contract=item.get("priceLimitNewContract", ""),
                        price_limit_delivery_month=item.get(
                            "priceLimitDeliveryMonth", ""
                        ),
                        trading_margin_rate_speculation_n=item.get(
                            "tradingMarginRateSpeculationN"
                        ),
                        trading_margin_rate_hedging_n=item.get(
                            "tradingMarginRateHedgingN"
                        ),
                        settlement_margin_rate_hedging_n=item.get(
                            "settlementMarginRateHedgingN"
                        ),
                        price_limit_n=item.get("priceLimitN"),
                        trading_margin_rate_n1=item.get("tradingMarginRateN1"),
                        settlement_margin_rate_hedging_n1=item.get(
                            "settlementMarginRateHedgingN1"
                        ),
                        price_limit_n1=item.get("priceLimitN1"),
                        trading_margin_rate_n2=item.get("tradingMarginRateN2"),
                        price_limit_n2=item.get("priceLimitN2"),
                        trading_limit=item.get("tradingLimit"),
                        spec_open_fee=item.get("specOpenFee"),
                        spec_offset_fee=item.get("specOffsetFee"),
                        spec_short_open_fee=item.get("specShortOpenFee"),
                        spec_short_offset_fee=item.get("specShortOffsetFee"),
                        hedge_open_fee=item.get("hedgeOpenFee"),
                        hedge_offset_fee=item.get("hedgeOffsetFee"),
                        hedge_short_open_fee=item.get("hedgeShortOpenFee"),
                        hedge_short_offset_fee=item.get("hedgeShortOffsetFee"),
                        fee_style=item.get("feeStyle"),
                        fee_style_en=item.get("feeStyleEn"),
                        delivery_fee=item.get("deliveryFee"),
                        max_hand=item.get("maxHand"),
                    )
                )
        return params

    def get_margin_arbi_perf_para(
        self,
        lang: str = "zh",
    ) -> List[MarginArbiPerfPara]:
        """获取套利交易保证金.

        Args:
            lang: 语言（"zh" 或 "en"）

        Returns:
            List[MarginArbiPerfPara]: 套利交易保证金列表

        Raises:
            APIError: API 错误
        """
        result = self.client.do_request(
            method="POST",
            path=PATH_GET_MARGIN_ARBI_PERF_PARA,
            body={"lang": lang},
            result_type=list,
        )

        return self._parse_margin_arbi_perf_para(result)

    def _parse_margin_arbi_perf_para(self, data: List) -> List[MarginArbiPerfPara]:
        """解析套利交易保证金数据."""
        if not isinstance(data, list):
            return []

        params = []
        for item in data:
            if isinstance(item, dict):
                params.append(
                    MarginArbiPerfPara(
                        arbi_name=item.get("arbiName", ""),
                        variety_name=item.get("varietyName", ""),
                        arbi_contract_id=item.get("arbiContractId", ""),
                        perf_sh_type=item.get("perfShType", ""),
                        margin_amt=float(item.get("marginAmt", 0)),
                    )
                )
        return params

    def get_new_contract_info(
        self,
        request: NewContractInfoRequest,
    ) -> List[NewContractInfo]:
        """获取期货/期权合约增挂信息.

        Args:
            request: 请求参数

        Returns:
            List[NewContractInfo]: 新增合约信息列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_NEW_CONTRACT_INFO,
            body=request,
            result_type=list,
        )

        return self._parse_new_contract_info(result)

    def _parse_new_contract_info(self, data: List) -> List[NewContractInfo]:
        """解析新增合约信息数据."""
        if not isinstance(data, list):
            return []

        contracts = []
        for item in data:
            if isinstance(item, dict):
                contracts.append(
                    NewContractInfo(
                        trade_type=item.get("tradeType", ""),
                        variety=item.get("variety", ""),
                        variety_order=item.get("varietyOrder", ""),
                        contract_id=item.get("contractId", ""),
                        start_trade_date=item.get("startTradeDate", ""),
                        ref_price_unit=item.get("refPriceUnit", ""),
                        no_rise_limit=item.get("noRiseLimit"),
                        no_fall_limit=item.get("noFallLimit"),
                    )
                )
        return contracts

    def get_main_series_info(
        self,
        request: MainSeriesInfoRequest,
    ) -> List[MainSeriesInfo]:
        """获取做市商持续报价合约.

        Args:
            request: 请求参数

        Returns:
            List[MainSeriesInfo]: 做市商持续报价合约列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_MAIN_SERIES_INFO,
            body=request,
            result_type=list,
        )

        return self._parse_main_series_info(result)

    def _parse_main_series_info(self, data: List) -> List[MainSeriesInfo]:
        """解析做市商持续报价合约数据."""
        if not isinstance(data, list):
            return []

        series = []
        for item in data:
            if isinstance(item, dict):
                series.append(
                    MainSeriesInfo(
                        trade_date=item.get("tradeDate", ""),
                        variety_id=item.get("varietyId", ""),
                        series_id=item.get("seriesId", ""),
                        contract_id=item.get("contractId", ""),
                    )
                )
        return series
