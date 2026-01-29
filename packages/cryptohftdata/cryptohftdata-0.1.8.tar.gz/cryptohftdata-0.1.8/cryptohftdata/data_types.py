"""
Data type enumerations and constants.
"""

from enum import Enum
from typing import Final, List


class DataType(Enum):
    """Enumeration of supported data types."""

    KLINES = "klines"
    ORDERBOOK = "orderbook"
    TRADES = "trades"
    TICKER = "ticker"
    MARK_PRICE = "mark_price"
    FUNDING_RATES = "funding_rates"
    OPEN_INTEREST = "open_interest"
    LIQUIDATIONS = "liquidations"

    def __str__(self) -> str:
        return self.value


class Interval(Enum):
    """Time intervals for kline data."""

    # Seconds
    SEC_1 = "1s"
    SEC_5 = "5s"
    SEC_15 = "15s"
    SEC_30 = "30s"

    # Minutes
    MIN_1 = "1m"
    MIN_3 = "3m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    MIN_30 = "30m"

    # Hours
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"

    # Days
    DAY_1 = "1d"
    DAY_3 = "3d"

    # Weeks
    WEEK_1 = "1w"

    # Months
    MONTH_1 = "1M"

    def __str__(self) -> str:
        return self.value


class OrderBookLevel(Enum):
    """Order book depth levels."""

    LEVEL_5 = 5
    LEVEL_10 = 10
    LEVEL_20 = 20
    LEVEL_50 = 50
    LEVEL_100 = 100
    LEVEL_500 = 500
    LEVEL_1000 = 1000
    FULL = -1  # Full order book

    def __str__(self) -> str:
        return str(self.value) if self.value != -1 else "full"


class MarketType(Enum):
    """Market types."""

    SPOT = "spot"
    FUTURES = "futures"
    OPTIONS = "options"
    DERIVATIVES = "derivatives"

    def __str__(self) -> str:
        return self.value


# Common time formats
TIME_FORMATS: Final[List[str]] = [
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S.%f",
]

# Default values
DEFAULT_INTERVAL: Final[str] = Interval.MIN_1.value
DEFAULT_ORDERBOOK_LEVEL: Final[int] = OrderBookLevel.LEVEL_20.value
DEFAULT_TIMEOUT: Final[int] = 30
DEFAULT_MAX_RETRIES: Final[int] = 3
