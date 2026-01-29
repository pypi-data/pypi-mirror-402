#!/usr/bin/env python3
"""
Test mark_price with known working date.
"""
import os
import sys
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("1. Starting test...")

    from cryptohftdata import CryptoHFTDataClient, exchanges

    print("2. Imports successful")

    # Use same API key that worked for other tests
    client = CryptoHFTDataClient(
        api_key="219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a",
    )
    print("3. Client created")

    # Use a date we know has data from previous tests
    print("4. Testing mark_price on binance_futures...")
    df = client.get_mark_price(
        symbol="BTCUSDT",
        exchange="binance_futures",
        start_date="2024-06-09",  # Use a known working date
        end_date="2024-06-09",
    )

    print(f"5. ✅ Retrieved {len(df)} mark_price records")

    if len(df) > 0:
        print(f"Columns: {df.columns.tolist()}")
        print("First few rows:")
        print(df.head())
    else:
        print("No data found for this date/symbol combination")

except Exception as e:
    print(f"❌ Error occurred: {e}")
    print("Full traceback:")
    traceback.print_exc()
