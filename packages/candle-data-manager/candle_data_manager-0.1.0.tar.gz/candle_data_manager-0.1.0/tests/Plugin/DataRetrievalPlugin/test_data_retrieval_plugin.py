import pytest
import pandas as pd
from unittest.mock import Mock

from candle_data_manager.Plugin.DataRetrievalPlugin.DataRetrievalPlugin import DataRetrievalPlugin
from candle_data_manager.Service.DataLoadService.DataLoadService import DataLoadService
from candle_data_manager.Plugin.DataAcquisitionPlugin.DataAcquisitionPlugin import DataAcquisitionPlugin
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_load_service():
    return Mock(spec=DataLoadService)


@pytest.fixture
def mock_acquisition_plugin():
    return Mock(spec=DataAcquisitionPlugin)


@pytest.fixture
def data_retrieval_plugin(mock_load_service, mock_acquisition_plugin):
    return DataRetrievalPlugin(mock_load_service, mock_acquisition_plugin)


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


def test_load_with_auto_fetch_returns_existing_data(
    data_retrieval_plugin, mock_load_service, mock_acquisition_plugin, sample_symbol
):
    # Given: 데이터가 이미 존재하는 경우
    start_at = 1609459200
    end_at = 1609545600

    expected_df = pd.DataFrame({
        'timestamp': [1609459200, 1609462800],
        'open': [29000.0, 29200.0],
        'high': [29500.0, 29800.0],
        'low': [28500.0, 29000.0],
        'close': [29200.0, 29500.0],
        'volume': [1000.0, 1200.0]
    })

    mock_load_service.load.return_value = expected_df

    # When: load_with_auto_fetch 호출
    result = data_retrieval_plugin.load_with_auto_fetch(sample_symbol, start_at, end_at)

    # Then: load가 한번만 호출됨
    mock_load_service.load.assert_called_once_with(sample_symbol, start_at, end_at)

    # Then: acquire_and_save는 호출되지 않음
    mock_acquisition_plugin.acquire_and_save.assert_not_called()

    # Then: 기존 데이터 반환
    pd.testing.assert_frame_equal(result, expected_df)


def test_load_with_auto_fetch_acquires_data_when_empty(
    data_retrieval_plugin, mock_load_service, mock_acquisition_plugin, sample_symbol
):
    # Given: 첫 번째 load는 빈 DataFrame 반환
    start_at = 1609459200
    end_at = 1609545600

    empty_df = pd.DataFrame()

    acquired_df = pd.DataFrame({
        'timestamp': [1609459200, 1609462800],
        'open': [29000.0, 29200.0],
        'high': [29500.0, 29800.0],
        'low': [28500.0, 29000.0],
        'close': [29200.0, 29500.0],
        'volume': [1000.0, 1200.0]
    })

    # 첫 번째 호출: 빈 DataFrame, 두 번째 호출: 데이터 있음
    mock_load_service.load.side_effect = [empty_df, acquired_df]

    # When: load_with_auto_fetch 호출
    result = data_retrieval_plugin.load_with_auto_fetch(sample_symbol, start_at, end_at)

    # Then: load가 두 번 호출됨 (전후)
    assert mock_load_service.load.call_count == 2
    mock_load_service.load.assert_any_call(sample_symbol, start_at, end_at)

    # Then: acquire_and_save가 호출됨
    mock_acquisition_plugin.acquire_and_save.assert_called_once_with(
        sample_symbol, start_at, end_at
    )

    # Then: 획득한 데이터 반환
    pd.testing.assert_frame_equal(result, acquired_df)


def test_load_with_auto_fetch_acquires_data_when_none(
    data_retrieval_plugin, mock_load_service, mock_acquisition_plugin, sample_symbol
):
    # Given: 첫 번째 load는 None 반환
    start_at = 1609459200
    end_at = 1609545600

    acquired_df = pd.DataFrame({
        'timestamp': [1609459200],
        'open': [29000.0],
        'high': [29500.0],
        'low': [28500.0],
        'close': [29200.0],
        'volume': [1000.0]
    })

    # 첫 번째 호출: None, 두 번째 호출: 데이터 있음
    mock_load_service.load.side_effect = [None, acquired_df]

    # When: load_with_auto_fetch 호출
    result = data_retrieval_plugin.load_with_auto_fetch(sample_symbol, start_at, end_at)

    # Then: load가 두 번 호출됨
    assert mock_load_service.load.call_count == 2

    # Then: acquire_and_save가 호출됨
    mock_acquisition_plugin.acquire_and_save.assert_called_once_with(
        sample_symbol, start_at, end_at
    )

    # Then: 획득한 데이터 반환
    pd.testing.assert_frame_equal(result, acquired_df)


def test_load_with_auto_fetch_propagates_load_error(
    data_retrieval_plugin, mock_load_service, mock_acquisition_plugin, sample_symbol
):
    # Given: load가 예외 발생
    start_at = 1609459200
    end_at = 1609545600

    mock_load_service.load.side_effect = Exception("Database error")

    # When/Then: 예외가 전파됨
    with pytest.raises(Exception, match="Database error"):
        data_retrieval_plugin.load_with_auto_fetch(sample_symbol, start_at, end_at)

    # Then: acquire_and_save는 호출되지 않음
    mock_acquisition_plugin.acquire_and_save.assert_not_called()


def test_load_with_auto_fetch_propagates_acquisition_error(
    data_retrieval_plugin, mock_load_service, mock_acquisition_plugin, sample_symbol
):
    # Given: 빈 데이터이고 acquire_and_save가 예외 발생
    start_at = 1609459200
    end_at = 1609545600

    empty_df = pd.DataFrame()
    mock_load_service.load.return_value = empty_df
    mock_acquisition_plugin.acquire_and_save.side_effect = Exception("Fetch error")

    # When/Then: 예외가 전파됨
    with pytest.raises(Exception, match="Fetch error"):
        data_retrieval_plugin.load_with_auto_fetch(sample_symbol, start_at, end_at)

    # Then: load는 한 번만 호출됨 (첫 번째만)
    assert mock_load_service.load.call_count == 1
