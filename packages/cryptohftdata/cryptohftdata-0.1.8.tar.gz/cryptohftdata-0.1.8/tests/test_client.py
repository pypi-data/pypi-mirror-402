"""
Test cases for the main client functionality.
"""

from datetime import datetime, timezone
from unittest.mock import ANY, Mock, patch

import pandas as pd
import pytest
import zstandard as zstd

from cryptohftdata import CryptoHFTDataClient
from cryptohftdata.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ValidationError,
)


@pytest.fixture
def client():
    """Fixture to provide a CryptoHFTDataClient instance for tests."""
    return CryptoHFTDataClient(api_key="test-key")


class TestCryptoHFTDataClient:
    """Test cases for the CryptoHFTDataClient class."""

    def test_client_initialization(self):
        """Test client initialization with default parameters."""
        client = CryptoHFTDataClient()
        assert client.base_url == "https://api.cryptohftdata.com"
        assert client.timeout == 30
        assert client.max_retries == 3

    def test_client_initialization_with_params(self):
        """Test client initialization with custom parameters."""
        custom_client = CryptoHFTDataClient(
            api_key="test-key",
            base_url="https://test-api.com",
            timeout=60,
            max_retries=5,
        )
        assert custom_client.api_key == "test-key"
        assert custom_client.base_url == "https://test-api.com"
        assert custom_client.timeout == 60
        assert custom_client.max_retries == 5

    def test_get_trades_validation(self, client):
        """Test input validation for get_trades method."""
        with pytest.raises(ValidationError):
            client.get_trades("", "binance_spot", "2025-01-01", "2025-01-02")

        with pytest.raises(ValidationError):
            client.get_trades("BTCUSDT", "invalid_exchange", "2025-01-01", "2025-01-02")

        with pytest.raises(ValidationError):
            client.get_trades("BTCUSDT", "binance_spot", "2025-01-02", "2025-01-01")

        with pytest.raises(ValidationError):
            client.get_trades("BTCUSDT", "binance_spot", "invalid-date", "2025-01-02")

        with pytest.raises(ValidationError):
            client.get_trades("BTCUSDT", "binance_spot", "2025-01-01", "invalid-date")

    @patch("cryptohftdata.client.requests.get")
    def test_get_trades_success(self, mock_get, client):
        """Test successful get_trades call."""
        mock_response_content = b"PAR1..."  # Dummy Parquet content
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = mock_response_content
        mock_resp.headers = {"Content-Type": "application/octet-stream"}
        mock_get.return_value = mock_resp

        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_df = pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2025-01-01T00:00:00Z")],
                    "price": [45000.0],
                    "quantity": [1.5],
                    "side": ["buy"],
                }
            )
            mock_read_parquet.return_value = mock_df

            result = client.get_trades(
                "BTCUSDT",
                "binance_spot",
                "2025-01-01",  # Test with a single day to predict call count
                "2025-01-01",  # End date same as start for simplicity in call count
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) > 0
            assert mock_get.call_count > 0  # Check that requests.get was called
            mock_read_parquet.assert_called()  # Check that read_parquet was called

    @patch("cryptohftdata.client.requests.get")
    def test_get_orderbook_success(self, mock_get, client):
        """Test successful get_orderbook call."""
        mock_response_content = b"PAR1..."  # Dummy Parquet content
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = mock_response_content
        mock_resp.headers = {"Content-Type": "application/octet-stream"}
        mock_get.return_value = mock_resp

        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_df = pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2025-01-01T00:00:00Z")],
                    "side": ["bid"],
                    "level": [0],
                    "price": [45000.0],
                    "size": [1.5],
                }
            )
            mock_read_parquet.return_value = mock_df

            result = client.get_orderbook(
                "BTCUSDT", "binance_spot", "2025-01-01", "2025-01-01"
            )

            assert isinstance(result, pd.DataFrame)
            assert mock_get.call_count > 0
            mock_read_parquet.assert_called()

    @patch("cryptohftdata.client.requests.get")
    def test_get_trades_success(self, mock_get, client):
        """Test successful get_trades call."""
        mock_response_content = b"PAR1..."  # Dummy Parquet content
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = mock_response_content
        mock_resp.headers = {"Content-Type": "application/octet-stream"}
        mock_get.return_value = mock_resp

        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_df = pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2025-01-01T00:00:00Z")],
                    "trade_id": ["12345"],
                    "price": [45000.0],
                    "quantity": [0.1],
                    "side": ["buy"],
                }
            )
            mock_read_parquet.return_value = mock_df

            result = client.get_trades(
                "BTCUSDT", "binance_spot", "2025-01-01", "2025-01-01"
            )

            assert isinstance(result, pd.DataFrame)
            assert mock_get.call_count > 0
            mock_read_parquet.assert_called()

    @patch("cryptohftdata.client.requests.get")
    def test_get_ticker_success(self, mock_get, client):
        """Test successful get_ticker call."""
        mock_response_content = b"PAR1..."  # Dummy Parquet content
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.content = mock_response_content
        mock_resp.headers = {"Content-Type": "application/octet-stream"}
        mock_get.return_value = mock_resp

        with patch("pandas.read_parquet") as mock_read_parquet:
            mock_df = pd.DataFrame(
                {
                    "timestamp": [pd.Timestamp("2025-01-01T00:00:00Z")],
                    "open": [45000.0],
                    "high": [45100.0],
                    "low": [44900.0],
                    "close": [45050.0],
                    "volume": [150.0],
                }
            )
            mock_read_parquet.return_value = mock_df

            result = client.get_ticker(
                "BTCUSDT", "binance_spot", "2025-01-01", "2025-01-01"
            )

            assert isinstance(result, pd.DataFrame)
            assert mock_get.call_count > 0
            mock_read_parquet.assert_called()

    @patch("cryptohftdata.client.HTTPClient.get")
    def test_list_symbols(self, mock_http_get, client):
        """Test list_symbols method."""
        mock_http_get.return_value = {
            "exchange": "binance_spot",
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "count": 2,
        }

        result = client.list_symbols("binance_spot")

        mock_http_get.assert_called_once_with(
            "symbols", params={"exchange": "binance_spot"}
        )
        assert result == ["BTCUSDT", "ETHUSDT"]

    @patch("cryptohftdata.client.HTTPClient.get")
    def test_list_exchanges(self, mock_http_get, client):
        """Test list_exchanges method."""
        # Expected exchanges based on the hardcoded list in client.py
        expected_exchanges = [
            "binance_spot",
            "binance_futures",
            "bybit_spot",
            "bybit",
            "kraken_spot",
            "kraken_derivatives",
            "okx_spot",
            "okx_futures",
            "bitget_spot",
            "bitget_futures",
            "hyperliquid_spot",
            "hyperliquid_futures",
            "lighter",
            "aster_futures",
            "bitmex",
        ]

        result = client.list_exchanges()

        assert result == expected_exchanges

    def test_context_manager(self):
        """Test client as context manager."""
        with CryptoHFTDataClient(api_key="test-key") as client_cm:
            assert isinstance(client_cm, CryptoHFTDataClient)

    def test_download_single_file_requires_api_key(self):
        client_no_key = CryptoHFTDataClient()
        with pytest.raises(
            ConfigurationError, match="API key is required for downloading data"
        ):
            client_no_key.get_trades(
                "BTCUSDT", "binance_spot", "2023-01-01", "2023-01-01"
            )

    @patch("cryptohftdata.client.requests.get")
    def test_download_single_file_handles_404(self, mock_get, client):
        mock_resp = Mock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result_df = client.get_trades(
            "BTCUSDT", "binance_spot", "2023-01-01", "2023-01-01"
        )
        assert result_df.empty
        assert mock_get.call_count == 24

    @patch("cryptohftdata.client.requests.get")
    def test_download_single_file_handles_401(self, mock_get, client):
        mock_resp = Mock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        with pytest.raises(AuthenticationError, match="Invalid API key"):
            client.get_trades("BTCUSDT", "binance_spot", "2023-01-01", "2023-01-01")
        assert mock_get.call_count > 0

    @patch("cryptohftdata.client.requests.get")
    def test_download_single_file_handles_other_http_error(self, mock_get, client):
        mock_resp = Mock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        result_df = client.get_trades(
            "BTCUSDT", "binance_spot", "2023-01-01", "2023-01-01"
        )
        assert result_df.empty
        assert mock_get.call_count == 24

    @patch("cryptohftdata.client.requests.get")
    @patch("zstandard.ZstdDecompressor")  # Target for 'zstandard.ZstdDecompressor'
    def test_download_single_file_zstd_error_fallback(
        self, mock_zstd_decompressor_class, mock_get, client
    ):  # Renamed for clarity
        mock_resp = Mock()
        mock_resp.status_code = 200
        # Simulate .zst file that is corrupted or not actually zstd, and doesn't start with PAR1
        mock_resp.content = b"fake_zstd_content_not_par1"
        mock_resp.headers = {
            "Content-Type": "application/octet-stream",
            "Content-Encoding": "zstd",
        }
        mock_get.return_value = mock_resp

        # Mock the instance created by ZstdDecompressor()
        mock_decompress_instance = mock_zstd_decompressor_class.return_value
        mock_decompress_instance.decompress.side_effect = zstd.ZstdError(
            "decompression failed"
        )

        client.clear_cache()  # Ensure cache is clear for this test

        def mock_generate_file_path_dynamic_for_test(
            exchange, symbol, data_type, date, hour
        ):
            # 'date' in _download_hourly_files is already a datetime object
            date_str = date.strftime("%Y-%m-%d")
            return f"{exchange}/{date_str}/{hour:02d}/{symbol}_{data_type}.parquet.zst"

        with patch("pandas.read_parquet") as mock_read_parquet, patch.object(
            client,
            "_generate_file_path",
            side_effect=mock_generate_file_path_dynamic_for_test,
        ):

            mock_df_single = pd.DataFrame({"data": [1]})  # Mock df for a single file
            mock_read_parquet.return_value = mock_df_single

            result = client.get_trades(
                "BTCUSDT", "binance_spot", "2023-01-01", "2023-01-01"
            )

            assert not result.empty
            # Each of the 24 hourly files should result in mock_df_single (1 row) after fallback.
            # These are then concatenated.
            assert len(result) == 24 * len(mock_df_single)

            assert (
                mock_zstd_decompressor_class.call_count == 24
            )  # ZstdDecompressor() instantiated 24 times
            assert (
                mock_decompress_instance.decompress.call_count == 24
            )  # .decompress() called 24 times (on the same mock instance due to .return_value)
            assert (
                mock_read_parquet.call_count == 24
            )  # Fallback pd.read_parquet called 24 times
