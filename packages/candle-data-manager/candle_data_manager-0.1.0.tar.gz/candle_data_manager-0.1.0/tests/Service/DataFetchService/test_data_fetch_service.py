import pytest
from unittest.mock import Mock, MagicMock
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Particles.ProviderNotImplementedError import ProviderNotImplementedError


@pytest.fixture
def mock_provider_registry():
    return Mock(spec=ProviderRegistry)


@pytest.fixture
def data_fetch_service(mock_provider_registry):
    return DataFetchService(mock_provider_registry)


@pytest.fixture
def sample_symbol():
    return Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )


def test_fetch_returns_data_from_provider(data_fetch_service, mock_provider_registry, sample_symbol):
    # Provider의 fetch 메서드가 호출되고 결과가 반환되는지 확인
    mock_provider = MagicMock()
    expected_data = [
        {"timestamp": 1609459200, "open": 29000, "high": 29500, "low": 28500, "close": 29200, "volume": 1000},
        {"timestamp": 1609462800, "open": 29200, "high": 29800, "low": 29000, "close": 29500, "volume": 1200}
    ]
    mock_provider.fetch.return_value = expected_data
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.fetch(sample_symbol, 1609459200, 1609466400)

    mock_provider_registry.get_provider.assert_called_once_with(sample_symbol)
    mock_provider.fetch.assert_called_once_with(sample_symbol, 1609459200, 1609466400)
    assert result == expected_data


def test_fetch_empty_result(data_fetch_service, mock_provider_registry, sample_symbol):
    # Provider가 빈 리스트를 반환하는 경우
    mock_provider = MagicMock()
    mock_provider.fetch.return_value = []
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.fetch(sample_symbol, 1609459200, 1609466400)

    assert result == []


def test_fetch_with_provider_not_implemented_error(data_fetch_service, mock_provider_registry, sample_symbol):
    # ProviderRegistry에서 Provider를 찾지 못한 경우
    mock_provider_registry.get_provider.side_effect = ProviderNotImplementedError("CRYPTO-UNKNOWN-SPOT")

    with pytest.raises(ProviderNotImplementedError):
        data_fetch_service.fetch(sample_symbol, 1609459200, 1609466400)


def test_fetch_all_data_returns_full_range(data_fetch_service, mock_provider_registry, sample_symbol):
    # fetch_all_data가 get_data_range를 호출하고 전체 범위 데이터를 가져오는지 확인
    mock_provider = MagicMock()
    oldest_ts = 1577836800  # 2020-01-01
    latest_ts = 1640995200  # 2022-01-01
    mock_provider.get_data_range.return_value = (oldest_ts, latest_ts)
    expected_data = [
        {"timestamp": oldest_ts, "open": 7000, "high": 7100, "low": 6900, "close": 7050, "volume": 500}
    ]
    mock_provider.fetch.return_value = expected_data
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.fetch_all_data(sample_symbol)

    mock_provider_registry.get_provider.assert_called_once_with(sample_symbol)
    mock_provider.get_data_range.assert_called_once_with(sample_symbol)
    mock_provider.fetch.assert_called_once_with(sample_symbol, oldest_ts, latest_ts)
    assert result == expected_data


def test_fetch_all_data_with_none_range(data_fetch_service, mock_provider_registry, sample_symbol):
    # get_data_range가 (None, None)을 반환하는 경우 빈 리스트 반환
    mock_provider = MagicMock()
    mock_provider.get_data_range.return_value = (None, None)
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.fetch_all_data(sample_symbol)

    mock_provider.get_data_range.assert_called_once_with(sample_symbol)
    mock_provider.fetch.assert_not_called()
    assert result == []


def test_fetch_all_data_with_partial_none_range(data_fetch_service, mock_provider_registry, sample_symbol):
    # get_data_range가 부분적으로 None을 반환하는 경우 (예: oldest만 있는 경우) 빈 리스트 반환
    mock_provider = MagicMock()
    mock_provider.get_data_range.return_value = (1577836800, None)
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.fetch_all_data(sample_symbol)

    mock_provider.get_data_range.assert_called_once_with(sample_symbol)
    mock_provider.fetch.assert_not_called()
    assert result == []


def test_get_market_list_calls_provider(data_fetch_service, mock_provider_registry):
    # get_market_list가 올바른 Provider를 선택하고 호출하는지 확인
    mock_provider = MagicMock()
    mock_provider.archetype = "CRYPTO"
    mock_provider.exchange = "BINANCE"
    mock_provider.tradetype = "SPOT"
    expected_market_list = [
        {"base": "BTC", "quote": "USDT", "timeframes": ["1m", "1h", "1d"], "listed_at": None, "full_name": "Bitcoin"},
        {"base": "ETH", "quote": "USDT", "timeframes": ["1m", "1h", "1d"], "listed_at": None, "full_name": "Ethereum"}
    ]
    mock_provider.get_market_list.return_value = expected_market_list
    mock_provider_registry.get_provider.return_value = mock_provider

    # archetype, exchange, tradetype으로 Symbol 생성하여 get_provider 호출
    result = data_fetch_service.get_market_list("CRYPTO", "BINANCE", "SPOT")

    # get_provider가 임시 Symbol로 호출되었는지 확인
    call_args = mock_provider_registry.get_provider.call_args
    called_symbol = call_args[0][0]
    assert called_symbol.archetype == "CRYPTO"
    assert called_symbol.exchange == "BINANCE"
    assert called_symbol.tradetype == "SPOT"

    mock_provider.get_market_list.assert_called_once()
    assert result == expected_market_list


def test_get_market_list_empty_result(data_fetch_service, mock_provider_registry):
    # Provider가 빈 마켓 리스트를 반환하는 경우
    mock_provider = MagicMock()
    mock_provider.archetype = "CRYPTO"
    mock_provider.exchange = "UPBIT"
    mock_provider.tradetype = "SPOT"
    mock_provider.get_market_list.return_value = []
    mock_provider_registry.get_provider.return_value = mock_provider

    result = data_fetch_service.get_market_list("CRYPTO", "UPBIT", "SPOT")

    assert result == []


def test_get_market_list_with_provider_not_implemented_error(data_fetch_service, mock_provider_registry):
    # 존재하지 않는 Provider를 요청한 경우
    mock_provider_registry.get_provider.side_effect = ProviderNotImplementedError("CRYPTO-UNKNOWN-SPOT")

    with pytest.raises(ProviderNotImplementedError):
        data_fetch_service.get_market_list("CRYPTO", "UNKNOWN", "SPOT")
