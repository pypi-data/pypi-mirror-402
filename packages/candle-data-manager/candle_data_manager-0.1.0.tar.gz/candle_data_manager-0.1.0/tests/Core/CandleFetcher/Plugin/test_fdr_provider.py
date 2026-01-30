import pytest
from unittest.mock import Mock, patch
import pandas as pd
from datetime import datetime

from candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider import FdrProvider
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol


class TestFdrProviderInit:
    def test_init_success(self):
        mock_conn = Mock(spec=ConnectionManager)

        provider = FdrProvider(mock_conn)

        assert provider is not None
        assert provider._normalization is not None
        assert provider._null_handling is not None


class TestFdrProviderFetch:
    @pytest.fixture
    def provider(self):
        mock_conn = Mock(spec=ConnectionManager)
        provider = FdrProvider(mock_conn)
        return provider

    @pytest.fixture
    def symbol(self):
        symbol = Symbol()
        symbol.id = 1
        symbol.archetype = "STOCK"
        symbol.exchange = "KRX"
        symbol.tradetype = "SPOT"
        symbol.base = "005930"
        symbol.quote = "KRW"
        symbol.timeframe = "1d"
        return symbol

    def test_fetch_daily_candles(self, provider, symbol):
        mock_df = pd.DataFrame({
            'Open': [70000.0, 70500.0],
            'High': [71000.0, 71500.0],
            'Low': [69500.0, 70000.0],
            'Close': [70500.0, 71000.0],
            'Volume': [10000000.0, 10500000.0],
            'Change': [0.5, 0.7]
        }, index=[
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02')
        ])

        normalized_data = [
            {
                'timestamp': 1704067200,
                'open': 7000000000000,
                'high': 7100000000000,
                'low': 6950000000000,
                'close': 7050000000000,
                'volume': 1000000000000000
            },
            {
                'timestamp': 1704153600,
                'open': 7050000000000,
                'high': 7150000000000,
                'low': 7000000000000,
                'close': 7100000000000,
                'volume': 1050000000000000
            }
        ]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider.fdr') as mock_fdr:
            mock_fdr.DataReader.return_value = mock_df
            provider._normalization.normalize_fdr = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            result = provider.fetch(symbol, 1704067200, 1704153600)

            assert len(result) == 2
            assert result[0]['timestamp'] == 1704067200
            assert result[0]['open'] == 7000000000000
            mock_fdr.DataReader.assert_called_once()
            provider._normalization.normalize_fdr.assert_called_once()
            provider._null_handling.handle.assert_called_once()

    def test_fetch_ticker_format(self, provider, symbol):
        mock_df = pd.DataFrame({
            'Open': [70000.0],
            'High': [71000.0],
            'Low': [69500.0],
            'Close': [70500.0],
            'Volume': [10000000.0],
            'Change': [0.5]
        }, index=[pd.Timestamp('2024-01-01')])

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 7000000000000,
            'high': 7100000000000,
            'low': 6950000000000,
            'close': 7050000000000,
            'volume': 1000000000000000
        }]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider.fdr') as mock_fdr:
            mock_fdr.DataReader.return_value = mock_df
            provider._normalization.normalize_fdr = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            provider.fetch(symbol, 1704067200, 1704153600)

            args = mock_fdr.DataReader.call_args
            assert args[0][0] == "005930"

    def test_fetch_empty_response(self, provider, symbol):
        mock_df = pd.DataFrame()

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider.fdr') as mock_fdr:
            mock_fdr.DataReader.return_value = mock_df

            result = provider.fetch(symbol, 1704067200, 1704153600)

            assert result == []

    def test_fetch_with_null_handling(self, provider, symbol):
        mock_df = pd.DataFrame({
            'Open': [70000.0, None],
            'High': [71000.0, None],
            'Low': [69500.0, None],
            'Close': [70500.0, None],
            'Volume': [10000000.0, 0.0],
            'Change': [0.5, 0.0]
        }, index=[
            pd.Timestamp('2024-01-01'),
            pd.Timestamp('2024-01-02')
        ])

        normalized_with_null = [
            {
                'timestamp': 1704067200,
                'open': 7000000000000,
                'high': 7100000000000,
                'low': 6950000000000,
                'close': 7050000000000,
                'volume': 1000000000000000
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
                'open': 7000000000000,
                'high': 7100000000000,
                'low': 6950000000000,
                'close': 7050000000000,
                'volume': 1000000000000000
            },
            {
                'timestamp': 1704153600,
                'open': 7050000000000,
                'high': 7050000000000,
                'low': 7050000000000,
                'close': 7050000000000,
                'volume': 0
            }
        ]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider.fdr') as mock_fdr:
            mock_fdr.DataReader.return_value = mock_df
            provider._normalization.normalize_fdr = Mock(return_value=normalized_with_null)
            provider._null_handling.handle = Mock(return_value=normalized_handled)

            result = provider.fetch(symbol, 1704067200, 1704153600)

            assert result[1]['open'] == 7050000000000
            provider._null_handling.handle.assert_called_once_with(normalized_with_null, symbol)

    def test_timestamp_conversion(self, provider, symbol):
        mock_df = pd.DataFrame({
            'Open': [70000.0],
            'High': [71000.0],
            'Low': [69500.0],
            'Close': [70500.0],
            'Volume': [10000000.0],
            'Change': [0.5]
        }, index=[pd.Timestamp('2024-01-01')])

        normalized_data = [{
            'timestamp': 1704067200,
            'open': 7000000000000,
            'high': 7100000000000,
            'low': 6950000000000,
            'close': 7050000000000,
            'volume': 1000000000000000
        }]

        with patch('candle_data_manager.Core.CandleFetcher.Plugin.FdrProvider.fdr') as mock_fdr:
            mock_fdr.DataReader.return_value = mock_df
            provider._normalization.normalize_fdr = Mock(return_value=normalized_data)
            provider._null_handling.handle = Mock(return_value=normalized_data)

            provider.fetch(symbol, 1704067200, 1704153600)

            call_args = mock_fdr.DataReader.call_args
            assert isinstance(call_args[0][1], datetime)
            assert isinstance(call_args[0][2], datetime)
