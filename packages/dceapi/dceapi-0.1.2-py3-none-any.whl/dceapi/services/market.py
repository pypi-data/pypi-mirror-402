"""DCE API Python SDK - 行情服务."""

from typing import TYPE_CHECKING, List, Optional, Union

from ..errors import ValidationError
from ..models import (
    ContractMonthMaxOpeni,
    ContractMonthMaxPrice,
    ContractMonthMaxRequest,
    ContractMonthMaxTurnover,
    ContractMonthMaxVolume,
    DivisionPriceInfo,
    DivisionPriceInfoRequest,
    Quote,
    QuotesRequest,
    RiseFallEvent,
    RiseFallEventRequest,
    VarietyMonthYearStat,
    VarietyMonthYearStatRequest,
)

if TYPE_CHECKING:
    from ..http import BaseClient

# API 端点
PATH_GET_NIGHT_QUOTES = "/dceapi/forward/publicweb/dailystat/tiNightQuotes"
PATH_GET_DAY_QUOTES = "/dceapi/forward/publicweb/dailystat/dayQuotes"
PATH_GET_WEEK_QUOTES = "/dceapi/forward/publicweb/dailystat/weekQuotes"
PATH_GET_MONTH_QUOTES = "/dceapi/forward/publicweb/dailystat/monthQuotes"
PATH_GET_CONTRACT_MONTH_MAX = "/dceapi/forward/publicweb/phasestat/contractMonthMax"
PATH_GET_VARIETY_MONTH_YEAR_STAT = "/dceapi/forward/publicweb/phasestat/varietyMonthYearStat"
PATH_GET_RISE_FALL_EVENT = "/dceapi/forward/publicweb/phasestat/riseFallEvent"
PATH_GET_DIVISION_PRICE_INFO = "/dceapi/forward/publicweb/dailystat/divisionPriceInfo"


