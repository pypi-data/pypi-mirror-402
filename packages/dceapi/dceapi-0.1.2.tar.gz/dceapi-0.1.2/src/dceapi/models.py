"""DCE API Python SDK - 数据模型."""

from dataclasses import dataclass
from typing import List, Optional


# ============================================================================
# 通用响应模型
# ============================================================================


@dataclass
class APIResponse:
    """API 通用响应."""

    code: int
    message: str
    data: Optional[dict] = None


@dataclass
class TokenResponse:
    """认证响应."""

    token_type: str  # Bearer
    access_token: str  # 访问令牌
    expires_in: int  # 过期时间（秒）


# ============================================================================
# 资讯数据模型
# ============================================================================


@dataclass
class Article:
    """文章."""

    id: str
    title: str
    sub_title: str
    summary: str
    show_date: str
    create_date: str
    content: str
    keywords: str
    page_name: str
    # API 文档新增字段
    version: Optional[str] = None
    source_id: Optional[str] = None
    release_date: Optional[str] = None
    entity_type: Optional[str] = None
    title_image_url: Optional[str] = None
    article_static_url: Optional[str] = None
    article_dynamic_url: Optional[str] = None



@dataclass
class GetArticleByPageRequest:
    """分页获取文章请求."""

    column_id: str
    page_no: int
    page_size: int
    site_id: int = 5


@dataclass
class GetArticleByPageResponse:
    """分页获取文章响应."""

    column_id: str
    total_count: int
    result_list: List[Article]
    # API 文档新增字段
    status: Optional[str] = None
    status_info: Optional[str] = None


# ============================================================================
# 通用数据模型
# ============================================================================


@dataclass
class TradeDate:
    """交易日期."""

    trade_date: str  # 对应 API 的 tradeDate 字段


@dataclass
class Variety:
    """品种."""

    variety_id: str  # 对应 API 的 varietyId
    variety_name: str  # 对应 API 的 varietyName
    variety_english_name: str  # 对应 API 的 varietyEnglishName
    pic: str
    variety_type: str  # 对应 API 的 varietyType
    quot_type: Optional[str] = None  # 行情类型


# ============================================================================
# 行情数据模型
# ============================================================================


@dataclass
class Quote:
    """行情数据."""

    variety: str
    contract_id: str
    deliv_month: Optional[str] = None  # 夜盘行情/月行情使用此字段
    open: Optional[str] = None
    high: Optional[str] = None
    low: Optional[str] = None
    close: Optional[str] = None
    last_clear: Optional[str] = None
    last_price: Optional[str] = None  # 夜盘行情
    clear_price: Optional[str] = None
    diff: Optional[str] = None
    diff1: Optional[str] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    diff_i: Optional[int] = None
    turnover: Optional[str] = None
    # API 文档新增字段
    variety_order: Optional[str] = None  # 品种id
    delta: Optional[str] = None  # Delta
    match_qty_sum: Optional[int] = None  # 行权量
    diff_t: Optional[str] = None  # 成交额变化
    diff_v: Optional[int] = None  # 成交量变化
    volumn_rate: Optional[str] = None  # 期权期货成交比
    open_interest_rate: Optional[str] = None  # 期权期货持仓比
    period_over_period_chg: Optional[str] = None  # 环比变化
    implied_volatility: Optional[str] = None  # 隐含波动率
    series_id: Optional[str] = None  # 期权系列
    avg_open_interest: Optional[int] = None  # 日均持仓量
    year_total_volume: Optional[int] = None  # 本年成交量
    year_avg_open_interest: Optional[int] = None  # 本年日均持仓量
    year_turnover: Optional[str] = None  # 本年成交额
    year_match_qty_sum: Optional[int] = None  # 本年行权量
    quote_key: Optional[str] = None  # 行情key
    # 夜盘行情特有字段
    declare_price: Optional[str] = None  # 申报价
    variety_en: Optional[str] = None  # 品种英文名
    turnover_en: Optional[str] = None  # 成交额(英文格式)


@dataclass
class QuotesRequest:
    """行情请求."""

    trade_date: str
    trade_type: str
    variety_id: Optional[str] = None
    variety: Optional[str] = None  # 用于夜盘行情
    lang: Optional[str] = None
    statistics_type: Optional[int] = None  # 期权统计类型：0-合约，1-系列，2-品种



