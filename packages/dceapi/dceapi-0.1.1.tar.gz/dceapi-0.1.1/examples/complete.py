"""DCE API Python SDK - 完整示例.

演示 SDK 的所有主要功能，包括:
- 客户端配置
- 通用服务（交易日期、品种列表）
- 资讯服务（文章列表、文章详情）
- 行情服务:
  - 日行情、周行情、月行情、夜盘行情
  - 合约最值统计、品种月度统计、合约停板查询、分时结算参考价
- 交易服务:
  - 日交易参数、月交易参数、交易参数表
  - 合约信息、套利合约、套利交易保证金
  - 新增合约信息、做市商持续报价合约
- 结算服务（结算参数）
- 会员服务（日排名、阶段排名）
- 交割服务:
  - 交割数据、交割配对、仓单、交割费用、仓库升贴水
  - 一次性交割卖方仓单、滚动交割卖方意向
  - 交割结算价、保税交割结算价
  - 胶合板交割商品、纤维板厂库自报换货差价
- 错误处理

运行前请设置环境变量:
    export DCE_API_KEY="your-api-key"
    export DCE_SECRET="your-secret"

然后运行:
    python examples/complete.py
"""

import sys
import time
from pathlib import Path

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
    ContractStatRequest,
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
    ValidationError,
    VarietyMonthYearStatRequest,
    WarehouseReceiptRequest,
)


