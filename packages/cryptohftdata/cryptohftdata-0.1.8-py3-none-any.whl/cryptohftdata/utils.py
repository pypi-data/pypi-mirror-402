"""
Utility functions for the CryptoHFTData SDK.
"""

import re
from datetime import datetime, timezone
from typing import List, Tuple, Union

from dateutil import parser as date_parser

from .data_types import TIME_FORMATS
from .exceptions import ValidationError


def validate_symbol(symbol: str) -> None:
    """
    Validate a trading symbol.

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")

    Raises:
        ValidationError: If the symbol is invalid
    """
    if not symbol:
        raise ValidationError("Symbol cannot be empty")

    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")

    # Minimum length check
    if len(symbol) < 3:
        raise ValidationError(f"Symbol too short: {symbol}")

    # Maximum length check
    if len(symbol) > 20:
        raise ValidationError(f"Symbol too long: {symbol}")


def parse_date(date_input: Union[str, datetime]) -> datetime:
    """
    Parse a date input into a datetime object.

    Args:
        date_input: Date as string or datetime object

    Returns:
        Parsed datetime object (timezone-aware)

    Raises:
        ValidationError: If the date cannot be parsed
    """
    if isinstance(date_input, datetime):
        # Ensure timezone awareness
        if date_input.tzinfo is None:
            return date_input.replace(tzinfo=timezone.utc)
        return date_input

    if not isinstance(date_input, str):
        raise ValidationError(
            f"Date must be string or datetime, got {type(date_input)}"
        )

    # Try parsing with dateutil first (most flexible)
    try:
        parsed_date = date_parser.parse(date_input)
        # Ensure timezone awareness
        if parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        return parsed_date
    except (ValueError, TypeError) as e:
        # Fall back to manual format parsing
        for fmt in TIME_FORMATS:
            try:
                parsed_date = datetime.strptime(date_input, fmt)
                return parsed_date.replace(tzinfo=timezone.utc)
            except ValueError:
                continue

        raise ValidationError(f"Unable to parse date: {date_input}") from e


def validate_date_range(start_date: datetime, end_date: datetime) -> None:
    """
    Validate a date range.

    Args:
        start_date: Start date
        end_date: End date

    Raises:
        ValidationError: If the date range is invalid
    """
    if start_date > end_date:
        raise ValidationError("Start date must be before or equal to end date")

    # Check for reasonable date range (not too far in the past or future)
    now = datetime.now(timezone.utc)

    # Don't allow dates too far in the future
    if start_date > now:
        raise ValidationError("Start date cannot be in the future")

    # if end_date > now:
    #     raise ValidationError("End date cannot be in the future")

    # Don't allow dates too far in the past (e.g., before 2010)
    min_date = datetime(2010, 1, 1, tzinfo=timezone.utc)
    if start_date < min_date:
        raise ValidationError(f"Start date cannot be before {min_date.date()}")


def normalize_symbol(symbol: str) -> str:
    """
    Normalize a trading symbol to uppercase.

    Args:
        symbol: Trading pair symbol

    Returns:
        Normalized symbol in uppercase
    """
    if not isinstance(symbol, str):
        raise ValidationError("Symbol must be a string")

    return symbol.upper().strip()


def format_interval(interval: str) -> str:
    """
    Normalize and validate a time interval string.

    Args:
        interval: Time interval (e.g., "1m", "1h", "1d")

    Returns:
        Normalized interval string

    Raises:
        ValidationError: If the interval is invalid
    """
    if not isinstance(interval, str):
        raise ValidationError("Interval must be a string")

    original_interval = interval.strip()

    # Check for months pattern first (before lowercasing)
    if re.match(r"^\d+M$", original_interval):
        return original_interval  # Keep uppercase M for months

    # For all other patterns, convert to lowercase
    interval = original_interval.lower()

    # Valid interval patterns (excluding months which is handled above)
    valid_patterns = [
        r"^\d+s$",  # seconds: 1s, 5s, etc.
        r"^\d+m$",  # minutes: 1m, 5m, etc.
        r"^\d+h$",  # hours: 1h, 4h, etc.
        r"^\d+d$",  # days: 1d, 3d, etc.
        r"^\d+w$",  # weeks: 1w
    ]

    if not any(re.match(pattern, interval) for pattern in valid_patterns):
        raise ValidationError(f"Invalid interval format: {original_interval}")

    return interval


def chunk_date_range(
    start_date: datetime, end_date: datetime, max_days: int = 30
) -> List[Tuple[datetime, datetime]]:
    """
    Split a date range into smaller chunks.

    Args:
        start_date: Start date
        end_date: End date
        max_days: Maximum days per chunk

    Returns:
        List of (start, end) date tuples
    """
    from datetime import timedelta

    chunks = []
    current_start = start_date

    while current_start < end_date:
        current_end = min(current_start + timedelta(days=max_days), end_date)
        chunks.append((current_start, current_end))
        current_start = current_end

    return chunks


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe file system usage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove leading/trailing dots and spaces
    safe_filename = safe_filename.strip(". ")

    # Limit length
    if len(safe_filename) > 255:
        safe_filename = safe_filename[:255]

    return safe_filename


def calculate_pagination(
    total_items: int, page_size: int, current_page: int = 1
) -> dict:
    """
    Calculate pagination parameters.

    Args:
        total_items: Total number of items
        page_size: Items per page
        current_page: Current page number (1-based)

    Returns:
        Dictionary with pagination info
    """
    import math

    total_pages = math.ceil(total_items / page_size) if page_size > 0 else 0

    return {
        "total_items": total_items,
        "page_size": page_size,
        "current_page": current_page,
        "total_pages": total_pages,
        "has_next": current_page < total_pages,
        "has_prev": current_page > 1,
        "start_index": (current_page - 1) * page_size,
        "end_index": min(current_page * page_size, total_items),
    }
