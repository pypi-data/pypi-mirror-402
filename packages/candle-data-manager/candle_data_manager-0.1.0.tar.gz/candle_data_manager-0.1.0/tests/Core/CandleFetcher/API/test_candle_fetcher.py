import pytest
from unittest.mock import Mock, MagicMock, patch

from candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher import CandleFetcher
from candle_data_manager.Particles.ProviderNotImplementedError import ProviderNotImplementedError
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager


class TestCandleFetcherInit:
    def test_initialization(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        assert fetcher._conn_manager == conn_manager
        assert fetcher._providers == {}


class TestCandleFetcherProviderSelection:
    def test_binance_spot_provider(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_binance_futures_provider(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "FUTURES"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceFuturesProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_upbit_provider(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "UPBIT"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "KRW"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.UpbitProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_fdr_provider_krx(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "KRX"
        symbol.tradetype = "SPOT"
        symbol.base = "005930"
        symbol.quote = "KRW"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.FdrProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_fdr_provider_nyse(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "NYSE"
        symbol.tradetype = "SPOT"
        symbol.base = "AAPL"
        symbol.quote = "USD"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.FdrProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_fdr_provider_nasdaq(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "NASDAQ"
        symbol.tradetype = "SPOT"
        symbol.base = "TSLA"
        symbol.quote = "USD"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.FdrProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            mock_instance.fetch.assert_called_once()

    def test_unsupported_exchange(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "UNKNOWN"
        symbol.tradetype = "SPOT"

        with pytest.raises(ProviderNotImplementedError) as exc_info:
            fetcher.fetch(symbol, 1704067200, 1704153600)

        assert exc_info.value.exchange == "UNKNOWN"


class TestCandleFetcherProviderCaching:
    def test_same_exchange_reuses_provider(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol1 = Mock(spec=Symbol)
        symbol1.exchange = "BINANCE"
        symbol1.tradetype = "SPOT"
        symbol1.base = "BTC"
        symbol1.quote = "USDT"
        symbol1.timeframe = "1d"

        symbol2 = Mock(spec=Symbol)
        symbol2.exchange = "BINANCE"
        symbol2.tradetype = "SPOT"
        symbol2.base = "ETH"
        symbol2.quote = "USDT"
        symbol2.timeframe = "1h"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            fetcher.fetch(symbol1, 1704067200, 1704153600)
            fetcher.fetch(symbol2, 1704067200, 1704153600)

            MockProvider.assert_called_once_with(conn_manager)
            assert mock_instance.fetch.call_count == 2

    def test_different_exchanges_use_different_providers(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol1 = Mock(spec=Symbol)
        symbol1.exchange = "BINANCE"
        symbol1.tradetype = "SPOT"
        symbol1.base = "BTC"
        symbol1.quote = "USDT"
        symbol1.timeframe = "1d"

        symbol2 = Mock(spec=Symbol)
        symbol2.exchange = "UPBIT"
        symbol2.tradetype = "SPOT"
        symbol2.base = "BTC"
        symbol2.quote = "KRW"
        symbol2.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockBinance, \
             patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.UpbitProvider') as MockUpbit:
            mock_binance_instance = MagicMock()
            mock_binance_instance.fetch.return_value = []
            MockBinance.return_value = mock_binance_instance

            mock_upbit_instance = MagicMock()
            mock_upbit_instance.fetch.return_value = []
            MockUpbit.return_value = mock_upbit_instance

            fetcher.fetch(symbol1, 1704067200, 1704153600)
            fetcher.fetch(symbol2, 1704067200, 1704153600)

            MockBinance.assert_called_once_with(conn_manager)
            MockUpbit.assert_called_once_with(conn_manager)
            mock_binance_instance.fetch.assert_called_once()
            mock_upbit_instance.fetch.assert_called_once()

    def test_binance_spot_and_futures_separate_cache(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol1 = Mock(spec=Symbol)
        symbol1.exchange = "BINANCE"
        symbol1.tradetype = "SPOT"
        symbol1.base = "BTC"
        symbol1.quote = "USDT"
        symbol1.timeframe = "1d"

        symbol2 = Mock(spec=Symbol)
        symbol2.exchange = "BINANCE"
        symbol2.tradetype = "FUTURES"
        symbol2.base = "BTC"
        symbol2.quote = "USDT"
        symbol2.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockSpot, \
             patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceFuturesProvider') as MockFutures:
            mock_spot_instance = MagicMock()
            mock_spot_instance.fetch.return_value = []
            MockSpot.return_value = mock_spot_instance

            mock_futures_instance = MagicMock()
            mock_futures_instance.fetch.return_value = []
            MockFutures.return_value = mock_futures_instance

            fetcher.fetch(symbol1, 1704067200, 1704153600)
            fetcher.fetch(symbol2, 1704067200, 1704153600)

            MockSpot.assert_called_once_with(conn_manager)
            MockFutures.assert_called_once_with(conn_manager)
            mock_spot_instance.fetch.assert_called_once()
            mock_futures_instance.fetch.assert_called_once()


class TestCandleFetcherTimeConversion:
    def test_string_time_conversion(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider, \
             patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.TimeConverter') as MockTimeConverter:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            MockTimeConverter.mutate_to.side_effect = lambda val, to_type: 1704067200 if val == "2021-5-3" else 1704153600

            fetcher.fetch(symbol, "2021-5-3", "2021-5-4")

            assert MockTimeConverter.mutate_to.call_count == 2
            MockTimeConverter.mutate_to.assert_any_call("2021-5-3", "timestamp")
            MockTimeConverter.mutate_to.assert_any_call("2021-5-4", "timestamp")

    def test_int_seconds_no_conversion(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider, \
             patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.TimeConverter') as MockTimeConverter:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            MockTimeConverter.mutate_to.side_effect = lambda val, to_type: val

            fetcher.fetch(symbol, 1704067200, 1704153600)

            mock_instance.fetch.assert_called_once_with(symbol, 1704067200, 1704153600)

    def test_int_milliseconds_conversion(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider, \
             patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.TimeConverter') as MockTimeConverter:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = []
            MockProvider.return_value = mock_instance

            MockTimeConverter.mutate_to.side_effect = lambda val, to_type: val // 1000 if val > 10000000000 else val

            fetcher.fetch(symbol, 1704067200000, 1704153600000)

            assert MockTimeConverter.mutate_to.call_count == 2


class TestCandleFetcherIntegration:
    def test_fetch_returns_normalized_data(self):
        conn_manager = Mock(spec=ConnectionManager)
        fetcher = CandleFetcher(conn_manager)

        symbol = Mock(spec=Symbol)
        symbol.exchange = "BINANCE"
        symbol.tradetype = "SPOT"
        symbol.base = "BTC"
        symbol.quote = "USDT"
        symbol.timeframe = "1d"

        expected_data = [
            {
                'timestamp': 1704067200,
                'open': 4200000000000,
                'high': 4250000000000,
                'low': 4150000000000,
                'close': 4200000000000,
                'volume': 100000000000
            }
        ]

        with patch('candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher.BinanceSpotProvider') as MockProvider:
            mock_instance = MagicMock()
            mock_instance.fetch.return_value = expected_data
            MockProvider.return_value = mock_instance

            result = fetcher.fetch(symbol, 1704067200, 1704153600)

            assert result == expected_data
            mock_instance.fetch.assert_called_once_with(symbol, 1704067200, 1704153600)
