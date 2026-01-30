import pytest
from unittest.mock import Mock, patch

from candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider import BinanceSpotProvider
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Particles.NoApiKeyError import NoApiKeyError
from candle_data_manager.Particles.ServerNotRespondedError import ServerNotRespondedError


class TestBinanceSpotProviderInit:
    def test_init_success(self):
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.return_value = True

            provider = BinanceSpotProvider(mock_conn)

            assert provider is not None
            mock_api_service.get_api_key.assert_called_once_with("BINANCE")
            mock_api_service.get_api_secret.assert_called_once_with("BINANCE")
            mock_api_service.check_server.assert_called_once_with("BINANCE", "test_key")

    def test_init_no_api_key(self):
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.side_effect = NoApiKeyError("BINANCE")

            with pytest.raises(NoApiKeyError):
                BinanceSpotProvider(mock_conn)

    def test_init_no_api_secret(self):
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.side_effect = NoApiKeyError("BINANCE")

            with pytest.raises(NoApiKeyError):
                BinanceSpotProvider(mock_conn)

    def test_init_server_not_responded(self):
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.ApiValidationService') as MockApiValidation:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.side_effect = ServerNotRespondedError("BINANCE")

            with pytest.raises(ServerNotRespondedError):
                BinanceSpotProvider(mock_conn)


