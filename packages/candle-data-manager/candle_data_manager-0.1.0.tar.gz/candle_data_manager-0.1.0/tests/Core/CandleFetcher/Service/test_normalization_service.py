import pytest
import pandas as pd
from datetime import datetime, timezone

from candle_data_manager.Core.CandleFetcher.Service.NormalizationService.NormalizationService import NormalizationService
from candle_data_manager.Core.Models.CandleRepository import CandleRepository


class TestNormalizeBinance:

    def test_basic_normalization(self):
        # Binance 형식 raw 데이터
        raw_data = [
            {
                "t": 1704067200000,  # ms
                "o": "42000.5",
                "h": "42500.0",
                "l": "41800.0",
                "c": "42200.0",
                "v": "1000.0"
            }
        ]

        service = NormalizationService()
        result = service.normalize_binance(raw_data)

        assert len(result) == 1
        assert result[0]["timestamp"] == 1704067200  # sec
        assert result[0]["open"] == CandleRepository.to_storage(42000.5)
        assert result[0]["high"] == CandleRepository.to_storage(42500.0)
        assert result[0]["low"] == CandleRepository.to_storage(41800.0)
        assert result[0]["close"] == CandleRepository.to_storage(42200.0)
        assert result[0]["volume"] == CandleRepository.to_storage(1000.0)

    def test_multiple_candles(self):
        raw_data = [
            {"t": 1704067200000, "o": "100.0", "h": "110.0", "l": "90.0", "c": "105.0", "v": "500.0"},
            {"t": 1704070800000, "o": "105.0", "h": "120.0", "l": "100.0", "c": "115.0", "v": "600.0"}
        ]

        service = NormalizationService()
        result = service.normalize_binance(raw_data)

        assert len(result) == 2
        assert result[0]["timestamp"] == 1704067200
        assert result[1]["timestamp"] == 1704070800

    def test_decimal_precision(self):
        # 소수점 정밀도 테스트
        raw_data = [
            {"t": 1704067200000, "o": "0.123456789", "h": "0.2", "l": "0.1", "c": "0.15", "v": "1000.123"}
        ]

        service = NormalizationService()
        result = service.normalize_binance(raw_data)

        assert result[0]["open"] == CandleRepository.to_storage(0.123456789)
        assert result[0]["close"] == CandleRepository.to_storage(0.15)

    def test_empty_list(self):
        service = NormalizationService()
        result = service.normalize_binance([])
        assert result == []


class TestNormalizeUpbit:

    def test_basic_normalization(self):
        raw_data = [
            {
                "timestamp": 1704067200000,  # ms
                "opening_price": 42000.5,
                "high_price": 42500.0,
                "low_price": 41800.0,
                "trade_price": 42200.0,
                "candle_acc_trade_volume": 1000.0
            }
        ]

        service = NormalizationService()
        result = service.normalize_upbit(raw_data)

        assert len(result) == 1
        assert result[0]["timestamp"] == 1704067200  # sec
        assert result[0]["open"] == CandleRepository.to_storage(42000.5)
        assert result[0]["high"] == CandleRepository.to_storage(42500.0)
        assert result[0]["low"] == CandleRepository.to_storage(41800.0)
        assert result[0]["close"] == CandleRepository.to_storage(42200.0)
        assert result[0]["volume"] == CandleRepository.to_storage(1000.0)

    def test_multiple_candles(self):
        raw_data = [
            {
                "timestamp": 1704067200000,
                "opening_price": 100.0,
                "high_price": 110.0,
                "low_price": 90.0,
                "trade_price": 105.0,
                "candle_acc_trade_volume": 500.0
            },
            {
                "timestamp": 1704070800000,
                "opening_price": 105.0,
                "high_price": 120.0,
                "low_price": 100.0,
                "trade_price": 115.0,
                "candle_acc_trade_volume": 600.0
            }
        ]

        service = NormalizationService()
        result = service.normalize_upbit(raw_data)

        assert len(result) == 2
        assert result[0]["timestamp"] == 1704067200
        assert result[1]["timestamp"] == 1704070800

    def test_empty_list(self):
        service = NormalizationService()
        result = service.normalize_upbit([])
        assert result == []


class TestNormalizeFdr:

    def test_basic_normalization(self):
        # FDR DataFrame
        df = pd.DataFrame({
            "Open": [42000.5],
            "High": [42500.0],
            "Low": [41800.0],
            "Close": [42200.0],
            "Volume": [1000.0]
        }, index=[pd.Timestamp('2024-01-01', tz='UTC')])

        service = NormalizationService()
        result = service.normalize_fdr(df)

        assert len(result) == 1
        assert result[0]["timestamp"] == int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        assert result[0]["open"] == CandleRepository.to_storage(42000.5)
        assert result[0]["high"] == CandleRepository.to_storage(42500.0)
        assert result[0]["low"] == CandleRepository.to_storage(41800.0)
        assert result[0]["close"] == CandleRepository.to_storage(42200.0)
        assert result[0]["volume"] == CandleRepository.to_storage(1000.0)

    def test_multiple_rows(self):
        df = pd.DataFrame({
            "Open": [100.0, 105.0],
            "High": [110.0, 120.0],
            "Low": [90.0, 100.0],
            "Close": [105.0, 115.0],
            "Volume": [500.0, 600.0]
        }, index=[
            pd.Timestamp('2024-01-01', tz='UTC'),
            pd.Timestamp('2024-01-02', tz='UTC')
        ])

        service = NormalizationService()
        result = service.normalize_fdr(df)

        assert len(result) == 2
        assert result[0]["timestamp"] == int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp())
        assert result[1]["timestamp"] == int(datetime(2024, 1, 2, tzinfo=timezone.utc).timestamp())

    def test_date_string(self):
        # index가 string인 경우도 처리
        df = pd.DataFrame({
            "Open": [42000.5],
            "High": [42500.0],
            "Low": [41800.0],
            "Close": [42200.0],
            "Volume": [1000.0]
        }, index=pd.DatetimeIndex(['2024-01-01']))

        service = NormalizationService()
        result = service.normalize_fdr(df)

        assert len(result) == 1
        assert isinstance(result[0]["timestamp"], int)
        assert result[0]["timestamp"] > 0

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])

        service = NormalizationService()
        result = service.normalize_fdr(df)

        assert result == []
