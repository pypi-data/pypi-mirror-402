import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime

from candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider import UpbitProvider
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Particles.NoApiKeyError import NoApiKeyError
from candle_data_manager.Particles.ServerNotRespondedError import ServerNotRespondedError
from candle_data_manager.Particles.InvalidDataError import InvalidDataError


class TestUpbitProviderInit:
    def test_init_success(self):
        # Mock 설정
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.return_value = True

            # 실행
            provider = UpbitProvider(mock_conn)

            # 검증
            assert provider is not None
            mock_api_service.get_api_key.assert_called_once_with("UPBIT")
            mock_api_service.get_api_secret.assert_called_once_with("UPBIT")
            mock_api_service.check_server.assert_called_once_with("UPBIT", "test_key")

    def test_init_no_api_key(self):
        # Mock 설정
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.side_effect = NoApiKeyError("UPBIT")

            # 실행 및 검증
            with pytest.raises(NoApiKeyError):
                UpbitProvider(mock_conn)

    def test_init_no_api_secret(self):
        # Mock 설정
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.side_effect = NoApiKeyError("UPBIT")

            # 실행 및 검증
            with pytest.raises(NoApiKeyError):
                UpbitProvider(mock_conn)

    def test_init_server_not_responded(self):
        # Mock 설정
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.side_effect = ServerNotRespondedError("UPBIT")

            # 실행 및 검증
            with pytest.raises(ServerNotRespondedError):
                UpbitProvider(mock_conn)


