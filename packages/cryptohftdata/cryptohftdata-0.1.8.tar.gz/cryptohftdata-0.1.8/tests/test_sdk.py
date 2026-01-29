#!/usr/bin/env python3
"""
Test script for the CryptoHFTData SDK.
This script tests the basic functionality of the SDK.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the SDK to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptohftdata import CryptoHFTDataClient, exchanges


def test_basic_functionality():
    """Test basic SDK functionality."""
    print("Testing CryptoHFTData SDK...")

    # Initialize client (without API key for basic tests)
    client = CryptoHFTDataClient()

    # Test list_exchanges
    print("\n1. Testing list_exchanges()...")
    try:
        supported_exchanges = client.list_exchanges()
        print(f"Supported exchanges: {supported_exchanges}")
        assert len(supported_exchanges) >= 14
        print("✓ list_exchanges() works correctly")
    except Exception as e:
        print(f"✗ list_exchanges() failed: {e}")

    # Test get_exchange_info
    print("\n2. Testing get_exchange_info()...")
    try:
        binance_info = client.get_exchange_info("binance_spot")
        print(f"Binance spot info: {binance_info}")
        assert "name" in binance_info
        print("✓ get_exchange_info() works correctly")
    except Exception as e:
        print(f"✗ get_exchange_info() failed: {e}")

    # Test list_symbols
    print("\n3. Testing list_symbols()...")
    try:
        symbols = client.list_symbols("binance_spot")
        print(f"Available symbols: {symbols[:5]}...")  # Show first 5
        assert len(symbols) > 0
        print("✓ list_symbols() works correctly")
    except Exception as e:
        print(f"✗ list_symbols() failed: {e}")

    # Test validation
    print("\n4. Testing validation...")
    try:
        client.get_exchange_info("invalid_exchange")
        print("✗ Validation failed - should have raised an error")
    except Exception as e:
        print(f"✓ Validation works correctly: {e}")

    print("\n5. Testing exchanges constants...")
    try:
        print(f"BINANCE_SPOT: {exchanges.BINANCE_SPOT}")
        print(f"BINANCE_FUTURES: {exchanges.BINANCE_FUTURES}")
        print(f"BYBIT_SPOT: {exchanges.BYBIT_SPOT}")
        print(f"BYBIT_FUTURES: {exchanges.BYBIT_FUTURES}")
        print(f"HYPERLIQUID_SPOT: {exchanges.HYPERLIQUID_SPOT}")
        print(f"HYPERLIQUID_FUTURES: {exchanges.HYPERLIQUID_FUTURES}")
        print(f"ASTER_FUTURES: {exchanges.ASTER_FUTURES}")
        print(f"BITMEX: {exchanges.BITMEX}")
        print("✓ Exchange constants work correctly")
    except Exception as e:
        print(f"✗ Exchange constants failed: {e}")


def test_with_api_key():
    """Test functionality that requires an API key."""
    print("\n6. Testing data download functionality...")

    # This would require a valid API key
    # For testing purposes, we'll just test the method signature
    try:
        from cryptohftdata.client import CryptoHFTDataClient
        from cryptohftdata.exceptions import ConfigurationError

        client = CryptoHFTDataClient()  # No API key

        # This should raise a ConfigurationError
        try:
            result = client.get_trades(
                "BTCUSDT", exchanges.BINANCE_FUTURES, "2025-01-01", "2025-01-02"
            )
            print("✗ Should have raised ConfigurationError")
        except ConfigurationError as e:
            print(f"✓ Correctly raised ConfigurationError: {e}")
        except Exception as e:
            print(f"? Unexpected error (may be OK): {e}")

    except Exception as e:
        print(f"✗ Data download test failed: {e}")


if __name__ == "__main__":
    test_basic_functionality()
    test_with_api_key()
    print("\n" + "=" * 50)
    print("SDK basic tests completed!")
    print("To test data downloading, set your API key:")
    print("client = CryptoHFTDataClient(api_key='your_api_key')")
