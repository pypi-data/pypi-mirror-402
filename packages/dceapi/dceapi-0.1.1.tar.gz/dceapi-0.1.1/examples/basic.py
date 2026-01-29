"""DCE API Python SDK - 基本示例.

演示如何使用 dceapi-py SDK 的基本功能。

运行前请设置环境变量:
    export DCE_API_KEY="your-api-key"
    export DCE_SECRET="your-secret"

然后运行:
    python examples/basic.py
"""

import sys
from pathlib import Path

# 添加 src 目录到 Python 路径（用于开发环境）
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dceapi import (
    APIError,
    AuthError,
    Client,
    Config,
    NetworkError,
    QuotesRequest,
    ValidationError,
)


def create_client_from_env():
    """从环境变量创建客户端（推荐）."""
    try:
        client = Client.from_env()
        print("✓ 客户端创建成功（从环境变量）")
        return client
    except ValidationError as e:
        print(f"✗ 验证错误: {e}")
        print("\n请设置以下环境变量:")
        print("  export DCE_API_KEY='your-api-key'")
        print("  export DCE_SECRET='your-secret'")
        sys.exit(1)


def create_client_with_config():
    """使用配置对象创建客户端."""
    config = Config(
        api_key="your-api-key",
        secret="your-secret",
        base_url="http://www.dce.com.cn",
        timeout=30.0,
        lang="zh",
        trade_type=1,
    )
    client = Client(config)
    print("✓ 客户端创建成功（使用配置）")
    return client


def example_get_trade_date(client: Client):
    """示例 1: 获取当前交易日期."""
    print("\n=== 示例 1: 获取当前交易日期 ===")
    try:
        trade_date = client.common.get_curr_trade_date()
        print(f"当前交易日期: {trade_date.trade_date}")
    except APIError as e:
        print(f"API 错误: {e}")
    except NetworkError as e:
        print(f"网络错误: {e}")


def example_get_variety_list(client: Client):
    """示例 2: 获取品种列表."""
    print("\n=== 示例 2: 获取品种列表 ===")
    try:
        # 获取期货品种
        varieties = client.common.get_variety_list(trade_type=1)
        print(f"期货品种数量: {len(varieties)}")
        
        # 显示前 5 个品种
        print("\n前 5 个品种:")
        for variety in varieties[:5]:
            print(f"  - {variety.variety_id}: {variety.variety_name} ({variety.variety_english_name})")
    except APIError as e:
        print(f"API 错误: {e}")
    except NetworkError as e:
        print(f"网络错误: {e}")


def example_get_day_quotes(client: Client):
    """示例 3: 获取日行情."""
    print("\n=== 示例 3: 获取日行情 ===")
    try:
        # 首先获取当前交易日期
        trade_date = client.common.get_curr_trade_date()
        
        # 获取玉米（c）的日行情
        req = QuotesRequest(
            variety_id="c",
            trade_date=trade_date.trade_date,
            trade_type="1"
        )
        quotes = client.market.get_day_quotes(req)
        
        print(f"玉米行情数量: {len(quotes)}")
        
        # 显示前 3 个合约
        print("\n前 3 个合约:")
        for quote in quotes[:3]:
            print(f"  - {quote.contract_id}: 最新价 {quote.last_price}, "
                  f"开盘 {quote.open}, 收盘 {quote.close}")
    except APIError as e:
        print(f"API 错误: {e}")
    except NetworkError as e:
        print(f"网络错误: {e}")


def example_error_handling():
    """示例 4: 错误处理."""
    print("\n=== 示例 4: 错误处理 ===")
    
    # 故意使用无效配置
    try:
        config = Config(api_key="", secret="invalid")
    except ValidationError as e:
        print(f"✓ 捕获验证错误: {e}")


def main():
    """主函数."""
    print("DCE API Python SDK - 基本示例")
    print("=" * 50)
    
    # 创建客户端
    client = create_client_from_env()
    
    # 运行示例
    example_get_trade_date(client)
    example_get_variety_list(client)
    example_get_day_quotes(client)
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("示例运行完成！")


if __name__ == "__main__":
    main()
