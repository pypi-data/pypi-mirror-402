"""
Test script to verify the SDK works with real API endpoints.
"""

import os
from datetime import datetime, timedelta

import cryptohftdata as chd


def test_real_api():
    """Test the SDK with real API calls."""

    # Set up API key
    api_key = os.getenv("CRYPTOHFTDATA_API_KEY")
    if not api_key:
        print("⚠️  No API key found. Set CRYPTOHFTDATA_API_KEY environment variable.")
        return

    chd.configure_client(
        api_key=api_key,
        base_url="https://your-api-domain.com/v1",  # Update with your actual API URL
    )

    # Test date range (last 24 hours)
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=24)

    try:
        print("Testing real API integration...")

        # Test 1: Binance Spot trades
        print("\n1. Testing Binance Spot trades...")
        trades = chd.get_trades(
            symbol="BTCUSDT",
            exchange=chd.exchanges.BINANCE_SPOT,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        print(f"   ✅ Got {len(trades)} trade records")
        print(f"   Columns: {list(trades.columns)}")

        # Test 2: Bybit Futures orderbook
        print("\n2. Testing Bybit Futures orderbook...")
        orderbook = chd.get_orderbook(
            symbol="ETHUSDT",
            exchange=chd.exchanges.BYBIT_FUTURES,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )
        print(f"   ✅ Got {len(orderbook)} orderbook snapshots")

        print("\n🎉 All tests passed! SDK is working correctly.")

    except chd.APIError as e:
        print(f"❌ API Error: {e}")
        print("   Check your API key and endpoint URL")
    except chd.ValidationError as e:
        print(f"❌ Validation Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")


if __name__ == "__main__":
    test_real_api()