class TestBinanceSpotProviderFetch:
    @pytest.fixture
    def provider(self):
        mock_conn = Mock(spec=ConnectionManager)

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.ApiValidationService') as MockApiValidation, \
             patch('candle_data_manager.Core.CandleFetcher.Plugin.BinanceSpotProvider.Spot') as MockSpot:
            mock_api_service = MockApiValidation.return_value
            mock_api_service.get_api_key.return_value = "test_key"
            mock_api_service.get_api_secret.return_value = "test_secret"
            mock_api_service.check_server.return_value = True

            provider = BinanceSpotProvider(mock_conn)
            return provider

    @pytest.fixture
    def symbol(self):
        symbol = Symbol()
        symbol.id = 1
        symbol.exchange = "BINANCE"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1h"
        return symbol

    def test_fetch_hourly_candles(self, provider, symbol):
        mock_response = [
            [
                1704067200000,
                "42000.00",
                "42500.00",
                "41800.00",
                "42200.00",
                "1000.00",
                1704070799999,
                "42000000.00",
                308,
                "500.00",
                "21000000.00",
                "0"
            ],
            [
                1704070800000,
                "42100.00",
                "42600.00",
                "41900.00",
                "42300.00",
                "1100.00",
                1704074399999,
                "43000000.00",
                320,
                "550.00",
                "23000000.00",
                "0"
            ]
        ]

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
                'timestamp': 1704070800,
                'open': 4210000000000,
                'high': 4260000000000,
                'low': 4190000000000,
                'close': 4230000000000,
                'volume': 110000000000
            }
        ]

        provider._client.klines = Mock(return_value=mock_response)
        provider._normalization.normalize_binance_spot = Mock(return_value=normalized_data)
        provider._null_handling.handle = Mock(return_value=normalized_data)

        result = provider.fetch(symbol, 1704067200, 1704153600)

        assert len(result) == 2
        assert result[0]['timestamp'] == 1704067200
        assert result[0]['open'] == 4200000000000
        provider._client.klines.assert_called_once()
        provider._normalization.normalize_binance_spot.assert_called_once()
        provider._null_handling.handle.assert_called_once()

    def test_fetch_ticker_format(self, provider, symbol):
        mock_response = [
            [
                1704067200000,
                "42000.00",
                "42500.00",
                "41800.00",
                "42200.00",
                "1000.00",
                1704070799999,
                "42000000.00",
                308,
                "500.00",
                "21000000.00",
                "0"
            ]
        ]

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 4200000000000,
            'high': 4250000000000,
            'low': 4180000000000,
            'close': 4220000000000,
            'volume': 100000000000
        }]

        provider._client.klines = Mock(return_value=mock_response)
        provider._normalization.normalize_binance_spot = Mock(return_value=normalized_data)
        provider._null_handling.handle = Mock(return_value=normalized_data)

        provider.fetch(symbol, 1704067200, 1704153600)

        args = provider._client.klines.call_args
        assert args.kwargs['symbol'] == "BTCUSDT"

    def test_timeframe_mapping(self, provider):
        test_cases = [
            ("1m", "1m"),
            ("5m", "5m"),
            ("1h", "1h"),
            ("4h", "4h"),
            ("1d", "1d"),
        ]

        for timeframe, expected_interval in test_cases:
            symbol = Symbol()
            symbol.id = 1
            symbol.exchange = "BINANCE"
            symbol.base = "BTC"
            symbol.quote = "USDT"
            symbol.timeframe = timeframe

            mock_response = [[
                1704067200000,
                "42000.00",
                "42500.00",
                "41800.00",
                "42200.00",
                "1000.00",
                1704070799999,
                "42000000.00",
                308,
                "500.00",
                "21000000.00",
                "0"
            ]]

            provider._client.klines = Mock(return_value=mock_response)
            provider._normalization.normalize_binance_spot = Mock(return_value=[])
            provider._null_handling.handle = Mock(return_value=[])

            provider.fetch(symbol, 1704067200, 1704153600)

            args = provider._client.klines.call_args
            assert args.kwargs['interval'] == expected_interval

    def test_fetch_empty_response(self, provider, symbol):
        mock_response = []

        provider._client.klines = Mock(return_value=mock_response)
        provider._normalization.normalize_binance_spot = Mock(return_value=[])
        provider._null_handling.handle = Mock(return_value=[])

        result = provider.fetch(symbol, 1704067200, 1704153600)

        assert result == []

    def test_fetch_with_null_handling(self, provider, symbol):
        mock_response = [
            [
                1704067200000,
                "42000.00",
                "42500.00",
                "41800.00",
                "42200.00",
                "1000.00",
                1704070799999,
                "42000000.00",
                308,
                "500.00",
                "21000000.00",
                "0"
            ],
            [
                1704070800000,
                None,
                None,
                None,
                None,
                "0.00",
                1704074399999,
                "0.00",
                0,
                "0.00",
                "0.00",
                "0"
            ]
        ]

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
                'timestamp': 1704070800,
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
                'timestamp': 1704070800,
                'open': 4220000000000,
                'high': 4220000000000,
                'low': 4220000000000,
                'close': 4220000000000,
                'volume': 0
            }
        ]

        provider._client.klines = Mock(return_value=mock_response)
        provider._normalization.normalize_binance_spot = Mock(return_value=normalized_with_null)
        provider._null_handling.handle = Mock(return_value=normalized_handled)

        result = provider.fetch(symbol, 1704067200, 1704153600)

        assert result[1]['open'] == 4220000000000
        provider._null_handling.handle.assert_called_once_with(normalized_with_null, symbol)

    def test_timestamp_conversion(self, provider, symbol):
        mock_response = [[
            1704067200000,
            "42000.00",
            "42500.00",
            "41800.00",
            "42200.00",
            "1000.00",
            1704070799999,
            "42000000.00",
            308,
            "500.00",
            "21000000.00",
            "0"
        ]]

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 4200000000000,
            'high': 4250000000000,
            'low': 4180000000000,
            'close': 4220000000000,
            'volume': 100000000000
        }]

        provider._client.klines = Mock(return_value=mock_response)
        provider._normalization.normalize_binance_spot = Mock(return_value=normalized_data)
        provider._null_handling.handle = Mock(return_value=normalized_data)

        provider.fetch(symbol, 1704067200, 1704153600)

        args = provider._client.klines.call_args
        assert args.kwargs['startTime'] == 1704067200000
        assert args.kwargs['endTime'] == 1704153600000
