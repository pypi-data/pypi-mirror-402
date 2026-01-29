"""DCE API Python SDK - 完整示例.

演示 SDK 的所有主要功能，使用官方 API 文档 (dceapiv1.0.md) 中的示例参数。
这既是一个示例脚本，也是一个针对官方示例数据的验证测试。

运行前请设置环境变量:
    export DCE_API_KEY="your-api-key"
    export DCE_SECRET="your-secret"

运行:
    python examples/complete.py
"""

import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional

# 添加 src 目录到 Python 路径（用于开发环境）
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dceapi import (
    APIError,
    AuthError,
    BondedDeliveryRequest,
    Client,
    Config,
    ContractInfoRequest,
    ContractMonthMaxRequest,
    DailyRankingRequest,
    DailyRankingResponse,
    DayTradeParamRequest,
    DeliveryDataRequest,
    DeliveryMatchRequest,
    DivisionPriceInfoRequest,
    GetArticleByPageRequest,
    MainSeriesInfoRequest,
    NetworkError,
    NewContractInfoRequest,
    PhaseRankingRequest,
    QuotesRequest,
    RiseFallEventRequest,
    RollDeliverySellerIntentionRequest,
    SettleParamRequest,
    TcCongregateDeliveryRequest,
    TradingParamRequest,
    ValidationError,
    VarietyMonthYearStatRequest,
    WarehouseReceiptRequest,
)

# 全局变量
TRADE_DATE = ""
TRADE_MONTH = ""


def safe_str(val: Any) -> str:
    """安全转换为字符串，None 转为空字符串."""
    return str(val) if val is not None else ""


