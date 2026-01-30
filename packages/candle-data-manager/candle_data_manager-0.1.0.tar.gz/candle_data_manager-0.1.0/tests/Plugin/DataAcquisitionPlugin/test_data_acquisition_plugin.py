import pytest
from unittest.mock import Mock, MagicMock
from candle_data_manager.Plugin.DataAcquisitionPlugin.DataAcquisitionPlugin import DataAcquisitionPlugin
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Service.DataSaveService.DataSaveService import DataSaveService
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_fetch_service():
    return Mock(spec=DataFetchService)


@pytest.fixture
def mock_save_service():
    return Mock(spec=DataSaveService)


@pytest.fixture
def data_acquisition_plugin(mock_fetch_service, mock_save_service):
    return DataAcquisitionPlugin(mock_fetch_service, mock_save_service)


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


def test_acquire_and_save_fetches_and_saves_data(data_acquisition_plugin, mock_fetch_service, mock_save_service, sample_symbol):
    # DataFetchService.fetch()로 데이터 획득 후 DataSaveService.save()로 저장
    start_at = 1609459200  # 2021-01-01 00:00:00
    end_at = 1609545600    # 2021-01-02 00:00:00

    expected_data = [
        {"timestamp": 1609459200, "open": 29000, "high": 29500, "low": 28500, "close": 29200, "volume": 1000},
        {"timestamp": 1609462800, "open": 29200, "high": 29800, "low": 29000, "close": 29500, "volume": 1200}
    ]
    mock_fetch_service.fetch.return_value = expected_data

    data_acquisition_plugin.acquire_and_save(sample_symbol, start_at, end_at)

    # fetch 호출 확인
    mock_fetch_service.fetch.assert_called_once_with(sample_symbol, start_at, end_at)

    # save 호출 확인
    mock_save_service.save.assert_called_once_with(sample_symbol, expected_data)


def test_acquire_and_save_with_empty_data(data_acquisition_plugin, mock_fetch_service, mock_save_service, sample_symbol):
    # 빈 데이터를 가져온 경우에도 save 호출
    start_at = 1609459200
    end_at = 1609545600

    mock_fetch_service.fetch.return_value = []

    data_acquisition_plugin.acquire_and_save(sample_symbol, start_at, end_at)

    mock_fetch_service.fetch.assert_called_once_with(sample_symbol, start_at, end_at)
    mock_save_service.save.assert_called_once_with(sample_symbol, [])


def test_acquire_and_save_propagates_fetch_error(data_acquisition_plugin, mock_fetch_service, mock_save_service, sample_symbol):
    # fetch 중 예외 발생 시 상위로 전파
    start_at = 1609459200
    end_at = 1609545600

    mock_fetch_service.fetch.side_effect = Exception("Network error")

    with pytest.raises(Exception, match="Network error"):
        data_acquisition_plugin.acquire_and_save(sample_symbol, start_at, end_at)

    # save는 호출되지 않아야 함
    mock_save_service.save.assert_not_called()


def test_acquire_and_save_propagates_save_error(data_acquisition_plugin, mock_fetch_service, mock_save_service, sample_symbol):
    # save 중 예외 발생 시 상위로 전파
    start_at = 1609459200
    end_at = 1609545600

    expected_data = [
        {"timestamp": 1609459200, "open": 29000, "high": 29500, "low": 28500, "close": 29200, "volume": 1000}
    ]
    mock_fetch_service.fetch.return_value = expected_data
    mock_save_service.save.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        data_acquisition_plugin.acquire_and_save(sample_symbol, start_at, end_at)

    # fetch는 호출되어야 함
    mock_fetch_service.fetch.assert_called_once_with(sample_symbol, start_at, end_at)