class DCEAPIDemo:
    """DCE API 演示类."""

    def __init__(self):
        """初始化演示."""
        self.client = self._create_client()
        self.trade_date = self._get_trade_date()
        self.trade_month = self.trade_date[:6]  # YYYYMM

    def _create_client(self) -> Client:
        """创建客户端."""
        try:
            client = Client.from_env()
            print("✓ 客户端创建成功")
            return client
        except ValidationError as e:
            print(f"✗ 配置错误: {e}")
            print("\n请设置以下环境变量:")
            print("  export DCE_API_KEY='your-api-key'")
            print("  export DCE_SECRET='your-secret'")
            sys.exit(1)

    def _get_trade_date(self) -> str:
        """获取当前交易日期."""
        try:
            result = self.client.common.get_curr_trade_date()
            print(f"✓ 当前交易日期: {result.trade_date}")
            return result.trade_date
        except Exception:
            # 如果获取失败，使用当前日期
            from datetime import datetime
            fallback = datetime.now().strftime("%Y%m%d")
            print(f"⚠ 无法获取交易日期，使用当前日期: {fallback}")
            return fallback

    def run_common_examples(self):
        """运行通用服务示例."""
        print("\n" + "=" * 60)
        print("CommonService 通用服务示例")
        print("=" * 60)

        # 获取当前交易日期（已在初始化时获取）
        print("\n--- GetCurrTradeDate 获取当前交易日期 ---")
        print(f"当前交易日期: {self.trade_date}")

        # 获取期货品种
        try:
            print("\n--- GetVarietyList 获取品种列表 ---")
            varieties = self.client.common.get_variety_list(trade_type=1)
            print(f"品种数量: {len(varieties)}")
            for i, v in enumerate(varieties):
                if i >= 5:
                    print(f"  ... 还有 {len(varieties) - 5} 个品种")
                    break
                print(f"  - {v.variety_name} ({v.variety_id}) - {v.variety_type}")
        except Exception as e:
            print(f"错误: {e}")

    def run_news_examples(self):
        """运行资讯服务示例."""
        print("\n" + "=" * 60)
        print("NewsService 资讯服务示例")
        print("=" * 60)

        # 获取交易所公告
        try:
            print("\n--- GetArticleByPage 获取交易所公告 (columnId=244) ---")
            req = GetArticleByPageRequest(
                column_id="244",  # 交易所公告
                page_no=1,
                page_size=5,
                site_id=5
            )
            result = self.client.news.get_article_by_page(req)
            print(f"总文章数: {result.total_count}, 当前页: {len(result.result_list)} 篇")
            for article in result.result_list:
                print(f"  - [{article.show_date}] {article.title}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取交易所通知
        try:
            print("\n--- GetArticleByPage 获取交易所通知 (columnId=245) ---")
            req = GetArticleByPageRequest(
                column_id="245",  # 交易所通知
                page_no=1,
                page_size=3,
                site_id=5
            )
            result = self.client.news.get_article_by_page(req)
            print(f"总通知数: {result.total_count}")
            for article in result.result_list:
                print(f"  - [{article.show_date}] {article.title}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取文章详情
        try:
            print("\n--- GetArticleDetail 获取文章详情 ---")
            # 首先获取一篇文章的ID
            req = GetArticleByPageRequest(
                column_id="244",
                page_no=1,
                page_size=1,
                site_id=5
            )
            result = self.client.news.get_article_by_page(req)
            if result.result_list:
                article_id = result.result_list[0].id
                print(f"  获取文章ID: {article_id}")
                detail = self.client.news.get_article_detail(article_id)
                print(f"  标题: {detail.title}")
                print(f"  发布时间: {detail.release_date or detail.show_date}")
                content_preview = detail.content[:100] if detail.content else ""
                print(f"  内容预览: {content_preview}...")
            else:
                print("  没有找到文章")
        except Exception as e:
            print(f"错误: {e}")

    def run_market_examples(self):
        """运行行情服务示例."""
        print("\n" + "=" * 60)
        print("MarketService 行情服务示例")
        print("=" * 60)

        print(f"使用交易日期: {self.trade_date}")

        # 获取日行情
        try:
            print(f"\n--- GetDayQuotes 获取日行情 (豆粕 m) ---")
            req = QuotesRequest(
                variety_id="m",
                trade_date=self.trade_date,
                trade_type="1",
                lang="zh"
            )
            quotes = self.client.market.get_day_quotes(req)
            print(f"豆粕日行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                if not q.contract_id or q.variety == "总计":
                    continue
                if count >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {q.contract_id} | 开: {q.open} 高: {q.high} "
                      f"低: {q.low} 收: {q.close} | 成交量: {q.volume}")
                count += 1
        except Exception as e:
            print(f"错误: {e}")

        # 获取夜盘行情
        try:
            print(f"\n--- GetNightQuotes 获取夜盘行情 (铁矿石 i) ---")
            req = QuotesRequest(
                variety="i",
                trade_date=self.trade_date,
                trade_type="1"
            )
            quotes = self.client.market.get_night_quotes(req)
            print(f"铁矿石夜盘行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                contract = q.deliv_month
                if not contract or q.variety == "总计":
                    continue
                if count >= 3:
                    break
                print(f"  合约: {contract} | 最新价: {q.last_price} | 持仓量: {q.open_interest}")
                count += 1
        except Exception as e:
            print(f"错误: {e}")

        # 获取周行情
        try:
            print(f"\n--- GetWeekQuotes 获取周行情 (豆粕 m) ---")
            req = QuotesRequest(
                variety_id="m",
                trade_date=self.trade_date,
                trade_type="1",
                lang="zh"
            )
            quotes = self.client.market.get_week_quotes(req)
            print(f"豆粕周行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                if not q.contract_id or q.variety == "总计":
                    continue
                if count >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {q.contract_id} | 周开: {q.open} 周收: {q.close} | "
                      f"成交量: {q.volume} | 日均持仓: {q.avg_open_interest}")
                count += 1
        except Exception as e:
            print(f"错误: {e}")

        # 获取月行情
        try:
            print(f"\n--- GetMonthQuotes 获取月行情 (玉米 c) ---")
            req = QuotesRequest(
                variety_id="c",
                trade_date=self.trade_date,
                trade_type="1",
                lang="zh"
            )
            quotes = self.client.market.get_month_quotes(req)
            print(f"玉米月行情, 合约数: {len(quotes)}")
            count = 0
            for q in quotes:
                if not q.contract_id or q.variety == "总计":
                    continue
                if count >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {q.contract_id} | 月开: {q.open} 月收: {q.close} | "
                      f"成交量: {q.volume} | 日均持仓: {q.avg_open_interest}")
                count += 1
        except Exception as e:
            print(f"错误: {e}")

        # 获取合约统计
        try:
            print(f"\n--- GetContractStat 获取合约统计 (豆粕 m2503) ---")
            req = ContractStatRequest(
                contract_code="m2503",
                start_date=self.trade_month[:4] + "0101",  # 年初
                end_date=self.trade_date
            )
            stats = self.client.market.get_contract_stat(req)
            print(f"合约统计数量: {len(stats)}")
            for i, s in enumerate(stats):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  合约: {s.contract_code} | 总成交量: {s.total_volume} | "
                      f"均价: {s.avg_price:.2f}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取合约最值统计（成交量）
        try:
            print(f"\n--- GetContractMonthMax 获取合约最值统计-成交量 ---")
            req = ContractMonthMaxRequest(
                start_month=self.trade_month,
                end_month=self.trade_month,
                stat_content="0",  # 0=成交量
                trade_type="1",
                lang="zh"
            )
            stats = self.client.market.get_contract_month_max(req)
            print(f"合约最值统计数量: {len(stats)}")
            for i, s in enumerate(stats):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  合约: {s.contract_id} | 总成交量: {s.sum_amount} | "
                      f"最大成交量: {s.max_amount} ({s.max_amount_date})")
        except Exception as e:
            print(f"错误: {e}")

        # 获取品种月度统计
        try:
            print(f"\n--- GetVarietyMonthYearStat 获取品种月度统计 ---")
            req = VarietyMonthYearStatRequest(
                trade_month=self.trade_month,
                trade_type="1",
                lang="zh"
            )
            stats = self.client.market.get_variety_month_year_stat(req)
            print(f"品种月度统计数量: {len(stats)}")
            for i, s in enumerate(stats):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  品种: {s.variety} | 本月成交量: {s.this_month_volumn} | "
                      f"同比: {s.volumn_balance}%")
        except Exception as e:
            print(f"错误: {e}")

        # 获取合约停板查询
        try:
            print(f"\n--- GetRiseFallEvent 获取合约停板查询 ---")
            req = RiseFallEventRequest(
                start_date=self.trade_month + "01",
                end_date=self.trade_date,
                variety_id="all",
                lang="zh"
            )
            events = self.client.market.get_rise_fall_event(req)
            print(f"停板事件数量: {len(events)}")
            for i, e in enumerate(events):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  日期: {e.trade_date} | 合约: {e.contract_id} | "
                      f"方向: {e.direction} | 次数: {e.times}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取分时结算参考价
        try:
            print(f"\n--- GetDivisionPriceInfo 获取分时结算参考价 ---")
            req = DivisionPriceInfoRequest(
                variety_id="a",
                trade_date=self.trade_date,
                trade_type="1"
            )
            prices = self.client.market.get_division_price_info(req)
            print(f"分时结算参考价数量: {len(prices)}")
            for i, p in enumerate(prices):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  时间: {p.calculate_time} | 合约: {p.contract_id} | "
                      f"结算价: {p.clear_price}")
        except Exception as e:
            print(f"错误: {e}")

    def run_trade_examples(self):
        """运行交易服务示例."""
        print("\n" + "=" * 60)
        print("TradeService 交易服务示例")
        print("=" * 60)

        # 获取日交易参数
        try:
            print("\n--- GetDayTradeParam 获取日交易参数 (豆粕 m) ---")
            req = DayTradeParamRequest(
                variety_id="m",
                trade_type="1",
                lang="zh"
            )
            params = self.client.trade.get_day_trade_param(req)
            print(f"日交易参数数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {p.contract_id} | 投机保证金率: {p.spec_buy_rate:.2%} | "
                      f"涨停: {p.rise_limit:.0f} | 跌停: {p.fall_limit:.0f}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取合约信息
        try:
            print("\n--- GetContractInfo 获取合约信息 (玉米 c) ---")
            req = ContractInfoRequest(
                variety_id="c",
                trade_type="1",
                lang="zh"
            )
            contracts = self.client.trade.get_contract_info(req)
            print(f"合约数量: {len(contracts)}")
            for i, c in enumerate(contracts):
                if i >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {c.contract_id} | 品种: {c.variety} | "
                      f"交易单位: {c.unit} | 最后交易日: {c.end_trade_date}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取套利合约
        try:
            print("\n--- GetArbitrageContract 获取套利合约 ---")
            contracts = self.client.trade.get_arbitrage_contract("zh")
            print(f"套利合约数量: {len(contracts)}")
            for i, a in enumerate(contracts):
                if i >= 3:
                    print("  ... 还有更多套利合约")
                    break
                print(f"  {a.arbi_name} | {a.variety_name} | "
                      f"{a.arbi_contract_id} | 最大手数: {a.max_hand}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取月交易参数
        try:
            print("\n--- GetMonthTradeParam 获取月交易参数 ---")
            response = self.client.trade.get_month_trade_param()
            print(f"月份: {response.month_date}")
            print(f"月交易参数数量: {len(response.list)}")
            for i, p in enumerate(response.list):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  合约: {p.contract_id} | 首日保证金率: {p.first_rate}% | "
                      f"15日保证金率: {p.fifteenth_rate}%")
        except Exception as e:
            print(f"错误: {e}")

        # 获取交易参数表（品种）
        try:
            print("\n--- GetTradingParam 获取交易参数表 ---")
            params = self.client.trade.get_trading_param()
            print(f"交易参数数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  品种: {p.variety_name} | 投机保证金率: {p.trading_margin_rate_speculation} | "
                      f"涨跌停板: {p.price_limit_existing_contract}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取套利交易保证金
        try:
            print("\n--- GetMarginArbiPerfPara 获取套利交易保证金 ---")
            params = self.client.trade.get_margin_arbi_perf_para("zh")
            print(f"套利交易保证金数量: {len(params)}")
            for i, p in enumerate(params):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  {p.arbi_name} | {p.variety_name} | {p.arbi_contract_id} | "
                      f"组合: {p.perf_sh_type} | 保证金: {p.margin_amt:.2f}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取新增合约信息
        try:
            print("\n--- GetNewContractInfo 获取新增合约信息 ---")
            req = NewContractInfoRequest(
                trade_date=self.trade_date,
                trade_type="1",
                lang="zh"
            )
            contracts = self.client.trade.get_new_contract_info(req)
            print(f"新增合约数量: {len(contracts)}")
            for i, c in enumerate(contracts):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  品种: {c.variety} | 合约: {c.contract_id} | "
                      f"开始交易日: {c.start_trade_date}")
        except Exception as e:
            print(f"错误: {e}")

        # 获取做市商持续报价合约
        try:
            print("\n--- GetMainSeriesInfo 获取做市商持续报价合约 ---")
            req = MainSeriesInfoRequest(
                variety_id="a",
                trade_date=self.trade_date
            )
            series = self.client.trade.get_main_series_info(req)
            print(f"做市商报价合约数量: {len(series)}")
            for i, s in enumerate(series):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  日期: {s.trade_date} | 系列: {s.series_id} | 合约: {s.contract_id}")
        except Exception as e:
            print(f"错误: {e}")

    def run_settle_examples(self):
        """运行结算服务示例."""
        print("\n" + "=" * 60)
        print("SettleService 结算服务示例")
        print("=" * 60)

        try:
            print("\n--- GetSettleParam 获取结算参数 (豆粕 m) ---")
            req = SettleParamRequest(
                variety_id="m",
                trade_date=self.trade_date,
                trade_type="1",
                lang="zh"
            )
            params = self.client.settle.get_settle_param(req)
            print(f"结算参数数量: {len(params)}")
            for i, s in enumerate(params):
                if i >= 3:
                    print("  ... 还有更多合约")
                    break
                print(f"  合约: {s.contract_id} | 结算价: {s.clear_price} | "
                      f"投机买保证金率: {s.spec_buy_rate} | 开仓手续费: {s.open_fee}")
        except Exception as e:
            print(f"错误: {e}")

    def run_member_examples(self):
        """运行会员服务示例."""
        print("\n" + "=" * 60)
        print("MemberService 会员服务示例")
        print("=" * 60)

        try:
            print("\n--- GetDailyRanking 获取日成交持仓排名 (豆一 a) ---")
            req = DailyRankingRequest(
                variety_id="a",
                contract_id="a2505",
                trade_date=self.trade_date,
                trade_type="1"
            )
            ranking = self.client.member.get_daily_ranking(req)
            
            # 成交量排名
            if ranking.qty_future_list:
                print("成交量排名 (前3):")
                for i, r in enumerate(ranking.qty_future_list):
                    if i >= 3:
                        break
                    print(f"  {r.rank}. {r.qty_abbr} | 成交量: {r.today_qty} | "
                          f"增减: {r.qty_sub:+d}")
            
            # 持买排名
            if ranking.buy_future_list:
                print("持买排名 (前3):")
                for i, r in enumerate(ranking.buy_future_list):
                    if i >= 3:
                        break
                    print(f"  {r.rank}. {r.buy_abbr} | 持买量: {r.today_buy_qty} | "
                          f"增减: {r.buy_sub:+d}")
        except Exception as e:
            print(f"错误: {e}")

        try:
            print("\n--- GetPhaseRanking 获取阶段成交排名 (豆一 a) ---")
            req = PhaseRankingRequest(
                variety="a",
                start_month=self.trade_month,
                end_month=self.trade_month,
                trade_type="1"
            )
            rankings = self.client.member.get_phase_ranking(req)
            print(f"阶段排名数量: {len(rankings)}")
            for i, r in enumerate(rankings):
                if i >= 3:
                    print("  ... 还有更多")
                    break
                print(f"  {r.seq}. {r.member_name} | 月成交量: {r.month_qty:.0f} | "
                      f"占比: {r.qty_ratio:.2f}%")
        except Exception as e:
            print(f"错误: {e}")

    def run_delivery_examples(self):
        """运行交割服务示例."""
        print("\n" + "=" * 60)
        print("DeliveryService 交割服务示例")
        print("=" * 60)

        print("\n注意: 交割服务的部分接口可能需要特定权限或参数格式")

        try:
            print("\n--- GetDeliveryData 获取交割数据 (豆一 a) ---")
            print("  (交割数据接口可能需要特定权限)")
            req = DeliveryDataRequest(
                variety_id="a",
                start_month=self.trade_month[:4] + "01",  # 年初
                end_month=self.trade_month,
                variety_type="0"  # 0=实物交割数据, 1=月均价交割数据
            )
            data = self.client.delivery.get_delivery_data(req)
            print(f"  交割数据数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {d.variety} | 合约: {d.contract_id} | "
                      f"交割日期: {d.delivery_date} | 交割量: {d.delivery_qty}")
        except Exception as e:
            print(f"  错误: {e}")

        try:
            print("\n--- GetDeliveryMatch 获取交割配对 (豆二 b) ---")
            print("  (交割配对接口可能需要特定权限)")
            req = DeliveryMatchRequest(
                variety_id="b",
                contract_id="all",
                start_month=self.trade_month[:4] + "01",  # 年初
                end_month=self.trade_month
            )
            matches = self.client.delivery.get_delivery_match(req)
            print(f"  交割配对数量: {len(matches)}")
            for i, m in enumerate(matches):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    合约: {m.contract_id} | 配对日期: {m.match_date} | "
                      f"买方: {m.buy_member_id} | 卖方: {m.sell_member_id} | "
                      f"配对手数: {m.delivery_qty}")
        except Exception as e:
            print(f"  错误: {e}")

        try:
            print("\n--- GetWarehouseReceipt 获取仓单日报 (豆一 a) ---")
            print("  (仓单数据接口可能需要特定权限)")
            req = WarehouseReceiptRequest(
                variety_id="a",
                trade_date=self.trade_date
            )
            response = self.client.delivery.get_warehouse_receipt(req)
            print(f"  仓单数据数量: {len(response.entity_list)}")
            for i, r in enumerate(response.entity_list):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {r.variety} | 仓库: {r.wh_abbr} | "
                      f"今日仓单量: {r.wbill_qty} | 增减: {r.diff}")
        except Exception as e:
            print(f"  错误: {e}")

        try:
            print("\n--- GetDeliveryCost 获取交割费用标准 (豆一 a) ---")
            print("  (交割费用接口可能需要特定权限)")
            costs = self.client.delivery.get_delivery_cost("a", variety_type="0")
            print(f"  交割费用数量: {len(costs)}")
            for i, cost in enumerate(costs):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {cost.variety} | 交割费: {cost.delivery_fee} | "
                      f"仓储费: {cost.fee_rate} | 定金率: {cost.earnest_rate}")
        except Exception as e:
            print(f"  错误: {e}")

        try:
            print("\n--- GetWarehousePremium 获取仓库升贴水 (玉米 c) ---")
            print("  (仓库升贴水接口可能需要特定权限)")
            response = self.client.delivery.get_warehouse_premium("c", self.trade_date)
            print(f"  仓库升贴水数量: {len(response.entity_list)}")
            for i, p in enumerate(response.entity_list):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {p.variety_name} | 仓库: {p.wh_name} | "
                      f"升贴水: {p.avg_agio}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取一次性交割卖方仓单查询
        try:
            print("\n--- GetTcCongregateDelivery 获取一次性交割卖方仓单 ---")
            req = TcCongregateDeliveryRequest(
                variety="all",
                contract_month=self.trade_month
            )
            data = self.client.delivery.get_tc_congregate_delivery(req)
            print(f"  一次性交割卖方仓单数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {d.variety_name} | 合约: {d.contract} | "
                      f"仓库: {d.warehouse_name} | 数量: {d.wbill_quantity}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取滚动交割卖方交割意向表
        try:
            print("\n--- GetRollDeliverySellerIntention 获取滚动交割卖方意向 ---")
            req = RollDeliverySellerIntentionRequest(
                variety="all",
                date=self.trade_date
            )
            data = self.client.delivery.get_roll_delivery_seller_intention(req)
            print(f"  滚动交割卖方意向数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    品种: {d.variety_name} | 合约: {d.contract} | "
                      f"仓库: {d.warehouse_name} | 数量: {d.quantity}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取交割结算价
        try:
            print("\n--- GetBondedDelivery 获取交割结算价 ---")
            req = BondedDeliveryRequest(
                start_date=self.trade_month + "01",
                end_date=self.trade_date
            )
            data = self.client.delivery.get_bonded_delivery(req)
            print(f"  交割结算价数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    日期: {d.delivery_date} | 品种: {d.variety_id} | "
                      f"合约: {d.contract_id} | 结算价: {d.delivery_price}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取保税交割结算价
        try:
            print("\n--- GetTdBondedDelivery 获取保税交割结算价 ---")
            req = BondedDeliveryRequest(
                start_date=self.trade_month + "01",
                end_date=self.trade_date
            )
            data = self.client.delivery.get_td_bonded_delivery(req)
            print(f"  保税交割结算价数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    日期: {d.delivery_date} | 品种: {d.variety_id} | "
                      f"合约: {d.contract_id} | 保税价: {d.bonded_delivery_price}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取胶合板交割商品
        try:
            print("\n--- GetPlywoodDeliveryCommodity 获取胶合板交割商品 ---")
            data = self.client.delivery.get_plywood_delivery_commodity()
            print(f"  胶合板交割商品数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    仓库: {d.wh_name} | 文件: {d.upload_file_name}")
        except Exception as e:
            print(f"  错误: {e}")

        # 获取纤维板厂库自报换货差价
        try:
            print("\n--- GetFactorySpotAgioQuotes 获取纤维板厂库自报换货差价 ---")
            data = self.client.delivery.get_factory_spot_agio_quotes()
            print(f"  换货差价数量: {len(data)}")
            for i, d in enumerate(data):
                if i >= 3:
                    print("    ... 还有更多")
                    break
                print(f"    序号: {d.seq_no} | 仓库: {d.wh_abbr} | "
                      f"品种: {d.variety_name}")
        except Exception as e:
            print(f"  错误: {e}")

    def run_error_handling_examples(self):
        """运行错误处理示例."""
        print("\n" + "=" * 60)
        print("错误处理示例")
        print("=" * 60)

        # 1. 验证错误
        print("\n1. 验证错误示例...")
        try:
            config = Config(api_key="", secret="test")
        except ValidationError as e:
            print(f"   ✓ 捕获验证错误: {e.field} - {e.message}")

        # 2. 无效的 columnId
        print("\n2. 无效参数示例...")
        try:
            req = GetArticleByPageRequest(
                column_id="999",  # 无效的 columnId
                page_no=1,
                page_size=10
            )
            self.client.news.get_article_by_page(req)
        except ValidationError as e:
            print(f"   ✓ 捕获验证错误: {e.message}")

    def run_all(self):
        """运行所有示例."""
        print("\nDCE API Python SDK - 完整功能演示")
        print("=" * 60)
        
        self.run_common_examples()
        time.sleep(3)
        self.run_news_examples()
        time.sleep(3)
        self.run_market_examples()
        time.sleep(3)
        self.run_trade_examples()
        time.sleep(3)
        self.run_settle_examples()
        time.sleep(3)
        self.run_member_examples()
        time.sleep(3)
        self.run_delivery_examples()
        time.sleep(3)
        self.run_error_handling_examples()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)


def main():
    """主函数."""
    demo = DCEAPIDemo()
    demo.run_all()


if __name__ == "__main__":
    main()