class TestUpbitProviderFetch:
    @pytest.fixture
    def provider(self):
        # Provider 생성
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.return_value = True

            provider = UpbitProvider(mock_conn)
            return provider

    @pytest.fixture
    def symbol(self):
        # Symbol 생성
        symbol = Symbol()
        symbol.id = 1
        symbol.exchange = "UPBIT"
        symbol.base = "BTC"
        symbol.quote = "KRW"
        symbol.timeframe = "1d"
        return symbol

    def test_fetch_daily_candles(self, provider, symbol):
        # pyupbit 응답 Mock (DataFrame)
        mock_df = pd.DataFrame({
            'open': [42000.0, 42100.0],
            'high': [42500.0, 42600.0],
            'low': [41800.0, 41900.0],
            'close': [42200.0, 42300.0],
            'volume': [1000.0, 1100.0],
            'value': [42000000.0, 43000000.0]
        }, index=[
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02')
        ])

        # NormalizationService Mock
        normalized_data = [
            {
                'timestamp': 1704067200,
                'open': 4200000000000,
                'high': 4250000000000,
                'low': 4180000000000,
                'close': 4220000000000,
                'volume': 100000000000
            },
            {
                'timestamp': 1704153600,
                'open': 4210000000000,
                'high': 4260000000000,
                'low': 4190000000000,
                'close': 4230000000000,
                'volume': 110000000000
            }
        ]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            # 실행
            result = provider.fetch(symbol, 1704067200, 1704153600)

            # 검증
            assert len(result) == 2
            assert result[0]['timestamp'] == 1704067200
            assert result[0]['open'] == 4200000000000
            mock_pyupbit.get_ohlcv.assert_called_once()
            provider._normalization.normalize_upbit.assert_called_once()
            provider._null_handling.handle.assert_called_once()

    def test_fetch_minute_candles(self, provider, symbol):
        # Symbol timeframe 변경
        symbol.timeframe = "1m"

        # pyupbit 응답 Mock
        mock_df = pd.DataFrame({
            'open': [42000.0],
            'high': [42100.0],
            'low': [41900.0],
            'close': [42050.0],
            'volume': [100.0],
            'value': [4200000.0]
        }, index=[pd.Timestamp('2024-01-01 00:00:00')])

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 4200000000000,
            'high': 4210000000000,
            'low': 4190000000000,
            'close': 4205000000000,
            'volume': 10000000000
        }]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            # 실행
            result = provider.fetch(symbol, 1704067200, 1704153600)

            # 검증
            assert len(result) == 1
            args = mock_pyupbit.get_ohlcv.call_args
            assert args[1]['interval'] == "minute1"

    def test_fetch_4hour_candles(self, provider, symbol):
        # Symbol timeframe 변경
        symbol.timeframe = "4h"

        mock_df = pd.DataFrame({
            'open': [42000.0],
            'high': [42500.0],
            'low': [41800.0],
            'close': [42200.0],
            'volume': [1000.0],
            'value': [42000000.0]
        }, index=[pd.Timestamp('2024-01-01 00:00:00')])

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 4200000000000,
            'high': 4250000000000,
            'low': 4180000000000,
            'close': 4220000000000,
            'volume': 100000000000
        }]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            # 실행
            result = provider.fetch(symbol, 1704067200, 1704153600)

            # 검증
            args = mock_pyupbit.get_ohlcv.call_args
            assert args[1]['interval'] == "minute240"

    def test_fetch_ticker_format(self, provider, symbol):
        # Ticker 형식 확인 (KRW-BTC)
        mock_df = pd.DataFrame({
            'open': [42000.0],
            'high': [42500.0],
            'low': [41800.0],
            'close': [42200.0],
            'volume': [1000.0],
            'value': [42000000.0]
        }, index=[pd.Timestamp('2024-01-01')])

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 4200000000000,
            'high': 4250000000000,
            'low': 4180000000000,
            'close': 4220000000000,
            'volume': 100000000000
        }]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            # 실행
            provider.fetch(symbol, 1704067200, 1704153600)

            # 검증 - ticker는 "KRW-BTC" 형식
            args = mock_pyupbit.get_ohlcv.call_args
            assert args.kwargs['ticker'] == "KRW-BTC"

    def test_fetch_empty_response(self, provider, symbol):
        # 빈 응답
        mock_df = pd.DataFrame()

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=[])
            provider._null_handling.handle = Mock(return_value=[])

            # 실행
            result = provider.fetch(symbol, 1704067200, 1704153600)

            # 검증
            assert result == []

    def test_fetch_with_null_handling(self, provider, symbol):
        # Null이 포함된 데이터
        mock_df = pd.DataFrame({
            'open': [42000.0, None],
            'high': [42500.0, None],
            'low': [41800.0, None],
            'close': [42200.0, None],
            'volume': [1000.0, 0.0],
            'value': [42000000.0, 0.0]
        }, index=[
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02')
        ])

        normalized_with_null = [
            {
                'timestamp': 1704067200,
                'open': 4200000000000,
                'high': 4250000000000,
                'low': 4180000000000,
                'close': 4220000000000,
                'volume': 100000000000
            },
            {
                'timestamp': 1704153600,
                'open': None,
                'high': None,
                'low': None,
                'close': None,
                'volume': 0
            }
        ]

        normalized_handled = [
            {
                'timestamp': 1704067200,
                'open': 4200000000000,
                'high': 4250000000000,
                'low': 4180000000000,
                'close': 4220000000000,
                'volume': 100000000000
            },
            {
                'timestamp': 1704153600,
                'open': 4220000000000,
                'high': 4220000000000,
                'low': 4220000000000,
                'close': 4220000000000,
                'volume': 0
            }
        ]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
            mock_pyupbit.get_ohlcv.return_value = mock_df
            provider._normalization.normalize_upbit = Mock(return_value=normalized_with_null)
            provider._null_handling.handle = Mock(return_value=normalized_handled)

            # 실행
            result = provider.fetch(symbol, 1704067200, 1704153600)

            # 검증
            assert result[1]['open'] == 4220000000000
            provider._null_handling.handle.assert_called_once_with(normalized_with_null, symbol)

    def test_timeframe_mapping(self, provider):
        # 다양한 timeframe 매핑 테스트
        test_cases = [
            ("1m", "minute1"),
            ("3m", "minute3"),
            ("5m", "minute5"),
            ("10m", "minute10"),
            ("30m", "minute30"),
            ("1h", "minute60"),
            ("4h", "minute240"),
            ("1d", "day"),
            ("1w", "week"),
        ]

        for timeframe, expected_interval in test_cases:
            symbol = Symbol()
            symbol.id = 1
            symbol.exchange = "UPBIT"
            symbol.base = "BTC"
            symbol.quote = "KRW"
            symbol.timeframe = timeframe

            mock_df = pd.DataFrame({
                'open': [42000.0],
                'high': [42500.0],
                'low': [41800.0],
                'close': [42200.0],
                'volume': [1000.0],
                'value': [42000000.0]
            }, index=[pd.Timestamp('2024-01-01')])

            with patch('candle_data_manager.Core.CandleFetcher.Plugin.UpbitProvider.pyupbit') as mock_pyupbit:
                mock_pyupbit.get_ohlcv.return_value = mock_df
                provider._normalization.normalize_upbit = Mock(return_value=[])
                provider._null_handling.handle = Mock(return_value=[])

                # 실행
                provider.fetch(symbol, 1704067200, 1704153600)

                # 검증
                args = mock_pyupbit.get_ohlcv.call_args
                assert args[1]['interval'] == expected_interval