def safe_int(val: Any) -> int:
    """安全转换为整数，None 转为 0."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


class DCEAPIDemo:
    """DCE API 演示类."""

    def __init__(self):
        """初始化演示."""
        print("\nDCE API Python SDK - 完整功能演示 (基于 dceapiv1.0.md)")
        print("=" * 80)
        self.client = self._create_client()

    def _create_client(self) -> Client:
        """创建客户端."""
        try:
            config = Config.from_env()
        except ValidationError:
            # Missing env vars, create empty config to trigger fallback logic below
            # Note: Config requires api_key/secret, so we must instantiate carefully or use dummy
            print("⚠️  未设置环境变量，使用演示模式（API调用将会失败）")
            print("若要实际运行，请设置:")
            print('  export DCE_API_KEY="your-api-key"')
            print('  export DCE_SECRET="your-secret"')
            print()
            return Client(Config(api_key="demo-key", secret="demo-secret"))

        if not config.base_url:
            config.base_url = "http://www.dce.com.cn"
        if not config.timeout:
            config.timeout = 30
        if not config.lang:
            config.lang = "zh"
        if not config.trade_type:
            config.trade_type = 1

        return Client(config)

    def get_trade_date(self) -> bool:
        """获取交易日期."""
        global TRADE_DATE, TRADE_MONTH
        try:
            result = self.client.common.get_curr_trade_date()
            TRADE_DATE = result.trade_date
            TRADE_MONTH = TRADE_DATE[:6]
            print(f"✓ 当前交易日期: {TRADE_DATE} {TRADE_MONTH}")
            TRADE_DATE = "20260119"
            TRADE_MONTH = "202601"
            return True
        except Exception as e:
            now = datetime.now()
            # 如果是周末，调整到周五
            if now.weekday() == 5:  # 周六
                now = now - timedelta(days=1)
            elif now.weekday() == 6:  # 周日
                now = now - timedelta(days=2)
            
            TRADE_DATE = now.strftime("%Y%m%d")
            TRADE_MONTH = TRADE_DATE[:6]
            print(f"⚠️  无法获取交易日期: {e}")
            print(f"⚠️  使用当前日期: {TRADE_DATE} {TRADE_MONTH}")
            return True

    def run_common_examples(self):
        """运行通用服务示例."""
        print("\n" + "=" * 80)
        print("CommonService - 通用服务")
        print("=" * 80)

        # 1. GetCurrTradeDate
        print("\n[1/2] GetCurrTradeDate - 获取当前交易日期")
        print(f"✅ 当前交易日期: {TRADE_DATE}")

        # 2. GetVarietyList
        print("\n[2/2] GetVarietyList - 获取品种列表")
        try:
            varieties = self.client.common.get_variety_list()
            print(f"✅ 品种数量: {len(varieties)}")
            for i, v in enumerate(varieties):
                if i >= 5:
                    print(f"  ... 还有 {len(varieties) - 5} 个品种")
                    break
                print(f"  - {v.variety_name} ({v.variety_id}) - {v.variety_type}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

    def run_news_examples(self):
        """运行资讯服务示例."""
        print("\n" + "=" * 80)
        print("NewsService - 资讯服务")
        print("=" * 80)

        columns = [
            ("244", "业务公告与通知"),
            ("245", "活动公告与通知"),
            ("246", "交易所新闻-文媒"),
            ("248", "媒体看大商所-文媒"),
            ("1076", "今日提示"),
            ("242", "新闻发布"),
        ]

        for i, (col_id, name) in enumerate(columns):
            print(f"\n[{i+1}/6] GetArticleByPage - {name} (columnId={col_id})")
            try:
                req = GetArticleByPageRequest(
                    column_id=col_id,
                    page_no=1,
                    site_id=5,
                    page_size=3
                )
                result = self.client.news.get_article_by_page(req)
                print(f"✅ 总文章数: {result.total_count}")
                for j, article in enumerate(result.result_list):
                    if j >= 2:
                        break
                    print(f"  - [{article.show_date}] {article.title}")
            except Exception as e:
                print(f"❌ Error: {e}")
            time.sleep(0.5)

    def run_market_examples(self):
        """运行行情服务示例."""
        print("\n" + "=" * 80)
        print("MarketService - 行情服务")
        print("=" * 80)
        print(f"\n使用交易日期: {TRADE_DATE}")

        # 1. GetNightQuotes
        print("\n[1/11] GetNightQuotes - 获取夜盘行情 (豆一 a)")
        try:
            req = QuotesRequest(variety="a", trade_type="1", trade_date=TRADE_DATE)
            quotes = self.client.market.get_night_quotes(req)
            print(f"✅ 豆一夜盘行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                contract = safe_str(q.deliv_month)
                if not contract or q.variety == "总计":
                    continue
                if count >= 3:
                    break
                print(f"  {contract} | 最新价: {safe_str(q.last_price)} | 持仓量: {safe_int(q.open_interest)}")
                count += 1
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 2. GetDayQuotes (Future)
        print("\n[2/11] GetDayQuotes - 获取日行情-期货 (豆一 a)")
        try:
            req = QuotesRequest(variety_id="a", trade_date=TRADE_DATE, trade_type="1", lang="zh")
            quotes = self.client.market.get_day_quotes(req)
            print(f"✅ 豆一日行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                if not q.contract_id or q.variety == "总计":
                    continue
                if count >= 3:
                    break
                print(f"  {q.contract_id} | 开: {safe_str(q.open)} 高: {safe_str(q.high)} "
                      f"低: {safe_str(q.low)} 收: {safe_str(q.close)}")
                count += 1
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 3. GetDayQuotes (Option)
        print("\n[3/11] GetDayQuotes - 获取日行情-期权 (豆一期权)")
        try:
            req = QuotesRequest(
                variety_id="a", trade_date=TRADE_DATE, trade_type="2",
                lang="zh", statistics_type=0
            )
            quotes = self.client.market.get_day_quotes(req)
            print(f"✅ 豆一期权日行情, 合约数: {len(quotes)}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 4. GetWeekQuotes
        print("\n[4/11] GetWeekQuotes - 获取周行情 (豆粕 m)")
        try:
            req = QuotesRequest(variety_id="m", trade_date=TRADE_DATE, trade_type="1")
            quotes = self.client.market.get_week_quotes(req)
            print(f"✅ 豆粕周行情, 合约数: {len(quotes)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 5. GetMonthQuotes
        print("\n[5/11] GetMonthQuotes - 获取月行情 (玉米 c)")
        try:
            req = QuotesRequest(variety="c", trade_date=TRADE_DATE, trade_type="1")
            quotes = self.client.market.get_month_quotes(req)
            print(f"✅ 玉米月行情, 合约数: {len(quotes)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 6. GetContractMonthMax (Volume)
        print("\n[6/11] GetContractMonthMax - 合约最值统计-成交量")
        try:
            req = ContractMonthMaxRequest(
                start_month=TRADE_MONTH, end_month=TRADE_MONTH,
                stat_content="0", trade_type="1", lang="zh"
            )
            stats = self.client.market.get_contract_month_max(req)
            print(f"✅ 成交量统计数量: {len(stats)}")
            for i, stat in enumerate(stats):
                if i >= 2:
                    break
                print(f"  {stat.contract_id} | 总量: {stat.sum_amount} | "
                      f"最大: {stat.max_amount} ({stat.max_amount_date})")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 7. GetContractMonthMax (Turnover)
        print("\n[7/11] GetContractMonthMax - 合约最值统计-成交额")
        try:
            req = ContractMonthMaxRequest(
                start_month=TRADE_MONTH, end_month=TRADE_MONTH,
                stat_content="1", trade_type="1", lang="zh"
            )
            stats = self.client.market.get_contract_month_max(req)
            print(f"✅ 成交额统计数量: {len(stats)}")
            for i, stat in enumerate(stats):
                if i >= 2:
                    break
                print(f"  {stat.contract_id} | 总额: {stat.sum_turnover} | "
                      f"最大: {stat.max_turnover} ({stat.max_turnover_date})")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 8. GetContractMonthMax (Open Interest)
        print("\n[8/11] GetContractMonthMax - 合约最值统计-持仓量")
        try:
            req = ContractMonthMaxRequest(
                start_month=TRADE_MONTH, end_month=TRADE_MONTH,
                stat_content="2", trade_type="1", lang="zh"
            )
            stats = self.client.market.get_contract_month_max(req)
            print(f"✅ 持仓量统计数量: {len(stats)}")
            for i, stat in enumerate(stats):
                if i >= 2:
                    break
                print(f"  {stat.contract_id} | 总持仓: {stat.sum_openi} | "
                      f"最大: {stat.max_openi} ({stat.max_openi_date})")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 9. GetContractMonthMax (Price)
        print("\n[9/11] GetContractMonthMax - 合约最值统计-价格统计")
        try:
            req = ContractMonthMaxRequest(
                start_month=TRADE_MONTH, end_month=TRADE_MONTH,
                stat_content="3", trade_type="1", lang="zh"
            )
            stats = self.client.market.get_contract_month_max(req)
            print(f"✅ 价格统计数量: {len(stats)}")
            for i, stat in enumerate(stats):
                if i >= 2:
                    break
                print(f"  {stat.contract_id} | 开: {stat.open} 收: {stat.close} "
                      f"高: {stat.high} ({stat.high_date}) 低: {stat.low} ({stat.low_date})")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 10. GetVarietyMonthYearStat
        print("\n[10/11] GetVarietyMonthYearStat - 获取品种月度统计")
        try:
            req = VarietyMonthYearStatRequest(
                trade_month=TRADE_MONTH, trade_type="1", lang="zh"
            )
            stats = self.client.market.get_variety_month_year_stat(req)
            print(f"✅ 品种月度统计数量: {len(stats)}")
            for i, stat in enumerate(stats):
                if i >= 3:
                    break
                print(f"  {stat.variety} | 本月成交量: {stat.this_month_volumn} | "
                      f"本年成交量: {stat.this_year_volumn}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 11. GetRiseFallEvent
        print("\n[11/11] GetRiseFallEvent - 获取合约停板查询")
        try:
            start_date = TRADE_MONTH + "01"
            req = RiseFallEventRequest(
                start_date=start_date, end_date=TRADE_DATE,
                variety_id="all", lang="zh"
            )
            events = self.client.market.get_rise_fall_event(req)
            print(f"✅ 停板事件数量: {len(events)}")
            for i, event in enumerate(events):
                if i >= 3:
                    break
                print(f"  {event.trade_date} | 合约: {event.contract_id} | "
                      f"方向: {event.direction} | 次数: {event.times}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # Bonus: GetDivisionPriceInfo
        print("\n[Bonus] GetDivisionPriceInfo - 获取分时结算参考价")
        try:
            req = DivisionPriceInfoRequest(
                variety_id="m", trade_date=TRADE_DATE, trade_type="1"
            )
            prices = self.client.market.get_division_price_info(req)
            print(f"✅ 分时结算参考价数量: {len(prices)}")
            for i, p in enumerate(prices):
                if i >= 3:
                    break
                print(f"  {p.calculate_date} {p.calculate_time} | "
                      f"合约: {p.contract_id} | 参考价: {p.clear_price}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_trade_examples(self):
        """运行交易服务示例."""
        print("\n" + "=" * 80)
        print("TradeService - 交易参数服务")
        print("=" * 80)

        # 1. GetDayTradeParam
        print("\n[1/8] GetDayTradeParam - 获取日交易参数 (豆一 a)")
        try:
            req = DayTradeParamRequest(variety_id="a", trade_type="1", lang="zh")
            params = self.client.trade.get_day_trade_param(req)
            print(f"✅ 日交易参数数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    break
                print(f"  合约: {p.contract_id} | 投机买保证金率: {p.spec_buy_rate*100:.2f}% | "
                      f"涨停价: {p.rise_limit} | 跌停价: {p.fall_limit}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 2. GetMonthTradeParam
        print("\n[2/8] GetMonthTradeParam - 获取月交易参数")
        try:
            month_param = self.client.trade.get_month_trade_param()
            print(f"✅ 月份: {month_param.month_date} | 首日: {month_param.first_date} | "
                  f"十日: {month_param.tenth_date} | 十五日: {month_param.fifteenth_date}")
            print(f"  参数项数量: {len(month_param.list)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 3. GetTradingParam
        print("\n[3/8] GetTradingParam - 获取交易参数表 (品种)")
        try:
            req = TradingParamRequest(lang="zh")
            params = self.client.trade.get_trading_param(request=req)
            print(f"✅ 交易参数表数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    break
                print(f"  {p.variety_name} | 投机保证金率: {p.trading_margin_rate_speculation} | "
                      f"套保保证金率: {p.trading_margin_rate_hedging}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 4. GetContractInfo
        print("\n[4/8] GetContractInfo - 获取合约信息 (豆一 a)")
        try:
            req = ContractInfoRequest(variety_id="a", trade_type="1", lang="zh")
            contracts = self.client.trade.get_contract_info(req)
            print(f"✅ 合约数量: {len(contracts)}")
            for i, c in enumerate(contracts):
                if i >= 3:
                    break
                print(f"  合约: {c.contract_id} | 品种: {c.variety} | "
                      f"开始交易日: {c.start_trade_date} | 最后交易日: {c.end_trade_date}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 5. GetArbitrageContract
        print("\n[5/8] GetArbitrageContract - 获取套利合约")
        try:
            contracts = self.client.trade.get_arbitrage_contract(lang="zh")
            print(f"✅ 套利合约数量: {len(contracts)}")
            for i, a in enumerate(contracts):
                if i >= 3:
                    break
                print(f"  {a.arbi_name} | {a.variety_name} | {a.arbi_contract_id} | "
                      f"最大手数: {a.max_hand} | 最小变动: {a.tick}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 6. GetMarginArbiPerfPara
        print("\n[6/8] GetMarginArbiPerfPara - 获取套利交易保证金")
        try:
            params = self.client.trade.get_margin_arbi_perf_para(lang="zh")
            print(f"✅ 套利保证金参数数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    break
                print(f"  {p.arbi_name} | {p.variety_name} | {p.perf_sh_type} | "
                      f"保证金: {p.margin_amt:.2f}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 7. GetNewContractInfo
        print("\n[7/8] GetNewContractInfo - 获取期货/期权合约增挂")
        try:
            req = NewContractInfoRequest(trade_date=TRADE_DATE, trade_type="1", lang="zh")
            contracts = self.client.trade.get_new_contract_info(req)
            print(f"✅ 新增合约数量: {len(contracts)}")
            for i, c in enumerate(contracts):
                if i >= 3:
                    break
                print(f"  {c.variety} | {c.contract_id} | 开始交易日: {c.start_trade_date}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 8. GetMainSeriesInfo
        print("\n[8/8] GetMainSeriesInfo - 获取做市商持续报价合约")
        try:
            req = MainSeriesInfoRequest(variety_id="m", trade_date=TRADE_DATE)
            series = self.client.trade.get_main_series_info(req)
            print(f"✅ 做市商持续报价合约数量: {len(series)}")
            for i, s in enumerate(series):
                if i >= 3:
                    break
                print(f"  品种: {s.variety_id} | 系列: {s.series_id} | 合约: {s.contract_id}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_settle_examples(self):
        """运行结算服务示例."""
        print("\n" + "=" * 80)
        print("SettleService - 结算参数服务")
        print("=" * 80)

        # 1. GetSettleParam
        print("\n[1/1] GetSettleParam - 获取结算参数 (豆一 a)")
        try:
            req = SettleParamRequest(variety_id="a", trade_date=TRADE_DATE, trade_type="1", lang="zh")
            params = self.client.settle.get_settle_param(req)
            print(f"✅ 结算参数数量: {len(params)}")
            for i, s in enumerate(params):
                if i >= 3:
                    break
                print(f"  合约: {s.contract_id} | 结算价: {s.clear_price} | "
                      f"投机买保证金率: {s.spec_buy_rate} | 投机卖保证金率: {s.spec_sell_rate}")
        except Exception as e:
             print(f"❌ Error: {e}")

    def run_member_examples(self):
        """运行会员服务示例."""
        print("\n" + "=" * 80)
        print("MemberService - 会员成交持仓统计服务")
        print("=" * 80)

        # 1. GetDailyRanking (Future)
        print("\n[1/3] GetDailyRanking - 获取日成交持仓排名-期货 (a2603)")
        try:
            req = DailyRankingRequest(
                variety_id="a", trade_date=TRADE_DATE, contract_id="a2603", trade_type="1"
            )
            ranking = self.client.member.get_daily_ranking(req)
            if ranking.qty_future_list:
                print("✅ 期货成交量排名前3:")
                for i, r in enumerate(ranking.qty_future_list):
                    if i >= 3: break
                    print(f"  {r.rank}. {r.qty_abbr} | 成交量: {r.today_qty} | 增减: {r.qty_sub}")
            if ranking.buy_future_list:
                print("✅ 期货持买排名前3:")
                for i, r in enumerate(ranking.buy_future_list):
                    if i >= 3: break
                    print(f"  {r.rank}. {r.buy_abbr} | 持买: {r.today_buy_qty} | 增减: {r.buy_sub}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(2)

        # 2. GetDailyRanking (Option)
        print("\n[2/3] GetDailyRanking - 获取日成交持仓排名-期权 (豆粕期权)")
        try:
            req = DailyRankingRequest(
                variety_id="m", trade_date=TRADE_DATE, contract_id="m2603", trade_type="2"
            )
            ranking = self.client.member.get_daily_ranking(req)
            if ranking.qty_option_up_list:
                print("✅ 期货看涨成交量排名前3:")
                for i, r in enumerate(ranking.qty_option_up_list):
                    if i >= 3: break
                    print(f"  {r.rank}. {r.qty_abbr} | 成交量: {r.today_qty} | 增减: {r.qty_sub}")
            if ranking.qty_option_down_list:
                print("✅ 期货看跌成交量排名前3:")
                for i, r in enumerate(ranking.qty_option_down_list):
                    if i >= 3: break
                    print(f"  {r.rank}. {r.qty_abbr} | 成交量: {r.today_qty} | 增减: {r.qty_sub}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 3. GetPhaseRanking
        print("\n[3/3] GetPhaseRanking - 获取阶段成交排名 (豆一 a)")
        try:
            req = PhaseRankingRequest(
                variety="a", start_month=TRADE_MONTH, end_month=TRADE_MONTH, trade_type="1"
            )
            rankings = self.client.member.get_phase_ranking(req)
            print(f"✅ 阶段排名数量: {len(rankings)}")
            for i, r in enumerate(rankings):
                if i >= 3:
                     break
                print(f"  {r.seq}. {r.member_name} | 成交量: {r.month_qty:.0f} (占比: {r.qty_ratio:.2f}%) | "
                      f"成交额: {r.month_amt:.2f}亿 (占比: {r.amt_ratio:.2f}%)")
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_delivery_examples(self):
        """运行交割服务示例."""
        print("\n" + "=" * 80)
        print("DeliveryService - 交割统计服务")
        print("=" * 80)

        # 1. GetDeliveryData
        print("\n[1/11] GetDeliveryData - 获取交割数据 (豆一 a)")
        try:
            req = DeliveryDataRequest(
                variety_id="a", start_month="202501", end_month="202510", variety_type="1"
            )
            data = self.client.delivery.get_delivery_data(req)
            print(f"✅ 交割数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.variety} | {d.contract_id} | 交割量: {d.delivery_qty} | "
                      f"金额: {d.delivery_amt}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 2. GetDeliveryMatch
        print("\n[2/11] GetDeliveryMatch - 获取交割配对表 (豆二 b)")
        try:
            req = DeliveryMatchRequest(
                variety_id="b", contract_id="all", start_month="202510", end_month="202510"
            )
            matches = self.client.delivery.get_delivery_match(req)
            print(f"✅ 配对数据数量: {len(matches)}")
            for i, m in enumerate(matches):
                if i >= 3: break
                print(f"  {m.contract_id} | {m.match_date} | 买: {m.buy_member_id} | "
                      f"卖: {m.sell_member_id} | 量: {m.delivery_qty} | 价: {m.delivery_price}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 3. GetWarehouseReceipt
        print("\n[3/11] GetWarehouseReceipt - 获取仓单日报 (豆一 a)")
        try:
            req = WarehouseReceiptRequest(variety_id="a", trade_date=TRADE_DATE)
            resp = self.client.delivery.get_warehouse_receipt(req)
            print(f"✅ 仓单数据数量: {len(resp.entity_list)}")
            for i, r in enumerate(resp.entity_list):
                if i >= 3: break
                print(f"  {r.variety} | {r.wh_abbr} | 昨日: {r.last_wbill_qty} | "
                      f"今日: {r.wbill_qty} | 增减: {r.diff}")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1)

        # 4. GetTcCongregateDelivery
        print("\n[4/11] GetTcCongregateDelivery - 获取一次性交割卖方仓单")
        try:
            req = TcCongregateDeliveryRequest(variety="all", contract_month="202508")
            data = self.client.delivery.get_tc_congregate_delivery(req)
            print(f"✅ 仓单数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.variety_name} | {d.contract} | {d.warehouse_name} | 数量: {d.wbill_quantity}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 5. GetRollDeliverySellerIntention
        print("\n[5/11] GetRollDeliverySellerIntention - 获取滚动交割卖方意向")
        try:
            req = RollDeliverySellerIntentionRequest(variety="all", date="20251013")
            data = self.client.delivery.get_roll_delivery_seller_intention(req)
            print(f"✅ 意向数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.variety_name} | {d.contract} | {d.warehouse_name} | 数量: {d.quantity}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 6. GetBondedDelivery
        print("\n[6/11] GetBondedDelivery - 获取交割结算价")
        try:
            req = BondedDeliveryRequest(start_date="20201009", end_date="20251009")
            data = self.client.delivery.get_bonded_delivery(req)
            print(f"✅ 结算价数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.delivery_date} | {d.variety_id} | {d.contract_id} | 价格: {d.delivery_price}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 7. GetTdBondedDelivery
        print("\n[7/11] GetTdBondedDelivery - 获取保税交割结算价")
        try:
            req = BondedDeliveryRequest(start_date="20171001", end_date="20201009")
            data = self.client.delivery.get_td_bonded_delivery(req)
            print(f"✅ 保税结算价数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.delivery_date} | {d.variety_id} | {d.contract_id} | "
                      f"即期: {d.delivery_price} | 保税: {d.bonded_delivery_price}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 8. GetFactorySpotAgioQuotes
        print("\n[8/11] GetFactorySpotAgioQuotes - 获取纤维板厂库自报换货差价")
        try:
            data = self.client.delivery.get_factory_spot_agio_quotes()
            print(f"✅ 差价数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.variety_name} | {d.wh_abbr} | 升贴水: {d.agio}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 9. GetWarehousePremium
        print("\n[9/11] GetWarehousePremium - 获取仓库升贴水")
        try:
            resp = self.client.delivery.get_warehouse_premium(variety_id="all", trade_date="20251010")
            print(f"✅ 升贴水数据数量: {len(resp.entity_list)}")
            for i, d in enumerate(resp.entity_list):
                 if i >= 3: break
                 print(f"  {d.variety_name} | {d.wh_name} | 升贴水: {d.avg_agio}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 10. GetPlywoodDeliveryCommodity
        print("\n[10/11] GetPlywoodDeliveryCommodity - 获取胶合板交割商品")
        try:
            data = self.client.delivery.get_plywood_delivery_commodity()
            print(f"✅ 商品数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3: break
                print(f"  {d.wh_name} | {d.upload_file_name}")
        except Exception as e:
             print(f"❌ Error: {e}")
        time.sleep(1)

        # 11. GetDeliveryCost
        print("\n[11/11] GetDeliveryCost - 获取交割费用标准 (豆一 a)")
        try:
            costs = self.client.delivery.get_delivery_cost(variety_id="a", variety_type="1", lang="zh")
            print(f"✅ 费用标准数量: {len(costs)}")
            for i, c in enumerate(costs):
                if i >= 3: break
                print(f"  {c.variety} | 交割费: {c.delivery_fee} | 仓储费: {c.fee_rate}")
        except Exception as e:
             print(f"❌ Error: {e}")


def main():
    """主函数."""
    demo = DCEAPIDemo()
    
    # 获取当前交易日
    if not demo.get_trade_date():
        return

    # 依次运行各服务示例
    demo.run_common_examples()
    demo.run_news_examples()
    demo.run_market_examples()
    demo.run_trade_examples()
    demo.run_settle_examples()
    demo.run_member_examples()
    demo.run_delivery_examples()

    print("\n" + "=" * 80)
    print("演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    main()