# ============================================================================
# 交割数据模型
# ============================================================================


@dataclass
class DeliveryData:
    """交割数据."""

    variety: str  # 品种名称
    contract_id: str  # 合约
    delivery_date: str  # 交割日期
    delivery_qty: int  # 交割量
    delivery_amt: str  # 交割金额
    # API 文档新增字段
    variety_en: Optional[str] = None  # 品种名称-英文


@dataclass
class DeliveryDataRequest:
    """交割数据请求."""

    variety_id: str  # 品种id
    start_month: str  # 开始月份
    end_month: str  # 结束月份
    variety_type: str = "0"  # 0=实物交割数据, 1=月均价交割数据


@dataclass
class DeliveryMatch:
    """交割配对."""

    contract_id: str  # 合约
    match_date: str  # 配对日期
    buy_member_id: str  # 买会员号
    sell_member_id: str  # 卖会员号
    delivery_qty: int  # 配对手数
    delivery_price: str  # 交割结算价


@dataclass
class DeliveryMatchRequest:
    """交割配对请求."""

    variety_id: str  # 品种id
    contract_id: str  # 合约id
    start_month: str  # 开始月份
    end_month: str  # 结束月份


@dataclass
class WarehouseReceipt:
    """仓单."""

    variety: str  # 品种名称
    wh_abbr: str  # 仓库/分库
    last_wbill_qty: int  # 昨日仓单量（手）
    wbill_qty: int  # 今日仓单量（手）
    diff: int  # 增减（手）
    # API 文档新增字段
    variety_order: Optional[str] = None  # 品种id
    group_code_order: Optional[str] = None
    wh_code_order: Optional[str] = None
    wh_type: Optional[str] = None
    gen_date: Optional[str] = None  # 生成日期
    delivery_abbr: Optional[str] = None
    reg_wbill_qty: Optional[int] = None
    logout_wbill_qty: Optional[int] = None  # 可选提货地点/分库-数量


@dataclass
class WarehouseReceiptResponse:
    """仓单日报响应."""

    entity_list: List["WarehouseReceipt"]  # 仓单列表
    if_agio_flag: Optional[str] = None
    agio_deli_type: Optional[str] = None
    if_agio_brand_flag: Optional[str] = None


@dataclass
class WarehouseReceiptRequest:
    """仓单请求."""

    variety_id: str  # 品种id
    trade_date: str  # 交易日


@dataclass
class DeliveryCost:
    """交割费用标准."""

    variety: str  # 品种名称
    earnest_rate: str  # 交割预报定金率(元/最小单位)
    unit: str  # 交易单位
    delivery_fee: str  # 交割手续费(元/手)
    fee_rate: str  # 仓储费标准(元/手天)
    start_date: str  # 开始日期
    end_date: str  # 结束日期


@dataclass
class WarehousePremium:
    """仓库升贴水."""

    variety_id: str  # 品种id
    variety_name: str  # 品种名称
    wh_name: str  # 仓库名称(提货地点)
    avg_agio: str  # 升贴水（元/吨）
    # 可选字段
    valid_date: Optional[str] = None
    wh_code: Optional[str] = None
    wh_group_abbr: Optional[str] = None  # 集团名称
    brand_abbr: Optional[str] = None  # 品牌


@dataclass
class WarehousePremiumResponse:
    """仓库升贴水响应."""

    entity_list: List["WarehousePremium"]
    if_agio_flag: Optional[str] = None
    agio_deli_type: Optional[str] = None
    if_agio_brand_flag: Optional[str] = None


# ============================================================================
# 会员数据模型
# ============================================================================


@dataclass
class Ranking:
    """排名数据."""

    rank: str
    qty_abbr: str  # 成交量会员简称
    today_qty: int  # 今日成交量
    qty_sub: int  # 成交量增减
    buy_abbr: str  # 持买会员简称
    today_buy_qty: int  # 今日持买量
    buy_sub: int  # 持买增减
    sell_abbr: str  # 持卖会员简称
    today_sell_qty: int  # 今日持卖量
    sell_sub: int  # 持卖增减


@dataclass
class DailyRankingRequest:
    """日排名请求."""

    variety_id: str
    contract_id: str
    trade_date: str
    trade_type: str  # 1=期货, 2=期权


