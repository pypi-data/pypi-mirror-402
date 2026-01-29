import re
import unittest
from datetime import datetime, timedelta, timezone

from cryptohftdata.exceptions import ValidationError
from cryptohftdata.utils import (
    calculate_pagination,
    chunk_date_range,
    format_interval,
    normalize_symbol,
    parse_date,
    sanitize_filename,
    validate_date_range,
    validate_symbol,
)


class TestUtils(unittest.TestCase):

    def test_validate_symbol_valid(self):
        self.assertIsNone(validate_symbol("BTCUSDT"))
        self.assertIsNone(validate_symbol("ETHBTC"))
        self.assertIsNone(validate_symbol("1000SHIBUSDT"))

    def test_validate_symbol_invalid(self):
        with self.assertRaisesRegex(ValidationError, "Symbol cannot be empty"):
            validate_symbol("")
        with self.assertRaisesRegex(ValidationError, "Symbol must be a string"):
            validate_symbol(123)
        with self.assertRaisesRegex(ValidationError, "Symbol too short: BT"):
            validate_symbol("BT")
        with self.assertRaisesRegex(
            ValidationError, "Symbol too long: THISISAVERYLONGSYMBOLNAME"
        ):
            validate_symbol("THISISAVERYLONGSYMBOLNAME")  # 26 chars

    def test_parse_date_string(self):
        dt_str = "2023-01-01T12:00:00Z"
        expected_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(parse_date(dt_str), expected_dt)

        dt_str_no_tz = "2023-01-01 10:30:00"
        expected_dt_utc = datetime(2023, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(parse_date(dt_str_no_tz), expected_dt_utc)

        # Test various supported formats
        self.assertEqual(
            parse_date("2023-01-15"),
            datetime(2023, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            parse_date("03/20/2023"),
            datetime(2023, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            parse_date("2023.04.10 15:45"),
            datetime(2023, 4, 10, 15, 45, 0, tzinfo=timezone.utc),
        )

    def test_parse_date_datetime_object(self):
        dt_aware = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(parse_date(dt_aware), dt_aware)

        dt_naive = datetime(2023, 1, 1, 10, 30, 0)
        expected_dt_utc = dt_naive.replace(tzinfo=timezone.utc)
        self.assertEqual(parse_date(dt_naive), expected_dt_utc)

    def test_parse_date_invalid(self):
        with self.assertRaisesRegex(
            ValidationError, "Date must be string or datetime, got <class 'int'>"
        ):
            parse_date(12345)
        with self.assertRaisesRegex(
            ValidationError, "Unable to parse date: invalid-date-string"
        ):
            parse_date("invalid-date-string")

    def test_validate_date_range_valid(self):
        start = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end = datetime(2023, 1, 10, tzinfo=timezone.utc)
        self.assertIsNone(validate_date_range(start, end))

        # Test with current time for end date
        start_past = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_now = datetime.now(timezone.utc)
        self.assertIsNone(validate_date_range(start_past, end_now))

    def test_validate_date_range_invalid(self):
        start = datetime(2023, 1, 10, tzinfo=timezone.utc)
        end = datetime(2023, 1, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(
            ValidationError, "Start date must be before or equal to end date"
        ):
            validate_date_range(start, end)

        future_start = datetime.now(timezone.utc) + timedelta(days=1)
        future_end = datetime.now(timezone.utc) + timedelta(days=2)
        with self.assertRaisesRegex(
            ValidationError, "Start date cannot be in the future"
        ):
            validate_date_range(future_start, future_end)

        # Commented out in original code, but good to have a test if uncommented
        # future_end_only_start = datetime(2023,1,1, tzinfo=timezone.utc)
        # future_end_only_end = datetime.now(timezone.utc) + timedelta(days=1)
        # with self.assertRaisesRegex(ValidationError, "End date cannot be in the future"):
        #     validate_date_range(future_end_only_start, future_end_only_end)

        too_old_start = datetime(2009, 12, 31, tzinfo=timezone.utc)
        valid_end = datetime(2010, 1, 5, tzinfo=timezone.utc)
        with self.assertRaisesRegex(
            ValidationError, "Start date cannot be before 2010-01-01"
        ):
            validate_date_range(too_old_start, valid_end)

    def test_normalize_symbol(self):
        self.assertEqual(normalize_symbol("btcusdt"), "BTCUSDT")
        self.assertEqual(normalize_symbol(" ETHBTC "), "ETHBTC")
        with self.assertRaisesRegex(ValidationError, "Symbol must be a string"):
            normalize_symbol(123)

    def test_format_interval_valid(self):
        self.assertEqual(format_interval("1m"), "1m")
        self.assertEqual(format_interval("5H"), "5h")
        self.assertEqual(format_interval(" 1D "), "1d")
        self.assertEqual(format_interval("15s"), "15s")
        self.assertEqual(format_interval("1w"), "1w")
        self.assertEqual(format_interval("1M"), "1M")  # Months should remain uppercase
        self.assertEqual(format_interval(" 12M "), "12M")  # Test with whitespace

    def test_format_interval_invalid(self):
        with self.assertRaisesRegex(ValidationError, "Interval must be a string"):
            format_interval(123)
        with self.assertRaisesRegex(ValidationError, "Invalid interval format: 1y"):
            format_interval("1y")  # Year not supported by current patterns
        with self.assertRaisesRegex(ValidationError, "Invalid interval format: m1"):
            format_interval("m1")
        with self.assertRaisesRegex(ValidationError, "Invalid interval format: 60"):
            format_interval("60")

    def test_chunk_date_range(self):
        start = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end = datetime(2023, 1, 5, tzinfo=timezone.utc)
        chunks = chunk_date_range(start, end, max_days=2)
        expected_chunks = [
            (
                datetime(2023, 1, 1, tzinfo=timezone.utc),
                datetime(2023, 1, 3, tzinfo=timezone.utc),
            ),
            (
                datetime(2023, 1, 3, tzinfo=timezone.utc),
                datetime(2023, 1, 5, tzinfo=timezone.utc),
            ),
        ]
        self.assertEqual(chunks, expected_chunks)

        # Test with end date not aligning perfectly with max_days
        end_partial = datetime(2023, 1, 4, tzinfo=timezone.utc)
        chunks_partial = chunk_date_range(start, end_partial, max_days=2)
        expected_chunks_partial = [
            (
                datetime(2023, 1, 1, tzinfo=timezone.utc),
                datetime(2023, 1, 3, tzinfo=timezone.utc),
            ),
            (
                datetime(2023, 1, 3, tzinfo=timezone.utc),
                datetime(2023, 1, 4, tzinfo=timezone.utc),
            ),
        ]
        self.assertEqual(chunks_partial, expected_chunks_partial)

        # Test with range smaller than max_days
        end_small = datetime(2023, 1, 2, tzinfo=timezone.utc)
        chunks_small = chunk_date_range(start, end_small, max_days=5)
        expected_chunks_small = [
            (
                datetime(2023, 1, 1, tzinfo=timezone.utc),
                datetime(2023, 1, 2, tzinfo=timezone.utc),
            )
        ]
        self.assertEqual(chunks_small, expected_chunks_small)

        # Test with start_date == end_date
        chunks_same = chunk_date_range(start, start, max_days=5)
        self.assertEqual(chunks_same, [])

    def test_sanitize_filename(self):
        self.assertEqual(sanitize_filename("file:name?.txt"), "file_name_.txt")
        self.assertEqual(sanitize_filename(" leading/trailing "), "leading_trailing")
        self.assertEqual(sanitize_filename(".hiddenfile"), "hiddenfile")
        long_name = "a" * 300
        self.assertEqual(len(sanitize_filename(long_name)), 255)
        self.assertTrue(sanitize_filename(long_name).startswith("a" * 255))

    def test_calculate_pagination(self):
        # Basic case
        pagination = calculate_pagination(total_items=100, page_size=10, current_page=1)
        self.assertEqual(pagination["total_pages"], 10)
        self.assertEqual(pagination["has_next"], True)
        self.assertEqual(pagination["has_prev"], False)
        self.assertEqual(pagination["start_index"], 0)
        self.assertEqual(pagination["end_index"], 10)

        # Middle page
        pagination_mid = calculate_pagination(
            total_items=100, page_size=10, current_page=5
        )
        self.assertEqual(pagination_mid["has_next"], True)
        self.assertEqual(pagination_mid["has_prev"], True)
        self.assertEqual(pagination_mid["start_index"], 40)
        self.assertEqual(pagination_mid["end_index"], 50)

        # Last page
        pagination_last = calculate_pagination(
            total_items=100, page_size=10, current_page=10
        )
        self.assertEqual(pagination_last["has_next"], False)
        self.assertEqual(pagination_last["has_prev"], True)
        self.assertEqual(pagination_last["start_index"], 90)
        self.assertEqual(pagination_last["end_index"], 100)

        # Page size larger than total items
        pagination_large_ps = calculate_pagination(
            total_items=5, page_size=10, current_page=1
        )
        self.assertEqual(pagination_large_ps["total_pages"], 1)
        self.assertEqual(pagination_large_ps["has_next"], False)
        self.assertEqual(pagination_large_ps["has_prev"], False)
        self.assertEqual(pagination_large_ps["start_index"], 0)
        self.assertEqual(pagination_large_ps["end_index"], 5)

        # Zero items
        pagination_zero = calculate_pagination(
            total_items=0, page_size=10, current_page=1
        )
        self.assertEqual(pagination_zero["total_pages"], 0)
        self.assertEqual(pagination_zero["has_next"], False)
        self.assertEqual(pagination_zero["has_prev"], False)
        self.assertEqual(pagination_zero["start_index"], 0)
        self.assertEqual(pagination_zero["end_index"], 0)

        # Zero page_size (should result in 0 total_pages)
        pagination_zero_ps = calculate_pagination(
            total_items=100, page_size=0, current_page=1
        )
        self.assertEqual(pagination_zero_ps["total_pages"], 0)


if __name__ == "__main__":
    unittest.main()
