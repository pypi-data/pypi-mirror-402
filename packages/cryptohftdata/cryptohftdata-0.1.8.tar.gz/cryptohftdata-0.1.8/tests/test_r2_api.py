"""
Test script to verify the SDK works with the R2 file structure and real API.
Tests the specific date 2025-06-09 with symbol BTCUSDT for binance_futures.
"""

import logging
import os
from datetime import datetime

import cryptohftdata as chd

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")


def test_r2_api():
    """Test the SDK with R2 file structure and real API calls."""

    # Set up API key
    api_key = os.getenv("CRYPTOHFTDATA_API_KEY")
    if not api_key:
        print("⚠️  No API key found. Set CRYPTOHFTDATA_API_KEY environment variable.")
        return

    print("Testing R2 API integration...")
    print(f"API Key: {api_key[:10]}...")

    # Initialize client with the correct API base URL
    client = chd.CryptoHFTDataClient(api_key=api_key)

    # Test parameters - using a known past date
    test_date = "2025-06-09"
    symbol = "BTCUSDT"
    exchange = "binance_futures"

    print(f"\nTesting with:")
    print(f"  Date: {test_date}")
    print(f"  Symbol: {symbol}")
    print(f"  Exchange: {exchange}")

    try:
        # Test 1: Get klines data
        print(f"\n1. Testing klines download...")
        print(f"   Expected file paths for {test_date}:")

        # Show what file paths will be generated
        for hour in range(24):
            file_path = client._generate_file_path(
                exchange, symbol, "kline", test_date, hour
            )
            print(f"     Hour {hour:02d}: {file_path}")

        # Attempt to download trades
        trades_df = client.get_trades(
            symbol=symbol, exchange=exchange, start_date=test_date, end_date=test_date
        )

        if not trades_df.empty:
            print(f"   ✅ Successfully downloaded {len(trades_df)} trade records")
            print(f"   Columns: {list(trades_df.columns)}")
            if hasattr(trades_df, "index"):
                print(
                    f"   Date range: {trades_df.index.min()} to {trades_df.index.max()}"
                )
        else:
            print("   ⚠️  No trade data found for this date/symbol")

        # Test 2: Get orderbook data
        print(f"\n2. Testing orderbook download...")
        orderbook_df = client.get_orderbook(
            symbol=symbol, exchange=exchange, start_date=test_date, end_date=test_date
        )

        if not orderbook_df.empty:
            print(
                f"   ✅ Successfully downloaded {len(orderbook_df)} orderbook records"
            )
            print(f"   Columns: {list(orderbook_df.columns)}")
        else:
            print("   ⚠️  No orderbook data found for this date/symbol")

        # Test 3: Get orderbook data
        print(f"\n3. Testing orderbook download...")
        orderbook_df = client.get_orderbook(
            symbol=symbol, exchange=exchange, start_date=test_date, end_date=test_date
        )

        if not orderbook_df.empty:
            print(
                f"   ✅ Successfully downloaded {len(orderbook_df)} orderbook snapshots"
            )
            print(f"   Columns: {list(orderbook_df.columns)}")
        else:
            print("   ⚠️  No orderbook data found for this date/symbol")

        print(f"\n🎉 R2 API test completed successfully!")

    except chd.AuthenticationError as e:
        print(f"❌ Authentication Error: {e}")
        print("   Check your API key")
    except chd.ValidationError as e:
        print(f"❌ Validation Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()


def test_file_path_generation():
    """Test the file path generation logic."""
    print("\nTesting file path generation:")

    client = chd.CryptoHFTDataClient(api_key="test")

    # Test various file path generations
    test_cases = [
        ("binance_futures", "2024-12-01", 0, "BTCUSDT", "kline"),
        ("binance_futures", "2024-12-01", 12, "BTCUSDT", "trades"),
        ("binance_futures", "2024-12-01", 23, "BTCUSDT", "orderbook"),
        ("bybit_spot", "2024-01-15", 6, "ETHUSDT", "ticker"),
    ]

    for exchange, date, hour, symbol, data_type in test_cases:
        file_path = client._generate_file_path(exchange, symbol, data_type, date, hour)
        print(f"  {exchange}/{date}/{hour:02d}/{symbol}_{data_type} -> {file_path}")


if __name__ == "__main__":
    test_file_path_generation()
    test_r2_api()
