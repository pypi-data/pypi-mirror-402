"""
CryptoHFTData Python SDK

A simple and intuitive API for accessing cryptocurrency high-frequency trading data.
"""

import pandas as pd

from .client import CryptoHFTDataClient
from .data_types import DataType
from .exceptions import (
    APIError,
    AuthenticationError,
    CryptoHFTDataError,
    ValidationError,
)
from .exchanges import exchanges

# Aliases for convenience
Client = CryptoHFTDataClient

# Version information
__version__ = "0.1.8"
__author__ = "CryptoHFTData Team"
__email__ = "support@cryptohftdata.com"

# Default client instance for convenience functions
_default_client = None


def _get_default_client() -> CryptoHFTDataClient:
    """Get or create the default client instance."""
    global _default_client
    if _default_client is None:
        _default_client = CryptoHFTDataClient()
    return _default_client


# Convenience functions that use the default client


def get_orderbook(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get orderbook data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing orderbook data
    """
    return _get_default_client().get_orderbook(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_trades(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get trade data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing trade data
    """
    return _get_default_client().get_trades(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_ticker(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get ticker data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing ticker data
    """
    return _get_default_client().get_ticker(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_mark_price(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get mark price data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier (mark price is typically available for futures markets)
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing mark price data

    Note:
        Mark price data is typically only available for futures exchanges.
    """
    return _get_default_client().get_mark_price(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_funding_rates(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get funding rates data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing funding rates data
    """
    return _get_default_client().get_funding_rates(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_open_interest(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get open interest data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing open interest data
    """
    return _get_default_client().get_open_interest(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def get_liquidations(
    symbol: str, exchange: str, start_date: str, end_date: str, **kwargs
) -> pd.DataFrame:
    """
    Get liquidations data for a trading pair.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        exchange: Exchange identifier
        start_date: Start date (ISO format or datetime)
        end_date: End date (ISO format or datetime)
        **kwargs: Additional parameters

    Returns:
        pandas DataFrame containing liquidations data
    """
    return _get_default_client().get_liquidations(
        symbol=symbol,
        exchange=exchange,
        start_date=start_date,
        end_date=end_date,
        **kwargs,
    )


def list_symbols(exchange: str, data_type: str = None) -> list[str]:
    """
    List available symbols for an exchange.

    Args:
        exchange: Exchange identifier
        data_type: Optional dataset filter (e.g., ``trades`` or ``ticker``)

    Returns:
        List of available symbols
    """
    return _get_default_client().list_symbols(exchange=exchange, data_type=data_type)


def list_exchanges() -> list[str]:
    """
    List all supported exchanges.

    Returns:
        List of supported exchange identifiers
    """
    return _get_default_client().list_exchanges()


def get_exchange_info(exchange: str) -> dict:
    """
    Get information about a specific exchange.

    Args:
        exchange: Exchange identifier

    Returns:
        Dictionary containing exchange information
    """
    return _get_default_client().get_exchange_info(exchange=exchange)


def configure_client(api_key: str = None, base_url: str = None, **kwargs) -> None:
    """
    Configure the default client with authentication and other settings.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API
        **kwargs: Additional configuration options
    """
    global _default_client
    _default_client = CryptoHFTDataClient(api_key=api_key, base_url=base_url, **kwargs)


# Export all public APIs
__all__ = [
    # Core functions
    "get_orderbook",
    "get_trades",
    "get_ticker",
    "get_mark_price",
    "get_funding_rates",
    "get_open_interest",
    "get_liquidations",
    "list_symbols",
    "list_exchanges",
    "get_exchange_info",
    "configure_client",
    # Classes
    "CryptoHFTDataClient",
    # Enums and constants
    "DataType",
    "exchanges",
    # Exceptions
    "CryptoHFTDataError",
    "APIError",
    "ValidationError",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]