class MarketService:
    """行情服务."""

    def __init__(self, client: "BaseClient") -> None:
        """初始化行情服务.

        Args:
            client: HTTP 客户端
        """
        self.client = client

    def get_night_quotes(
        self,
        request: QuotesRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[Quote]:
        """获取夜盘行情.

        Args:
            request: 行情请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[Quote]: 行情数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_NIGHT_QUOTES,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        # 转换为 Quote 对象列表
        return self._parse_quotes(result)

    def get_day_quotes(
        self,
        request: QuotesRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[Quote]:
        """获取日行情.

        Args:
            request: 行情请求参数
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[Quote]: 行情数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DAY_QUOTES,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_quotes(result)

    def get_week_quotes(
        self,
        request: QuotesRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[Quote]:
        """获取周行情.

        Args:
            request: 行情请求参数（与日行情使用相同参数结构）
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[Quote]: 行情数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_WEEK_QUOTES,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_quotes(result)

    def get_month_quotes(
        self,
        request: QuotesRequest,
        trade_type: Optional[int] = None,
        lang: Optional[str] = None,
    ) -> List[Quote]:
        """获取月行情.

        Args:
            request: 行情请求参数（与日行情使用相同参数结构）
            trade_type: 交易类型（覆盖配置）
            lang: 语言（覆盖配置）

        Returns:
            List[Quote]: 行情数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
            NetworkError: 网络错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_MONTH_QUOTES,
            body=request,
            result_type=list,
            trade_type=trade_type,
            lang=lang,
        )

        return self._parse_quotes(result)

    def get_contract_month_max(
        self,
        request: ContractMonthMaxRequest,
    ) -> List[Union[ContractMonthMaxVolume, ContractMonthMaxTurnover,
                    ContractMonthMaxOpeni, ContractMonthMaxPrice]]:
        """获取合约最值统计.

        根据 stat_content 参数返回不同类型的统计数据:
        - 0: 成交量统计 -> ContractMonthMaxVolume
        - 1: 成交额统计 -> ContractMonthMaxTurnover
        - 2: 持仓量统计 -> ContractMonthMaxOpeni
        - 3: 价格统计 -> ContractMonthMaxPrice

        Args:
            request: 合约最值统计请求

        Returns:
            统计数据列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_CONTRACT_MONTH_MAX,
            body=request,
            result_type=list,
        )

        return self._parse_contract_month_max(result, request.stat_content)

    def _parse_contract_month_max(
        self, data: List, stat_content: str
    ) -> List[Union[ContractMonthMaxVolume, ContractMonthMaxTurnover,
                    ContractMonthMaxOpeni, ContractMonthMaxPrice]]:
        """解析合约最值统计数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if not isinstance(item, dict):
                continue

            if stat_content == "0":  # 成交量
                result.append(ContractMonthMaxVolume(
                    contract_id=item.get("contractId", ""),
                    sum_amount=int(item.get("sumAmount", 0)),
                    max_amount=int(item.get("maxAmount", 0)),
                    max_amount_date=item.get("maxAmountDate", ""),
                    min_amount=int(item.get("minAmount", 0)),
                    min_amount_date=item.get("minAmountDate", ""),
                    avg_amount=int(item.get("avgAmount", 0)),
                ))
            elif stat_content == "1":  # 成交额
                result.append(ContractMonthMaxTurnover(
                    contract_id=item.get("contractId", ""),
                    sum_turnover=item.get("sumTurnover", ""),
                    max_turnover=item.get("maxTurnover", ""),
                    max_turnover_date=item.get("maxTurnoverDate", ""),
                    min_turnover=item.get("minTurnover", ""),
                    min_turnover_date=item.get("minTurnoverDate", ""),
                    avg_turnover=item.get("avgTurnover", ""),
                ))
            elif stat_content == "2":  # 持仓量
                result.append(ContractMonthMaxOpeni(
                    contract_id=item.get("contractId", ""),
                    sum_openi=int(item.get("sumOpeni", 0)),
                    max_openi=int(item.get("maxOpeni", 0)),
                    max_openi_date=item.get("maxOpeniDate", ""),
                    min_openi=int(item.get("minOpeni", 0)),
                    min_openi_date=item.get("minOpeniDate", ""),
                    avg_openi=int(item.get("avgOpeni", 0)),
                ))
            elif stat_content == "3":  # 价格统计
                result.append(ContractMonthMaxPrice(
                    contract_id=item.get("contractId", ""),
                    open=item.get("open", ""),
                    close=item.get("close", ""),
                    high=item.get("high", ""),
                    high_date=item.get("highDate", ""),
                    low=item.get("low", ""),
                    low_date=item.get("lowDate", ""),
                    clear_price=item.get("clearPrice", ""),
                ))
        return result

    def get_variety_month_year_stat(
        self,
        request: VarietyMonthYearStatRequest,
    ) -> List[VarietyMonthYearStat]:
        """获取品种月度统计.

        Args:
            request: 品种月度统计请求

        Returns:
            List[VarietyMonthYearStat]: 品种月度统计列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_VARIETY_MONTH_YEAR_STAT,
            body=request,
            result_type=list,
        )

        return self._parse_variety_month_year_stat(result)

    def _parse_variety_month_year_stat(
        self, data: List
    ) -> List[VarietyMonthYearStat]:
        """解析品种月度统计数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(VarietyMonthYearStat(
                    variety=item.get("variety", ""),
                    this_month_volumn=int(item.get("thisMonthVolumn", 0)),
                    volumn_balance=item.get("volumnBalance", ""),
                    volumn_chain=item.get("volumnChain", ""),
                    this_year_volumn=int(item.get("thisYearVolumn", 0)),
                    year_volumn_chain=item.get("yearVolumnChain", ""),
                    this_month_turnover=item.get("thisMonthTurnover", ""),
                    turnover_balance=item.get("turnoverBalance", ""),
                    turnover_chain=item.get("turnoverChain", ""),
                    this_year_turnover=item.get("thisYearTurnover", ""),
                    year_turnover_chain=item.get("yearTurnoverChain", ""),
                    this_month_openi=int(item.get("thisMonthOpeni", 0)),
                    openi_balance=item.get("openiBalance", ""),
                    openi_chain=item.get("openiChain", ""),
                ))
        return result

    def get_rise_fall_event(
        self,
        request: RiseFallEventRequest,
    ) -> List[RiseFallEvent]:
        """获取合约停板查询.

        Args:
            request: 合约停板查询请求

        Returns:
            List[RiseFallEvent]: 停板事件列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_RISE_FALL_EVENT,
            body=request,
            result_type=list,
        )

        return self._parse_rise_fall_event(result)

    def _parse_rise_fall_event(self, data: List) -> List[RiseFallEvent]:
        """解析合约停板数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(RiseFallEvent(
                    trade_date=item.get("tradeDate", ""),
                    contract_id=item.get("contractId", ""),
                    direction=item.get("direction", ""),
                    times=int(item.get("times", 0)),
                ))
        return result

    def get_division_price_info(
        self,
        request: DivisionPriceInfoRequest,
    ) -> List[DivisionPriceInfo]:
        """获取分时结算参考价.

        Args:
            request: 分时结算参考价请求

        Returns:
            List[DivisionPriceInfo]: 分时结算参考价列表

        Raises:
            ValidationError: 参数验证错误
            APIError: API 错误
        """
        if request is None:
            raise ValidationError("request", "request is required")

        result = self.client.do_request(
            method="POST",
            path=PATH_GET_DIVISION_PRICE_INFO,
            body=request,
            result_type=list,
        )

        return self._parse_division_price_info(result)

    def _parse_division_price_info(self, data: List) -> List[DivisionPriceInfo]:
        """解析分时结算参考价数据."""
        if not isinstance(data, list):
            return []

        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(DivisionPriceInfo(
                    calculate_date=item.get("calculateDate", ""),
                    calculate_time=item.get("calculateTime", ""),
                    variety_name=item.get("varietyName", ""),
                    variety_en_name=item.get("varietyEnName", ""),
                    contract_id=item.get("contractId", ""),
                    clear_price=int(item.get("clearPrice", 0)),
                    series_id=item.get("seriesId"),
                    volatility=item.get("volatility"),
                ))
        return result

    def _parse_quotes(self, data: List) -> List[Quote]:
        """解析行情数据.

        Args:
            data: 原始数据列表

        Returns:
            List[Quote]: Quote 对象列表
        """
        if not isinstance(data, list):
            return []

        quotes = []
        for item in data:
            if isinstance(item, dict):
                quote = Quote(
                    variety=item.get("variety", ""),
                    contract_id=item.get("contractId", ""),
                    deliv_month=item.get("delivMonth"),
                    open=item.get("open"),
                    high=item.get("high"),
                    low=item.get("low"),
                    close=item.get("close"),
                    last_clear=item.get("lastClear"),
                    last_price=item.get("lastPrice"),
                    clear_price=item.get("clearPrice"),
                    diff=item.get("diff"),
                    diff1=item.get("diff1"),
                    volume=item.get("volumn", item.get("volume")),  # 兼容 API 拼写错误 (volumn) 和正确拼写
                    open_interest=item.get("openInterest"),
                    diff_i=item.get("diffI"),
                    turnover=item.get("turnover"),
                    # 新增字段
                    variety_order=item.get("varietyOrder"),
                    delta=item.get("delta"),
                    match_qty_sum=item.get("matchQtySum"),
                    diff_t=item.get("diffT"),
                    diff_v=item.get("diffV"),
                    volumn_rate=item.get("volumnRate"),
                    open_interest_rate=item.get("openInterestRate"),
                    period_over_period_chg=item.get("periodOverPeriodChg"),
                    implied_volatility=item.get("impliedVolatility"),
                    series_id=item.get("seriesId"),
                    avg_open_interest=item.get("avgOpenInterest"),
                    year_total_volume=item.get("yearTotalVolume"),
                    year_avg_open_interest=item.get("yearAvgOpenInterest"),
                    year_turnover=item.get("yearTurnover"),
                    year_match_qty_sum=item.get("yearMatchQtySum"),
                    quote_key=item.get("quoteKey"),
                    # 夜盘行情特有字段
                    declare_price=item.get("declarePrice"),
                    variety_en=item.get("varietyEn"),
                    turnover_en=item.get("turnoverEn"),
                )
                quotes.append(quote)
        return quotes