@dataclass
class DailyRankingResponse:
    """日排名响应."""

    contract_id: str
    today_qty: int
    qty_sub: int
    today_buy_qty: int
    buy_sub: int
    today_sell_qty: int
    sell_sub: int
    qty_future_list: List[Ranking]  # 成交量排名(期货)
    buy_future_list: List[Ranking]  # 持买排名(期货)
    sell_future_list: List[Ranking]  # 持卖排名(期货)
    # API 文档新增字段 - 期权特有排名列表
    qty_option_up_list: Optional[List[Ranking]] = None  # 看涨期权成交量排名
    buy_option_up_list: Optional[List[Ranking]] = None  # 看涨期权持买排名
    sell_option_up_list: Optional[List[Ranking]] = None  # 看涨期权持卖排名
    qty_option_down_list: Optional[List[Ranking]] = None  # 看跌期权成交量排名
    buy_option_down_list: Optional[List[Ranking]] = None  # 看跌期权持买排名
    sell_option_down_list: Optional[List[Ranking]] = None  # 看跌期权持卖排名


@dataclass
class PhaseRankingRequest:
    """阶段排名请求."""

    variety: str
    start_month: str
    end_month: str
    trade_type: str


@dataclass
class PhaseRanking:
    """阶段排名数据."""

    seq: str
    member_id: str
    member_name: str
    month_qty: float
    qty_ratio: float
    month_amt: float
    amt_ratio: float
    # API 文档新增字段
    amt_member_id: Optional[str] = None  # 会员号-成交额
    amt_member_name: Optional[str] = None  # 会员简称-成交额


# ============================================================================
# 交易参数数据模型
# ============================================================================


@dataclass
class TradeParam:
    """交易参数."""

    contract_id: str
    spec_buy_rate: float  # 投机买保证金率
    spec_buy: float  # 投机买保证金
    hedge_buy_rate: float  # 套保买保证金率
    hedge_buy: float  # 套保买保证金
    rise_limit_rate: float  # 涨停板比例
    rise_limit: float  # 涨停价
    fall_limit: float  # 跌停价
    trade_date: str
    # API 文档新增字段
    style: Optional[str] = None  # 限仓模式
    self_tot_buy_posi_quota: Optional[int] = None  # 非期货公司会员持仓限额-期货
    self_tot_buy_posi_quota_ser_limit: Optional[int] = None  # 非期货公司会员持仓限额-期权
    client_buy_posi_quota: Optional[int] = None  # 客户持仓限额-期货
    client_buy_posi_quota_ser_limit: Optional[int] = None  # 客户持仓限额-期权
    contract_limit: Optional[int] = None  # 合约限额
    variety_limit: Optional[int] = None  # 品种限额


@dataclass
class DayTradeParamRequest:
    """日交易参数请求."""

    variety_id: str
    trade_type: str
    lang: str


@dataclass
class ContractInfo:
    """合约信息."""

    contract_id: str
    variety: str
    variety_order: str
    unit: int
    tick: str
    start_trade_date: str
    end_trade_date: str
    end_delivery_date: str
    trade_type: str


@dataclass
class ContractInfoRequest:
    """合约信息请求."""

    variety_id: str
    trade_type: str
    lang: str


@dataclass
class ArbitrageContract:
    """套利合约."""

    arbi_name: str  # 套利策略名称
    variety_name: str  # 品种名称
    arbi_contract_id: str  # 套利合约代码
    max_hand: int  # 最大下单手数
    tick: float  # 最小变动价位


@dataclass
class ArbitrageContractRequest:
    """套利合约请求."""

    lang: str


# ============================================================================
# 结算参数数据模型
# ============================================================================


@dataclass
class SettleParam:
    """结算参数."""

    variety: str
    variety_order: str
    contract_id: str
    clear_price: str  # 结算价
    open_fee: str  # 开仓手续费
    offset_fee: str  # 平仓手续费
    short_open_fee: str  # 日内开仓手续费
    short_offset_fee: str  # 日内平仓手续费
    style: str  # 限仓模式
    spec_buy_rate: str  # 投机买保证金率
    spec_sell_rate: str  # 投机卖保证金率
    hedge_buy_rate: str  # 套保买保证金率
    hedge_sell_rate: str  # 套保卖保证金率
    # API 文档新增字段 - 套保手续费
    hedge_open_fee: Optional[str] = None  # 套保开仓手续费
    hedge_offset_fee: Optional[str] = None  # 套保平仓手续费
    hedge_short_open_fee: Optional[str] = None  # 套保日内开仓手续费
    hedge_short_offset_fee: Optional[str] = None  # 套保日内平仓手续费


