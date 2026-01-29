#!/usr/bin/env python3
"""
Test script for mark_price functionality with actual API calls.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from cryptohftdata import CryptoHFTDataClient, exchanges


def test_mark_price():
    """Test mark_price functionality on futures exchanges."""

    # Create client with the working API key
    client = CryptoHFTDataClient(
        api_key="219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a"
    )

    print("Testing mark_price functionality...")
    print("=" * 50)

    # Test parameters
    symbol = "BTCUSDT"
    start_date = "2025-01-09"  # Recent date with data
    end_date = "2025-01-09"

    # Test with Binance Futures
    print(f"\n1. Testing {exchanges.BINANCE_FUTURES}")
    try:
        df = client.get_mark_price(
            symbol=symbol,
            exchange=exchanges.BINANCE_FUTURES,
            start_date=start_date,
            end_date=end_date,
        )

        if len(df) > 0:
            print(f"✅ Successfully retrieved {len(df)} mark_price records")
            print(f"Columns: {list(df.columns)}")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            print(f"Sample data:")
            print(df.head())
        else:
            print("⚠️  No data found, but API call succeeded")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test with Bybit Futures
    print(f"\n2. Testing {exchanges.BYBIT_FUTURES}")
    try:
        df = client.get_mark_price(
            symbol=symbol,
            exchange=exchanges.BYBIT_FUTURES,
            start_date=start_date,
            end_date=end_date,
        )

        if len(df) > 0:
            print(f"✅ Successfully retrieved {len(df)} mark_price records")
            print(f"Columns: {list(df.columns)}")
            print(f"Date range: {df.index[0]} to {df.index[-1]}")
            print(f"Sample data:")
            print(df.head())
        else:
            print("⚠️  No data found, but API call succeeded")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test with spot exchange (should have no data)
    print(f"\n3. Testing {exchanges.BINANCE_SPOT} (should have no mark_price data)")
    try:
        df = client.get_mark_price(
            symbol=symbol,
            exchange=exchanges.BINANCE_SPOT,
            start_date=start_date,
            end_date=end_date,
        )

        if len(df) > 0:
            print(
                f"⚠️  Unexpectedly found {len(df)} mark_price records on spot exchange"
            )
        else:
            print("✅ No data found on spot exchange (as expected)")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_mark_price()
