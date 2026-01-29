#!/usr/bin/env python3
"""
Comprehensive test of mark_price functionality demonstrating both client method and convenience function.
"""

import os
import sys

from cryptohftdata import (
    CryptoHFTDataClient,
    configure_client,
    exchanges,
    get_mark_price,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_mark_price_comprehensive():
    """Test mark_price using both client and convenience function approaches."""

    print("🚀 Testing mark_price functionality")
    print("=" * 60)

    # Configure the global client for convenience functions
    configure_client(
        api_key="219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a",
    )
    print("✅ Global client configured")

    # Test parameters
    symbol = "BTCUSDT"
    start_date = "2024-06-09"
    end_date = "2024-06-09"

    print(f"\n📊 Testing with symbol: {symbol}, date: {start_date}")

    # Test 1: Using client method directly
    print(f"\n1️⃣  Testing client.get_mark_price() with {exchanges.BINANCE_FUTURES}")
    try:
        client = CryptoHFTDataClient(
            api_key="219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a",
        )

        df = client.get_mark_price(
            symbol=symbol,
            exchange=exchanges.BINANCE_FUTURES,
            start_date=start_date,
            end_date=end_date,
        )

        print(f"   ✅ Success: {len(df)} records retrieved")
        if len(df) > 0:
            print(f"   📋 Columns: {df.columns.tolist()}")
            print(f"   🕐 Time range: {df.index[0]} to {df.index[-1]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 2: Using convenience function
    print(
        f"\n2️⃣  Testing get_mark_price() convenience function with {exchanges.BYBIT_FUTURES}"
    )
    try:
        df = get_mark_price(
            symbol=symbol,
            exchange=exchanges.BYBIT_FUTURES,
            start_date=start_date,
            end_date=end_date,
        )

        print(f"   ✅ Success: {len(df)} records retrieved")
        if len(df) > 0:
            print(f"   📋 Columns: {df.columns.tolist()}")
            print(f"   🕐 Time range: {df.index[0]} to {df.index[-1]}")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Test 3: Test with spot exchange (should return empty data)
    print(f"\n3️⃣  Testing with spot exchange {exchanges.BINANCE_SPOT} (should be empty)")
    try:
        df = get_mark_price(
            symbol=symbol,
            exchange=exchanges.BINANCE_SPOT,
            start_date=start_date,
            end_date=end_date,
        )

        if len(df) == 0:
            print("   ✅ Correctly returned empty data for spot exchange")
        else:
            print(f"   ⚠️  Unexpectedly found {len(df)} records on spot exchange")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    print(f"\n🎉 Mark price testing completed!")


if __name__ == "__main__":
    test_mark_price_comprehensive()