@dataclass
class SettleParamRequest:
    """结算参数请求."""

    variety_id: str
    trade_date: str
    trade_type: str
    lang: str


# ============================================================================
# 行情统计新增模型
# ============================================================================


@dataclass
class ContractMonthMaxRequest:
    """合约最值统计请求."""

    start_month: str  # 开始月份 YYYYMM
    end_month: str  # 结束月份 YYYYMM
    stat_content: str  # 统计内容: 0=成交量, 1=成交额, 2=持仓量, 3=价格统计
    trade_type: str  # 1=期货, 2=期权
    lang: str = "zh"


@dataclass
class ContractMonthMaxVolume:
    """合约最值统计-成交量."""

    contract_id: str
    sum_amount: int  # 总成交量
    max_amount: int  # 最大成交量
    max_amount_date: str  # 最大成交量日期
    min_amount: int  # 最小成交量
    min_amount_date: str  # 最小成交量日期
    avg_amount: int  # 平均成交量


@dataclass
class ContractMonthMaxTurnover:
    """合约最值统计-成交额."""

    contract_id: str
    sum_turnover: str  # 总成交额
    max_turnover: str  # 最大成交额
    max_turnover_date: str  # 最大成交额日期
    min_turnover: str  # 最小成交额
    min_turnover_date: str  # 最小成交额日期
    avg_turnover: str  # 平均成交额


@dataclass
class ContractMonthMaxOpeni:
    """合约最值统计-持仓量."""

    contract_id: str
    sum_openi: int  # 总持仓量
    max_openi: int  # 最大持仓量
    max_openi_date: str  # 最大持仓量日期
    min_openi: int  # 最小持仓量
    min_openi_date: str  # 最小持仓量日期
    avg_openi: int  # 平均持仓量


@dataclass
class ContractMonthMaxPrice:
    """合约最值统计-价格统计."""

    contract_id: str
    open: str  # 开盘价
    close: str  # 收盘价
    high: str  # 最高价
    high_date: str  # 最高价日期
    low: str  # 最低价
    low_date: str  # 最低价日期
    clear_price: str  # 结算价


@dataclass
class VarietyMonthYearStatRequest:
    """品种月度统计请求."""

    trade_month: str  # 交易月份 YYYYMM
    trade_type: str  # 1=期货, 2=期权
    lang: str = "zh"


@dataclass
class VarietyMonthYearStat:
    """品种月度统计."""

    variety: str  # 品种名称
    this_month_volumn: int  # 本月成交量
    volumn_balance: str  # 成交量同比
    volumn_chain: str  # 成交量环比
    this_year_volumn: int  # 本年成交量
    year_volumn_chain: str  # 本年成交量同比
    this_month_turnover: str  # 本月成交额
    turnover_balance: str  # 成交额同比
    turnover_chain: str  # 成交额环比
    this_year_turnover: str  # 本年成交额
    year_turnover_chain: str  # 本年成交额同比
    this_month_openi: int  # 本月持仓量
    openi_balance: str  # 持仓量同比
    openi_chain: str  # 持仓量环比


@dataclass
class RiseFallEventRequest:
    """合约停板查询请求."""

    start_date: str  # 开始日期 YYYYMMDD
    end_date: str  # 结束日期 YYYYMMDD
    variety_id: str  # 品种id, all=全部
    lang: str = "zh"


@dataclass
class RiseFallEvent:
    """合约停板事件."""

    trade_date: str  # 交易日期
    contract_id: str  # 合约代码
    direction: str  # 方向: 涨停/跌停
    times: int  # 次数


@dataclass
class DivisionPriceInfoRequest:
    """分时结算参考价请求."""

    variety_id: str  # 品种id
    trade_date: str  # 交易日期 YYYYMMDD
    trade_type: str  # 1=期货, 2=期权


