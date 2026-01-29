import os
import unittest
from datetime import datetime, timedelta, timezone  # Added timezone

import pandas as pd

from cryptohftdata import CryptoHFTDataClient, DataType


class TestLiquidations(unittest.TestCase):
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

    def test_get_liquidations_binance_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_liquidations(
            symbol="BTCUSDT",
            exchange="binance_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        # Liquidations can be sparse, so data might be empty for a short range
        if not data.empty:
            self.assertIn("timestamp", data.columns)
            self.assertIn("side", data.columns)
            self.assertIn("quantity", data.columns)
            self.assertIn("price", data.columns)
            self.assertTrue(
                (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
            )
            self.assertTrue(
                (
                    data["timestamp"]
                    < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
                ).all()
            )
        else:
            print(
                f"No liquidations data for binance_futures BTCUSDT {self.start_date} to {self.end_date}"
            )

    def test_get_liquidations_bybit_futures(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        data = self.client.get_liquidations(
            symbol="BTCUSDT",
            exchange="bybit_futures",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.assertIsInstance(data, pd.DataFrame)
        if not data.empty:
            self.assertIn("timestamp", data.columns)
            self.assertIn("side", data.columns)
            self.assertIn("quantity", data.columns)
            self.assertIn("price", data.columns)
            self.assertTrue(
                (data["timestamp"] >= pd.to_datetime(self.start_date, utc=True)).all()
            )
            self.assertTrue(
                (
                    data["timestamp"]
                    < pd.to_datetime(self.end_date, utc=True) + pd.Timedelta(days=1)
                ).all()
            )
        else:
            print(
                f"No liquidations data for bybit_futures BTCUSDT {self.start_date} to {self.end_date}"
            )

    def test_get_liquidations_limit(self):
        if not self.api_key:
            self.skipTest("API key not found.")
        # Use a longer historical range to increase chance of getting liquidation data
        long_start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )
        long_end_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d"
        )
        data = self.client.get_liquidations(
            symbol="ETHUSDT",
            exchange="binance_futures",
            start_date=long_start_date,
            end_date=long_end_date,
            limit=5,
        )
        self.assertIsInstance(data, pd.DataFrame)
        if not data.empty:
            self.assertLessEqual(len(data), 5)
        else:
            print(
                f"No liquidations data for binance_futures ETHUSDT {long_start_date} to {long_end_date} with limit 5"
            )


if __name__ == "__main__":
    unittest.main()
