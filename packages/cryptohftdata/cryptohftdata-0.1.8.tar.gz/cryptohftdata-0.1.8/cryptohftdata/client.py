"""
Main client class for the CryptoHFTData SDK.
"""

import asyncio
import io
import json
import logging
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
import pandas as pd
import requests
import zstandard as zstd
from tqdm import tqdm

from .data_types import DEFAULT_TIMEOUT, DataType, Interval, OrderBookLevel
from .exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    CryptoHFTDataError,
    NetworkError,
    TimeoutError,
    ValidationError,
)
from .exchanges import ExchangeConstants
from .http_client import HTTPClient, JWTTokenManager
from .utils import parse_date, validate_date_range, validate_symbol

logger = logging.getLogger(__name__)


class CryptoHFTDataClient:
    """
    Main client for accessing CryptoHFTData API.

    This client provides both synchronous and asynchronous methods for fetching
    cryptocurrency market data from various exchanges.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        rate_limit: Optional[int] = None,
        use_jwt: bool = True,
        **kwargs,
    ):
        """
        Initialize the CryptoHFTData client.

        Args:
            api_key: API key for authentication (optional for public data)
            base_url: Base URL for the API (defaults to production URL)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit: Maximum requests per second (optional)
            use_jwt: Whether to use JWT tokens for authentication (default: True)
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.base_url = base_url or "https://api.cryptohftdata.com"
        self.download_endpoint = f"{self.base_url}/download"
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit = rate_limit
        self.use_jwt = use_jwt

        # Initialize HTTP client with JWT support
        self._http_client = HTTPClient(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
            max_retries=self.max_retries,
            rate_limit=self.rate_limit,
            use_jwt=self.use_jwt,
            **kwargs,
        )

        # JWT token manager for direct downloads
        self._jwt_manager: Optional[JWTTokenManager] = None
        if self.api_key and self.use_jwt:
            self._jwt_manager = JWTTokenManager(self.api_key, self.base_url, timeout)

        # Exchange validator
        self._exchange_validator = ExchangeConstants()

        # LRU file cache to store the most recent 100 files downloaded
        self._file_cache: OrderedDict[str, Optional[pd.DataFrame]] = OrderedDict()
        self._cache_max_size = 100

        logger.info(f"Initialized CryptoHFTData client with base_url: {self.base_url}")

    def _get_from_cache(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Get file from cache and move to end (most recently used).

        Args:
            file_path: The file path to retrieve from cache

        Returns:
            DataFrame if found in cache, None otherwise
        """
        if file_path in self._file_cache:
            # Move to end (most recently used)
            value = self._file_cache.pop(file_path)
            self._file_cache[file_path] = value
            return value
        return None

    def _add_to_cache(self, file_path: str, data: Optional[pd.DataFrame]) -> None:
        """
        Add file to cache, removing oldest entries if necessary.

        Args:
            file_path: The file path to cache
            data: The DataFrame to cache (can be None for failed downloads)
        """
        # Remove if already exists (to update position)
        if file_path in self._file_cache:
            del self._file_cache[file_path]

        # Add to end (most recently used)
        self._file_cache[file_path] = data

        # Remove oldest entries if cache is too large
        while len(self._file_cache) > self._cache_max_size:
            oldest_key = next(iter(self._file_cache))
            del self._file_cache[oldest_key]
            logger.debug(f"Removed oldest cache entry: {oldest_key}")

    def _generate_file_path(
        self,
        exchange: str,
        symbol: str,
        data_type: str,
        date: Union[str, datetime],
        hour: int,
    ) -> str:
        """
        Generate R2 file path based on the directory structure.

        Format: [exchange]/[YYYY-MM-DD]/[HH]/[symbol]_[type].parquet.zst
        """
        if isinstance(date, str):
            # If date is already a string, use it directly
            date_str = date
        else:
            # If date is a datetime object, format it
            date_str = date.strftime("%Y-%m-%d")

        hour_str = f"{hour:02d}"
        return f"{exchange}/{date_str}/{hour_str}/{symbol}_{data_type}.parquet.zst"

    def _download_single_file(
        self, file_path: str, retry_count: int = 0
    ) -> Optional[pd.DataFrame]:
        """
        Download a single parquet file from R2.

        Returns None if file doesn't exist or download fails.
        """
        if not self.api_key:
            raise ConfigurationError("API key is required for downloading data")

        # Check cache first
        cached_result = self._get_from_cache(file_path)
        if cached_result is not None:
            logger.debug(f"Using cached file: {file_path}")
            return cached_result

        # Prepare headers for authentication
        headers = {}

        # Try JWT token first if available
        if self._jwt_manager and self.use_jwt:
            try:
                jwt_token = self._jwt_manager.get_jwt_token()
                headers["Authorization"] = f"Bearer {jwt_token}"
                url = f"{self.download_endpoint}?file={file_path}"
            except AuthenticationError as e:
                logger.warning(
                    f"JWT token generation failed: {e}, falling back to API key"
                )
                headers["X-API-Key"] = self.api_key
                url = f"{self.download_endpoint}?file={file_path}"
        else:
            # Use API key directly
            url = f"{self.download_endpoint}?file={file_path}&api_key={self.api_key}"

        try:
            logger.debug(f"Downloading file: {file_path}")
            response = requests.get(url, headers=headers, timeout=self.timeout)

            if response.status_code == 404:
                logger.debug(f"File not found: {file_path}")
                self._add_to_cache(file_path, None)
                return None
            elif response.status_code == 401:
                # Check if this is a JWT token expiration and retry once
                if (
                    retry_count == 0
                    and self._jwt_manager
                    and self.use_jwt
                    and "Authorization" in headers
                ):
                    try:
                        error_data = response.json()
                        error_code = error_data.get("code", "")

                        # If it's an expired token, invalidate and retry
                        if error_code in [
                            "expired_token",
                            "invalid_token",
                            "validation_failed",
                        ]:
                            logger.debug("JWT token expired, refreshing and retrying")
                            self._jwt_manager.invalidate_token()
                            return self._download_single_file(
                                file_path, retry_count + 1
                            )
                    except (json.JSONDecodeError, KeyError):
                        pass

                # This error should be critical and propagate up
                raise AuthenticationError("Invalid API key or authentication failed")
            elif response.status_code != 200:
                logger.warning(
                    f"Failed to download {file_path}: HTTP {response.status_code}"
                )
                return None

            # Check content length and type
            content_length = len(response.content)
            content_type = response.headers.get("Content-Type", "unknown")
            content_encoding = response.headers.get("Content-Encoding", "none")
            logger.debug(
                f"Response: {content_length} bytes, content-type: {content_type}, encoding: {content_encoding}"
            )

            if content_length == 0:
                logger.warning(f"Empty response for {file_path}")
                return None

            # Check if the content is already plain parquet (PAR1 magic)
            if response.content.startswith(b"PAR1"):
                # File is already uncompressed parquet
                logger.debug(f"File {file_path} is plain parquet (not compressed)")
                df = pd.read_parquet(io.BytesIO(response.content))
            elif file_path.endswith(".zst") or content_encoding == "zstd":
                # File should be zstd compressed
                try:
                    # Decompress zstd file
                    dctx = zstd.ZstdDecompressor()
                    decompressed_data = dctx.decompress(response.content)
                    logger.debug(
                        f"Successfully decompressed {content_length} -> {len(decompressed_data)} bytes"
                    )

                    # Read parquet from decompressed data
                    df = pd.read_parquet(io.BytesIO(decompressed_data))
                except zstd.ZstdError as zst_error:
                    logger.warning(
                        f"Zstd decompression failed for {file_path}: {str(zst_error)}"
                    )
                    # Fallback: try reading as plain parquet
                    try:
                        df = pd.read_parquet(io.BytesIO(response.content))
                        logger.info(
                            f"File {file_path} was read as plain parquet despite .zst extension"
                        )
                    except Exception as plain_error:
                        logger.error(
                            f"Failed to read {file_path} as both compressed and plain parquet: zstd={zst_error}, plain={plain_error}"
                        )
                        return None
            else:
                # Assume plain parquet
                df = pd.read_parquet(io.BytesIO(response.content))

            logger.debug(f"Successfully downloaded {file_path}: {len(df)} records")

            # Cache the successful result
            self._add_to_cache(file_path, df)
            return df

        except Exception as e:
            # If the exception is one of our critical ones, re-raise it.
            if isinstance(e, (AuthenticationError, ConfigurationError)):
                raise
            # Otherwise, log it as a warning for this specific file and return None.
            logger.warning(f"Error downloading {file_path}: {str(e)}")
            return None

    def _download_hourly_files(
        self,
        exchange: str,
        symbol: str,
        data_type: str,
        date: datetime,
        max_workers: int = 1,
        progress_bar: Optional[tqdm] = None,
    ) -> List[pd.DataFrame]:
        """
        Download files for all 24 hours of a given date.

        Uses concurrent downloads for better performance.
        """
        file_paths = []
        for hour in range(24):
            file_path = self._generate_file_path(
                exchange, symbol, data_type, date, hour
            )
            file_paths.append((file_path, hour))

        successful_downloads = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_hour = {
                executor.submit(self._download_single_file, file_path): hour
                for file_path, hour in file_paths
            }

            # Collect results as they complete
            # Store the first critical error encountered
            first_critical_error = None

            for future in as_completed(future_to_hour):
                hour = future_to_hour[future]
                try:
                    df = (
                        future.result()
                    )  # This will re-raise exceptions from _download_single_file
                    if df is not None:
                        successful_downloads.append((hour, df))
                except (ConfigurationError, AuthenticationError) as critical_error:
                    logger.error(
                        f"Critical download error for hour {hour}: {str(critical_error)}"
                    )
                    if first_critical_error is None:
                        first_critical_error = critical_error
                    # Optionally, cancel remaining futures if possible, though ThreadPoolExecutor makes this tricky.
                    # For now, we'll collect all results/exceptions and raise the first critical one.
                except Exception as e:
                    logger.warning(f"Download failed for hour {hour}: {str(e)}")

                # Update progress bar after each file (whether successful or failed)
                if progress_bar is not None:
                    progress_bar.update(1)

            if first_critical_error:
                # If a critical error occurred in any of the tasks, raise it.
                raise first_critical_error

        # Sort by hour and return DataFrames
        successful_downloads.sort(key=lambda x: x[0])
        return [df for _, df in successful_downloads]

    def _download_date_range(
        self,
        exchange: str,
        symbol: str,
        data_type: str,
        start_date: datetime,
        end_date: datetime,
        max_workers: int = 1,
    ) -> pd.DataFrame:
        """
        Download files for a date range and concatenate them.
        """
        all_dataframes = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        # Calculate total number of files (24 files per day)
        total_days = (end_date_only - current_date).days + 1
        total_files = total_days * 24

        # Create progress bar for individual files
        progress_bar = tqdm(
            total=total_files,
            desc=f"Downloading {symbol} {data_type} data from {exchange}",
            unit="file",
        )

        while current_date <= end_date_only:
            date_dt = datetime.combine(current_date, datetime.min.time())

            logger.info(f"Downloading data for {current_date}")
            hourly_dfs = self._download_hourly_files(
                exchange,
                symbol,
                data_type,
                date_dt,
                progress_bar=progress_bar,
                max_workers=max_workers,
            )

            if hourly_dfs:
                all_dataframes.extend(hourly_dfs)
                logger.info(f"Downloaded {len(hourly_dfs)} files for {current_date}")
            else:
                logger.warning(f"No data found for {current_date}")

            current_date += timedelta(days=1)

        progress_bar.close()

        if not all_dataframes:
            logger.warning("No data files found for the specified date range")
            return pd.DataFrame()

        # Concatenate all DataFrames
        logger.info(f"Concatenating {len(all_dataframes)} DataFrames")
        result_df = pd.concat(all_dataframes, ignore_index=True)

        # Sort by timestamp if available
        if "timestamp" in result_df.columns:
            result_df = result_df.sort_values("timestamp").reset_index(drop=True)
        elif "open_time" in result_df.columns:
            result_df = result_df.sort_values("open_time").reset_index(drop=True)

        logger.info(f"Final dataset: {len(result_df)} records")
        return result_df

    def _get_data(
        self,
        data_type: str,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        max_workers: int = 10,
        **_: Any,
    ) -> pd.DataFrame:
        """Common logic for fetching different types of data."""
        self._validate_common_params(symbol, exchange, start_date, end_date)

        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)

        df = self._download_date_range(
            exchange, symbol, data_type, start_dt, end_dt, max_workers=max_workers
        )

        return df

    def get_orderbook(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get orderbook data for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            exchange: Exchange identifier
            start_date: Start date (ISO format string or datetime object)
            end_date: End date (ISO format string or datetime object)
            **kwargs: Additional query parameters

        Returns:
            pandas DataFrame containing orderbook data

        Raises:
            ValidationError: If input parameters are invalid
            APIError: If the API request fails
        """
        return self._get_data(
            "orderbook",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

    def get_trades(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get trade data for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            exchange: Exchange identifier
            start_date: Start date (ISO format string or datetime object)
            end_date: End date (ISO format string or datetime object)
            **kwargs: Additional query parameters

        Returns:
            pandas DataFrame containing trade data

        Raises:
            ValidationError: If input parameters are invalid
            APIError: If the API request fails
        """
        return self._get_data(
            "trades",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

    def get_ticker(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get ticker data for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            exchange: Exchange identifier
            start_date: Start date (ISO format string or datetime object)
            end_date: End date (ISO format string or datetime object)
            **kwargs: Additional query parameters

        Returns:
            pandas DataFrame containing ticker data

        Raises:
            ValidationError: If input parameters are invalid
            APIError: If the API request fails
        """
        return self._get_data(
            "ticker",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

    def get_mark_price(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get mark price data for a trading pair.

        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            exchange: Exchange identifier (mark price is typically available for futures markets)
            start_date: Start date (ISO format string or datetime object)
            end_date: End date (ISO format string or datetime object)
            **kwargs: Additional query parameters

        Returns:
            pandas DataFrame containing mark price data

        Raises:
            ValidationError: If input parameters are invalid
            APIError: If the API request fails

        Note:
            Mark price data is typically only available for futures exchanges.
        """
        return self._get_data(
            "mark_price",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

    def get_open_interest(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get open interest data for a given symbol and exchange.
        """
        df = self._get_data(
            "open_interest",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

        # Post-processing: remove duplicate timestamp rows, keeping the most recent one
        if not df.empty and "timestamp" in df.columns:
            # Sort by timestamp to ensure we keep the most recent duplicate
            df = df.sort_values("timestamp")
            # Drop duplicates based on timestamp, keeping the last occurrence (most recent)
            df = df.drop_duplicates(subset=["timestamp"], keep="last")
            # Reset index after dropping duplicates
            df = df.reset_index(drop=True)
            logger.debug(
                f"Removed duplicate timestamps from open interest data, final shape: {df.shape}"
            )

        return df

    def get_liquidations(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        **kwargs,
    ) -> pd.DataFrame:
        """
        Get liquidations data for a given symbol and exchange.
        """
        return self._get_data(
            "liquidations",
            symbol,
            exchange,
            start_date,
            end_date,
            **kwargs,
        )

    def list_symbols(self, exchange: str, data_type: Optional[str] = None) -> List[str]:
        """
        List available symbols for an exchange.

        Args:
            exchange: Exchange identifier
            data_type: Optional dataset filter (e.g., ``trades`` or ``ticker``)

        Returns:
            List of available symbols

        """
        if not self._exchange_validator.is_valid_exchange(exchange):
            raise ValidationError(f"Invalid exchange: {exchange}")

        params: Dict[str, Any] = {"exchange": exchange}
        if data_type:
            params["data_type"] = data_type

        try:
            logger.debug(
                "Fetching symbols from API",
                extra={"exchange": exchange, "data_type": data_type},
            )
            response = self._http_client.get("symbols", params=params)
        except (APIError, AuthenticationError, NetworkError, TimeoutError) as exc:
            raise APIError(f"Failed to fetch symbols: {exc}") from exc

        symbols = response.get("symbols", []) if isinstance(response, dict) else []

        if not isinstance(symbols, list):
            raise APIError("Invalid response format from symbols endpoint")

        normalized_symbols = [str(symbol) for symbol in symbols]
        logger.info(
            "Fetched %d symbols for %s",
            len(normalized_symbols),
            exchange,
        )
        return normalized_symbols

    def list_exchanges(self) -> List[str]:
        """
        List all supported exchanges.

        Returns:
            List of supported exchange identifiers
        """
        return [
            ExchangeConstants.BINANCE_SPOT,
            ExchangeConstants.BINANCE_FUTURES,
            ExchangeConstants.BYBIT_SPOT,
            ExchangeConstants.BYBIT_FUTURES,
            ExchangeConstants.KRAKEN_SPOT,
            ExchangeConstants.KRAKEN_FUTURES,
            ExchangeConstants.OKX_SPOT,
            ExchangeConstants.OKX_FUTURES,
            ExchangeConstants.BITGET_SPOT,
            ExchangeConstants.BITGET_FUTURES,
            ExchangeConstants.HYPERLIQUID_SPOT,
            ExchangeConstants.HYPERLIQUID_FUTURES,
            ExchangeConstants.LIGHTER,
            ExchangeConstants.ASTER_FUTURES,
            ExchangeConstants.BITMEX,
        ]

    def get_exchange_info(self, exchange: str) -> Dict[str, Any]:
        """
        Get information about a specific exchange.

        Args:
            exchange: Exchange identifier

        Returns:
            Dictionary containing exchange information
        """
        if not self._exchange_validator.is_valid_exchange(exchange):
            raise ValidationError(f"Invalid exchange: {exchange}")

        # Return basic exchange information
        exchange_info = {
            ExchangeConstants.BINANCE_SPOT: {
                "name": "Binance Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "ticker"],
            },
            ExchangeConstants.BINANCE_FUTURES: {
                "name": "Binance Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "funding_rates",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.BYBIT_SPOT: {
                "name": "Bybit Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "ticker"],
            },
            ExchangeConstants.BYBIT_FUTURES: {
                "name": "Bybit Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "funding_rates",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.KRAKEN_SPOT: {
                "name": "Kraken Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "ticker"],
            },
            ExchangeConstants.KRAKEN_FUTURES: {
                "name": "Kraken Derivatives",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.OKX_SPOT: {
                "name": "OKX Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "ticker"],
            },
            ExchangeConstants.OKX_FUTURES: {
                "name": "OKX Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "funding_rates",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.BITGET_SPOT: {
                "name": "Bitget Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "ticker"],
            },
            ExchangeConstants.BITGET_FUTURES: {
                "name": "Bitget Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.HYPERLIQUID_SPOT: {
                "name": "Hyperliquid Spot",
                "type": "spot",
                "supported_data_types": ["klines", "trades", "orderbook", "mark_price"],
            },
            ExchangeConstants.HYPERLIQUID_FUTURES: {
                "name": "Hyperliquid Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "mark_price",
                    "open_interest",
                ],
            },
            ExchangeConstants.LIGHTER: {
                "name": "Lighter Perpetuals",
                "type": "futures",
                "supported_data_types": [
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "open_interest",
                ],
            },
            ExchangeConstants.ASTER_FUTURES: {
                "name": "Aster Futures",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "open_interest",
                    "liquidations",
                ],
            },
            ExchangeConstants.BITMEX: {
                "name": "BitMEX",
                "type": "futures",
                "supported_data_types": [
                    "klines",
                    "trades",
                    "orderbook",
                    "ticker",
                    "mark_price",
                    "open_interest",
                    "liquidations",
                ],
            },
        }

        return exchange_info.get(exchange, {"name": exchange, "type": "unknown"})

    def _validate_common_params(
        self,
        symbol: str,
        exchange: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
    ) -> None:
        """Validate common parameters used across methods."""
        # Validate symbol
        validate_symbol(symbol)

        # Validate exchange
        if not self._exchange_validator.is_valid_exchange(exchange):
            raise ValidationError(f"Invalid exchange: {exchange}")

        # Validate date range
        start_dt = parse_date(start_date)
        end_dt = parse_date(end_date)
        validate_date_range(start_dt, end_dt)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self._http_client.close()

    def clear_cache(self) -> None:
        """Clear the internal file cache."""
        self._file_cache.clear()
        logger.info("File cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state."""
        return {
            "cached_files": len(self._file_cache),
            "cache_max_size": self._cache_max_size,
            "successful_downloads": len(
                [k for k, v in self._file_cache.items() if v is not None]
            ),
            "failed_downloads": len(
                [k for k, v in self._file_cache.items() if v is None]
            ),
        }