@dataclass
class DivisionPriceInfo:
    """分时结算参考价."""

    calculate_date: str  # 计算日期
    calculate_time: str  # 计算时间
    variety_name: str  # 品种名称
    variety_en_name: str  # 品种英文名
    contract_id: str  # 合约代码
    clear_price: int  # 结算参考价
    series_id: Optional[str] = None  # 期权系列
    volatility: Optional[float] = None  # 波动率


# ============================================================================
# 交割统计新增模型
# ============================================================================


@dataclass
class TcCongregateDeliveryRequest:
    """一次性交割卖方仓单查询请求."""

    variety: str  # 品种id, all=全部
    contract_month: str  # 合约月份 YYYYMM


@dataclass
class TcCongregateDelivery:
    """一次性交割卖方仓单."""

    variety_id: str  # 品种id
    variety_name: str  # 品种名称
    contract: str  # 合约
    warehouse_name: str  # 仓库名称
    wbill_quantity: str  # 仓单数量
    agreeable_place: Optional[str] = None  # 协议提货地点
    agreeable_brand: Optional[str] = None  # 协议品牌
    agreeable_quality: Optional[str] = None  # 协议质量
    agreeable_quantity: Optional[str] = None  # 协议数量
    agreeable_spread: Optional[str] = None  # 协议升贴水
    contracts: Optional[str] = None  # 合约列表
    contract_way: Optional[str] = None  # 合约方式
    wh_group_name: Optional[str] = None  # 仓库集团名称


@dataclass
class RollDeliverySellerIntentionRequest:
    """滚动交割卖方交割意向表请求."""

    variety: str  # 品种id, all=全部
    date: str  # 日期 YYYYMMDD


@dataclass
class RollDeliverySellerIntention:
    """滚动交割卖方交割意向."""

    variety_id: str  # 品种id
    variety_name: str  # 品种名称
    contract: str  # 合约
    type: str  # 类型: 仓库/厂库
    warehouse_code: str  # 仓库代码
    warehouse_name: str  # 仓库名称
    quantity: str  # 数量
    trade_date: str  # 交易日期
    delivery_way: str  # 交割方式
    agreeable_place: Optional[str] = None
    agreeable_brand: Optional[str] = None
    agreeable_quality: Optional[str] = None
    agreeable_quantity: Optional[str] = None
    agreeable_spread: Optional[str] = None
    contracts: Optional[str] = None
    contract_way: Optional[str] = None
    wh_group_name: Optional[str] = None


@dataclass
class BondedDeliveryRequest:
    """交割结算价请求."""

    start_date: str  # 开始日期 YYYYMMDD
    end_date: str  # 结束日期 YYYYMMDD


@dataclass
class BondedDelivery:
    """交割结算价."""

    delivery_date: str  # 交割日期
    delivery_way: str  # 交割方式
    variety_id: str  # 品种id
    contract_id: str  # 合约代码
    delivery_price: str  # 交割结算价
    wh_abbr: Optional[str] = None  # 仓库简称
    bonded_delivery_price: Optional[str] = None  # 保税交割结算价


@dataclass
class PlywoodDeliveryCommodity:
    """胶合板交割商品."""

    apply_id: str  # 申请id
    wh_name: str  # 仓库名称
    wh_abbr: str  # 仓库简称
    upload_file_id: str  # 上传文件id
    file_size: int  # 文件大小
    upload_file_name: str  # 上传文件名


@dataclass
class FactorySpotAgioQuote:
    """纤维板厂库自报换货差价."""

    seq_no: str  # 序号
    wh_abbr: str  # 仓库简称
    variety_id: str  # 品种id
    variety_name: str  # 品种名称
    wh_code: Optional[str] = None
    bh: Optional[str] = None
    mdmin: Optional[str] = None
    mdmax: Optional[str] = None
    jq: Optional[str] = None
    agio: Optional[str] = None
    min_exchange_amount: Optional[str] = None
    wh_addr: Optional[str] = None
    connect_person: Optional[str] = None
    tel: Optional[str] = None


# ============================================================================
# 交易参数新增模型
# ============================================================================


