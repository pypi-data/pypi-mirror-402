"""DCE API Python SDK.

大连商品交易所 (DCE) API v1.0 Python SDK

基本使用:
    >>> from dceapi import Client
    >>> client = Client.from_env()
    >>> trade_date = client.common.get_curr_trade_date()
    >>> print(f"当前交易日期: {trade_date.date}")
"""

__version__ = "0.1.0"

from .client import Client
from .config import Config
from .errors import (
    APIError,
    AuthError,
    DCEAPIException,
    ErrorCode,
    NetworkError,
    TokenError,
    ValidationError,
)
from .models import (
    ArbitrageContract,
    Article,
    # 新增 - 交割统计
    BondedDelivery,
    BondedDeliveryRequest,
    ContractInfo,
    ContractInfoRequest,
    # 新增 - 行情统计
    ContractMonthMaxOpeni,
    ContractMonthMaxPrice,
    ContractMonthMaxRequest,
    ContractMonthMaxTurnover,
    ContractMonthMaxVolume,
    DailyRankingRequest,
    DailyRankingResponse,
    DayTradeParamRequest,
    DeliveryCost,
    DeliveryData,
    DeliveryDataRequest,
    DeliveryMatch,
    DeliveryMatchRequest,
    # 新增 - 行情统计
    DivisionPriceInfo,
    DivisionPriceInfoRequest,
    # 新增 - 交割统计
    FactorySpotAgioQuote,
    GetArticleByPageRequest,
    GetArticleByPageResponse,
    # 新增 - 交易参数
    MainSeriesInfo,
    MainSeriesInfoRequest,
    MarginArbiPerfPara,
    MonthTradeParamItem,
    MonthTradeParamResponse,
    # 新增 - 交易参数
    NewContractInfo,
    NewContractInfoRequest,
    PhaseRanking,
    PhaseRankingRequest,
    # 新增 - 交割统计
    PlywoodDeliveryCommodity,
    Quote,
    QuotesRequest,
    Ranking,
    # 新增 - 行情统计
    RiseFallEvent,
    RiseFallEventRequest,
    # 新增 - 交割统计
    RollDeliverySellerIntention,
    RollDeliverySellerIntentionRequest,
    SettleParam,
    SettleParamRequest,
    # 新增 - 交割统计
    TcCongregateDelivery,
    TcCongregateDeliveryRequest,
    TradeDate,
    TradeParam,
    # 新增 - 交易参数
    TradingParam,
    TradingParamRequest,
    Variety,
    # 新增 - 行情统计
    VarietyMonthYearStat,
    VarietyMonthYearStatRequest,
    WarehousePremium,
    WarehousePremiumResponse,
    WarehouseReceipt,
    WarehouseReceiptRequest,
    WarehouseReceiptResponse,
)

__all__ = [
    # 版本
    "__version__",
    # 客户端
    "Client",
    "Config",
    # 错误
    "DCEAPIException",
    "APIError",
    "AuthError",
    "NetworkError",
    "ValidationError",
    "TokenError",
    "ErrorCode",
    # 通用模型
    "TradeDate",
    "Variety",
    # 资讯模型
    "Article",
    "GetArticleByPageRequest",
    "GetArticleByPageResponse",
    # 行情模型
    "Quote",
    "QuotesRequest",
    # 行情统计新增
    "ContractMonthMaxRequest",
    "ContractMonthMaxVolume",
    "ContractMonthMaxTurnover",
    "ContractMonthMaxOpeni",
    "ContractMonthMaxPrice",
    "VarietyMonthYearStatRequest",
    "VarietyMonthYearStat",
    "RiseFallEventRequest",
    "RiseFallEvent",
    "DivisionPriceInfoRequest",
    "DivisionPriceInfo",
    # 交易模型
    "TradeParam",
    "DayTradeParamRequest",
    "ContractInfo",
    "ContractInfoRequest",
    "ArbitrageContract",
    # 交易参数新增
    "MonthTradeParamItem",
    "MonthTradeParamResponse",
    "TradingParamRequest",
    "TradingParam",
    "MarginArbiPerfPara",
    "NewContractInfoRequest",
    "NewContractInfo",
    "MainSeriesInfoRequest",
    "MainSeriesInfo",
    # 结算模型
    "SettleParam",
    "SettleParamRequest",
    # 会员模型
    "Ranking",
    "DailyRankingRequest",
    "DailyRankingResponse",
    "PhaseRanking",
    "PhaseRankingRequest",
    # 交割模型
    "DeliveryData",
    "DeliveryDataRequest",
    "DeliveryMatch",
    "DeliveryMatchRequest",
    "WarehouseReceipt",
    "WarehouseReceiptRequest",
    "WarehouseReceiptResponse",
    "DeliveryCost",
    "WarehousePremium",
    "WarehousePremiumResponse",
    # 交割统计新增
    "TcCongregateDeliveryRequest",
    "TcCongregateDelivery",
    "RollDeliverySellerIntentionRequest",
    "RollDeliverySellerIntention",
    "BondedDeliveryRequest",
    "BondedDelivery",
    "PlywoodDeliveryCommodity",
    "FactorySpotAgioQuote",
]
