"""
Exchange identifiers and constants.
"""

from typing import Final, List


class ExchangeConstants:
    """Constants for supported exchanges."""

    # Binance
    BINANCE_SPOT: Final[str] = "binance_spot"
    BINANCE_FUTURES: Final[str] = "binance_futures"

    # Bybit
    BYBIT_SPOT: Final[str] = "bybit_spot"
    BYBIT_FUTURES: Final[str] = "bybit"

    # Kraken
    KRAKEN_SPOT: Final[str] = "kraken_spot"
    KRAKEN_FUTURES: Final[str] = "kraken_derivatives"

    # OKX
    OKX_SPOT: Final[str] = "okx_spot"
    OKX_FUTURES: Final[str] = "okx_futures"

    # Bitget
    BITGET_SPOT: Final[str] = "bitget_spot"
    BITGET_FUTURES: Final[str] = "bitget_futures"

    # Hyperliquid
    HYPERLIQUID_SPOT: Final[str] = "hyperliquid_spot"
    HYPERLIQUID_FUTURES: Final[str] = "hyperliquid_futures"

    # Lighter
    LIGHTER: Final[str] = "lighter"

    # Aster
    ASTER_FUTURES: Final[str] = "aster_futures"

    # BitMEX
    BITMEX: Final[str] = "bitmex"

    @classmethod
    def get_all_exchanges(cls) -> List[str]:
        """Get a list of all supported exchange identifiers."""
        return [
            value
            for name, value in cls.__dict__.items()
            if isinstance(value, str) and not name.startswith("_")
        ]

    @classmethod
    def is_valid_exchange(cls, exchange: str) -> bool:
        """Check if an exchange identifier is valid."""
        return exchange in cls.get_all_exchanges()

    @classmethod
    def get_exchange_type(cls, exchange: str) -> str:
        """Get the exchange type (spot, futures, options, etc.)."""
        futures_exchanges = {
            cls.BINANCE_FUTURES,
            cls.BYBIT_FUTURES,
            cls.KRAKEN_FUTURES,
            cls.OKX_FUTURES,
            cls.BITGET_FUTURES,
            cls.HYPERLIQUID_FUTURES,
            cls.LIGHTER,
            cls.ASTER_FUTURES,
            cls.BITMEX,
        }

        spot_exchanges = {
            cls.BINANCE_SPOT,
            cls.BYBIT_SPOT,
            cls.KRAKEN_SPOT,
            cls.OKX_SPOT,
            cls.BITGET_SPOT,
            cls.HYPERLIQUID_SPOT,
        }

        if exchange in futures_exchanges:
            return "futures"
        if exchange in spot_exchanges:
            return "spot"
        return "unknown"

    @classmethod
    def get_exchange_name(cls, exchange: str) -> str:
        """Get the exchange name without the market type."""
        if "_" in exchange:
            return exchange.split("_", 1)[0]
        return exchange


# Create the exchanges instance that users will import
exchanges = ExchangeConstants()