@dataclass
class MonthTradeParamItem:
    """月交易参数项."""

    variety_id: str  # 品种id
    contract_id: str  # 合约代码
    first_rate: float  # 首日保证金率
    fifteenth_rate: float  # 15日保证金率
    first_rate_hedge: float  # 首日套保保证金率
    fifteenth_rate_hedge: float  # 15日套保保证金率
    delivery_rise_limit: float  # 交割涨跌停板
    first_self_quota: str  # 首日非期货公司会员限仓
    first_client_quota: str  # 首日客户限仓
    tenth_self_quota: str  # 10日非期货公司会员限仓
    tenth_client_quota: str  # 10日客户限仓


@dataclass
class MonthTradeParamResponse:
    """月交易参数响应."""

    month_date: str  # 月份
    first_date: str  # 首日
    tenth_date: str  # 10日
    fifteenth_date: str  # 15日
    list: List[MonthTradeParamItem]  # 参数列表


@dataclass
class TradingParamRequest:
    """交易参数表请求."""

    lang: str = "zh"


@dataclass
class TradingParam:
    """交易参数表（品种）."""

    variety_id: str  # 品种id
    variety_name: str  # 品种名称
    trading_margin_rate_speculation: str  # 投机交易保证金率
    trading_margin_rate_hedging: str  # 套保交易保证金率
    price_limit_existing_contract: str  # 已有合约涨跌停板
    price_limit_new_contract: str  # 新合约涨跌停板
    price_limit_delivery_month: str  # 交割月涨跌停板
    # N日参数
    trading_margin_rate_speculation_n: Optional[str] = None
    trading_margin_rate_hedging_n: Optional[str] = None
    settlement_margin_rate_hedging_n: Optional[str] = None
    price_limit_n: Optional[str] = None
    # N+1日参数
    trading_margin_rate_n1: Optional[str] = None
    settlement_margin_rate_hedging_n1: Optional[str] = None
    price_limit_n1: Optional[str] = None
    # N+2日参数
    trading_margin_rate_n2: Optional[str] = None
    price_limit_n2: Optional[str] = None
    # 限仓和手续费
    trading_limit: Optional[str] = None
    spec_open_fee: Optional[str] = None  # 投机开仓手续费
    spec_offset_fee: Optional[str] = None  # 投机平仓手续费
    spec_short_open_fee: Optional[str] = None  # 投机日内开仓手续费
    spec_short_offset_fee: Optional[str] = None  # 投机日内平仓手续费
    hedge_open_fee: Optional[str] = None  # 套保开仓手续费
    hedge_offset_fee: Optional[str] = None  # 套保平仓手续费
    hedge_short_open_fee: Optional[str] = None  # 套保日内开仓手续费
    hedge_short_offset_fee: Optional[str] = None  # 套保日内平仓手续费
    fee_style: Optional[str] = None  # 手续费类型
    fee_style_en: Optional[str] = None  # 手续费类型英文
    delivery_fee: Optional[str] = None  # 交割手续费
    max_hand: Optional[str] = None  # 最大下单手数


@dataclass
class MarginArbiPerfPara:
    """套利交易保证金."""

    arbi_name: str  # 套利名称
    variety_name: str  # 品种名称
    arbi_contract_id: str  # 套利合约代码
    perf_sh_type: str  # 组合类型 (套保-套保等)
    margin_amt: float  # 保证金金额


@dataclass
class NewContractInfoRequest:
    """期货/期权合约增挂请求."""

    trade_date: str  # 交易日期 YYYYMMDD
    trade_type: str  # 1=期货, 2=期权
    lang: str = "zh"


@dataclass
class NewContractInfo:
    """新增合约信息."""

    trade_type: str  # 交易类型
    variety: str  # 品种名称
    variety_order: str  # 品种id
    contract_id: str  # 合约代码
    start_trade_date: str  # 开始交易日期
    ref_price_unit: str  # 参考价单位
    no_rise_limit: Optional[str] = None  # 无涨停限制
    no_fall_limit: Optional[str] = None  # 无跌停限制


@dataclass
class MainSeriesInfoRequest:
    """做市商持续报价合约请求."""

    variety_id: str  # 品种id
    trade_date: str  # 交易日期 YYYYMMDD


@dataclass
class MainSeriesInfo:
    """做市商持续报价合约."""

    trade_date: str  # 交易日期
    variety_id: str  # 品种id
    series_id: str  # 系列id
    contract_id: str  # 合约代码
