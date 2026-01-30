from datetime import datetime, timezone
import pytest
import sys
from pathlib import Path

# TimeConverter 모듈을 직접 import
time_converter_path = Path(__file__).resolve().parents[4] / "src" / "candle_data_manager" / "Core" / "CandleFetcher" / "Core" / "TimeConverter"
sys.path.insert(0, str(time_converter_path))

from TimeConverter import TimeConverter


class TestTimeConverterToTimestamp:

    def test_string_date_to_timestamp(self):
        result = TimeConverter.mutate_to("2024-1-1", "timestamp")
        assert result == 1704067200

    def test_string_datetime_to_timestamp(self):
        result = TimeConverter.mutate_to("2025-1-5 5:12:39", "timestamp")
        assert result == 1736053959

    def test_sec_timestamp_to_timestamp(self):
        result = TimeConverter.mutate_to(1704067200, "timestamp")
        assert result == 1704067200

    def test_ms_timestamp_to_timestamp(self):
        result = TimeConverter.mutate_to(1704067200000, "timestamp")
        assert result == 1704067200

    def test_datetime_to_timestamp(self):
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = TimeConverter.mutate_to(dt, "timestamp")
        assert result == 1704067200


class TestTimeConverterToDatetime:

    def test_string_date_to_datetime(self):
        result = TimeConverter.mutate_to("2024-1-1", "datetime")
        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_string_datetime_to_datetime(self):
        result = TimeConverter.mutate_to("2025-1-5 5:12:39", "datetime")
        expected = datetime(2025, 1, 5, 5, 12, 39, tzinfo=timezone.utc)
        assert result == expected

    def test_sec_timestamp_to_datetime(self):
        result = TimeConverter.mutate_to(1704067200, "datetime")
        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_ms_timestamp_to_datetime(self):
        result = TimeConverter.mutate_to(1704067200000, "datetime")
        expected = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_datetime_to_datetime(self):
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        result = TimeConverter.mutate_to(dt, "datetime")
        assert result == dt


class TestTimeConverterEdgeCases:

    def test_various_string_formats(self):
        # 다양한 문자열 형식 지원
        result1 = TimeConverter.mutate_to("2021-5-3", "timestamp")
        assert result1 == 1620000000

        result2 = TimeConverter.mutate_to("2021-05-03", "timestamp")
        assert result2 == 1620000000

        result3 = TimeConverter.mutate_to("2021-5-3 10:30:45", "timestamp")
        assert result3 == 1620037845

    def test_different_timestamp_lengths(self):
        # 10자리 (sec)
        result1 = TimeConverter.mutate_to(1620000000, "timestamp")
        assert result1 == 1620000000

        # 13자리 (ms)
        result2 = TimeConverter.mutate_to(1620000000000, "timestamp")
        assert result2 == 1620000000

    def test_datetime_without_timezone(self):
        # timezone 없는 datetime은 UTC로 가정
        dt = datetime(2024, 1, 1, 0, 0, 0)
        result = TimeConverter.mutate_to(dt, "timestamp")
        assert result == 1704067200
