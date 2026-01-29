import os
import unittest
from datetime import datetime, timedelta, timezone  # Added timezone

import pandas as pd

from cryptohftdata import CryptoHFTDataClient, DataType


class TestOpenInterest(unittest.TestCase):
    def setUp(self):
        self.api_key = os.environ.get("CRYPTOHFTDATA_API_KEY")
        self.client = CryptoHFTDataClient(api_key=self.api_key)
        # Use a shorter, more recent period for open interest as it can be voluminous
        # Use timezone-aware datetime objects
        self.start_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime(
            "%Y-%m-%d"
        )
        self.end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )

    def test_get_open_interest_binance_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_open_interest(
            symbol="BTCUSDT",
            exchange="binance_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertIn("timestamp", data.columns)
        self.assertIn("open_interest", data.columns)
        self.assertTrue(
            (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
        )
        self.assertTrue(
            (
                data["timestamp"]
                < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
            ).all()
        )

    def test_get_open_interest_bybit_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_open_interest(
            symbol="BTCUSDT",
            exchange="bybit_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertIn("timestamp", data.columns)
        self.assertIn("open_interest", data.columns)
        self.assertTrue(
            (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
        )
        self.assertTrue(
            (
                data["timestamp"]
                < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
            ).all()
        )

    def test_get_open_interest_limit(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_open_interest(
            symbol="ETHUSDT",
            exchange="binance_futures",
            start_date=self.start_date,
            end_date=self.end_date,
            limit=100,  # Open interest data can be granular, so a slightly larger limit for testing
        )
        self.assertIsInstance(data, pd.DataFrame)
        self.assertFalse(data.empty)
        self.assertLessEqual(len(data), 100)


if __name__ == "__main__":
    unittest.main()
