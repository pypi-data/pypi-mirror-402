"""
Test script to find available data by trying recent dates.
"""

import os
from datetime import datetime, timedelta

import cryptohftdata as chd


def test_recent_dates():
    """Test with more recent dates to find available data."""

    # Set up API key
    api_key = "219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a"

    print("Testing recent dates to find available data...")
    print(f"API Key: {api_key[:10]}...")

    # Initialize client
    client = chd.CryptoHFTDataClient(api_key=api_key)

    # Test parameters
    symbol = "BTCUSDT"
    exchange = "binance_futures"

    # Try last 7 days
    today = datetime.now()
    for i in range(1, 8):
        test_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")

        print(f"\nTesting date: {test_date}")

        try:
            # Test just one hour to be quick
            file_path = client._generate_file_path(
                exchange, symbol, "klines", test_date, 0
            )
            print(f"  Testing file: {file_path}")

            df = client._download_single_file(file_path)
            if df is not None:
                print(f"  ✅ Found data! {len(df)} records")

                # Now try full day download
                print(f"  Downloading full day...")
                full_df = client.get_trades(
                    symbol=symbol,
                    exchange=exchange,
                    start_date=test_date,
                    end_date=test_date,
                )

                if not full_df.empty:
                    print(f"  ✅ Full day download successful: {len(full_df)} records")
                    print(f"  Columns: {list(full_df.columns)}")
                    if hasattr(full_df, "index") and len(full_df) > 0:
                        print(f"  Sample data shape: {full_df.shape}")
                        print(f"  First few rows:\n{full_df.head()}")
                    return test_date

            else:
                print(f"  ❌ No data found")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\nNo data found in recent dates.")
    return None


def test_single_file_download():
    """Test downloading a single file to debug the API response."""
    api_key = "219e71098264d5cda7f1ffa78b2145d790c51f2ea3af93e5129c7ce0c2e5d21a"
    client = chd.CryptoHFTDataClient(api_key=api_key)

    # Test a specific file path
    file_path = "binance_futures/2024-12-20/00/BTCUSDT_klines.parquet.zst"

    print(f"Testing specific file: {file_path}")

    import requests

    url = f"{client.download_endpoint}?file={file_path}&api_key={api_key}"
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print(f"Content Length: {len(response.content)} bytes")
        else:
            print(f"Response Text: {response.text}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("=== Testing Single File Download ===")
    test_single_file_download()

    print("\n\n=== Testing Recent Dates ===")
    found_date = test_recent_dates()

    if found_date:
        print(f"\n🎉 Successfully found data for {found_date}")
    else:
        print(
            "\n⚠️  No recent data found. The API might not have data for recent dates or the file structure might be different."
        )
