import os
import unittest
from datetime import datetime, timedelta, timezone  # Added timezone
import pandas as pd
from cryptohftdata import CryptoHFTDataClient, DataType


class TestFundingRates(unittest.TestCase):
    def setUp(self):
        self.api_key = os.environ.get("CRYPTOHFTDATA_API_KEY")
        self.client = CryptoHFTDataClient(api_key=self.api_key)
        # Use timezone-aware datetime objects
        self.start_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )
        self.end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

    def test_get_funding_rates_binance_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_funding_rates(
            symbol="BTCUSDT",
            exchange="binance_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertIn("timestamp", data.columns)
        self.assertIn("funding_rate", data.columns)
        self.assertIn("funding_time", data.columns)
        # Check if data is within the requested date range
        self.assertTrue(
            (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
        )
        self.assertTrue(
            (
                data["timestamp"]
                < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
            ).all()
        )

    def test_get_funding_rates_bybit_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_funding_rates(
            symbol="BTCUSDT",
            exchange="bybit_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertIn("timestamp", data.columns)
        self.assertIn("funding_rate", data.columns)
        self.assertIn("funding_time", data.columns)
        self.assertTrue(
            (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
        )
        self.assertTrue(
            (
                data["timestamp"]
                < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
            ).all()
        )

    def test_get_funding_rates_limit(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_funding_rates(
            symbol="BTCUSDT",
            exchange="binance_futures",
            start_date=self.start_date,
            end_date=self.end_date,
            limit=5,
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertEqual(len(data), 5)


if __name__ == "__main__":
    unittest.main()
