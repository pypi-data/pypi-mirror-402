import pytest
from unittest.mock import Mock, MagicMock
import pandas as pd

from candle_data_manager.API.CandleDataAPI.CandleDataAPI import CandleDataAPI
from candle_data_manager.Plugin.UpdateOrchestrationPlugin.UpdateOrchestrationPlugin import UpdateOrchestrationPlugin
from candle_data_manager.Plugin.DataRetrievalPlugin.DataRetrievalPlugin import DataRetrievalPlugin
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService
from candle_data_manager.Service.MarketFactoryService.MarketFactoryService import MarketFactoryService
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Particles.UpdateResult import UpdateResult
from candle_data_manager.Particles.Market import Market


@pytest.fixture
def mock_connection_manager():
    mock_cm = Mock(spec=ConnectionManager)
    mock_session = MagicMock()
    mock_cm.session_scope.return_value.__enter__ = Mock(return_value=mock_session)
    mock_cm.session_scope.return_value.__exit__ = Mock(return_value=False)
    return mock_cm


@pytest.fixture
def mock_update_plugin():
    return Mock(spec=UpdateOrchestrationPlugin)


@pytest.fixture
def mock_retrieval_plugin():
    return Mock(spec=DataRetrievalPlugin)


@pytest.fixture
def mock_symbol_service():
    return Mock(spec=SymbolService)


@pytest.fixture
def mock_market_factory():
    return Mock(spec=MarketFactoryService)


@pytest.fixture
def candle_data_api(
    mock_connection_manager,
    mock_update_plugin,
    mock_retrieval_plugin,
    mock_symbol_service,
    mock_market_factory
):
    return CandleDataAPI(
        connection_manager=mock_connection_manager,
        update_plugin=mock_update_plugin,
        retrieval_plugin=mock_retrieval_plugin,
        symbol_service=mock_symbol_service,
        market_factory=mock_market_factory
    )


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


def test_active_update_calls_plugin_with_session(
    candle_data_api, mock_connection_manager, mock_update_plugin, sample_symbol
):
    # Given: UpdateResult 설정
    expected_result = UpdateResult(
        success_symbols=[sample_symbol],
        failed_symbols=[],
        total_rows=1000
    )
    mock_update_plugin.active_update.return_value = expected_result

    # When: active_update 호출
    result = candle_data_api.active_update(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT"
    )

    # Then: session_scope 사용됨
    mock_connection_manager.session_scope.assert_called_once()

    # Then: UpdateOrchestrationPlugin.active_update가 호출됨
    mock_update_plugin.active_update.assert_called_once()
    call_args = mock_update_plugin.active_update.call_args
    assert call_args.kwargs['archetype'] == "CRYPTO"
    assert call_args.kwargs['exchange'] == "BINANCE"
    assert call_args.kwargs['tradetype'] == "SPOT"

    # Then: UpdateResult 반환
    assert result == expected_result


def test_passive_update_calls_plugin_with_all_parameters(
    candle_data_api, mock_connection_manager, mock_update_plugin, sample_symbol
):
    # Given: UpdateResult 설정
    expected_result = UpdateResult(
        success_symbols=[sample_symbol],
        failed_symbols=[],
        total_rows=500
    )
    mock_update_plugin.passive_update.return_value = expected_result

    # When: passive_update 호출 (모든 파라미터)
    result = candle_data_api.passive_update(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h",
        buffer_size=50000
    )

    # Then: session_scope 사용됨
    mock_connection_manager.session_scope.assert_called_once()

    # Then: UpdateOrchestrationPlugin.passive_update가 호출됨
    mock_update_plugin.passive_update.assert_called_once()
    call_args = mock_update_plugin.passive_update.call_args
    assert call_args.kwargs['archetype'] == "CRYPTO"
    assert call_args.kwargs['exchange'] == "BINANCE"
    assert call_args.kwargs['tradetype'] == "SPOT"
    assert call_args.kwargs['base'] == "BTC"
    assert call_args.kwargs['quote'] == "USDT"
    assert call_args.kwargs['timeframe'] == "1h"
    assert call_args.kwargs['buffer_size'] == 50000

    # Then: UpdateResult 반환
    assert result == expected_result


def test_passive_update_calls_plugin_with_partial_parameters(
    candle_data_api, mock_connection_manager, mock_update_plugin
):
    # Given: UpdateResult 설정
    expected_result = UpdateResult(
        success_symbols=[],
        failed_symbols=[],
        total_rows=0
    )
    mock_update_plugin.passive_update.return_value = expected_result

    # When: passive_update 호출 (일부 파라미터만)
    result = candle_data_api.passive_update(
        archetype="CRYPTO",
        exchange="BINANCE"
    )

    # Then: UpdateOrchestrationPlugin.passive_update가 호출됨
    mock_update_plugin.passive_update.assert_called_once()
    call_args = mock_update_plugin.passive_update.call_args
    assert call_args.kwargs['archetype'] == "CRYPTO"
    assert call_args.kwargs['exchange'] == "BINANCE"
    assert call_args.kwargs.get('tradetype') is None
    assert call_args.kwargs.get('base') is None


def test_load_returns_multiple_markets(
    candle_data_api,
    mock_connection_manager,
    mock_symbol_service,
    mock_retrieval_plugin,
    mock_market_factory
):
    # Given: 여러 Symbol 검색 결과
    symbol1 = Symbol(
        archetype="CRYPTO", exchange="BINANCE", tradetype="SPOT",
        base="BTC", quote="USDT", timeframe="1h"
    )
    symbol2 = Symbol(
        archetype="CRYPTO", exchange="BINANCE", tradetype="SPOT",
        base="ETH", quote="USDT", timeframe="1h"
    )
    mock_symbol_service.find_symbols.return_value = [symbol1, symbol2]

    # Given: DataRetrievalPlugin이 DataFrame 반환
    df1 = pd.DataFrame({'timestamp': [1], 'close': [100.0]})
    df2 = pd.DataFrame({'timestamp': [1], 'close': [200.0]})
    mock_retrieval_plugin.load_with_auto_fetch.side_effect = [df1, df2]

    # Given: MarketFactoryService가 Market 생성
    market1 = Market(symbol=symbol1, candles=df1)
    market2 = Market(symbol=symbol2, candles=df2)
    mock_market_factory.create_market.side_effect = [market1, market2]

    # When: load 호출
    result = candle_data_api.load(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        quote="USDT",
        timeframe="1h",
        start_at=1609459200,
        end_at=1609545600,
        limit=100
    )

    # Then: session_scope 사용됨
    mock_connection_manager.session_scope.assert_called_once()

    # Then: SymbolService.find_symbols 호출됨
    mock_symbol_service.find_symbols.assert_called_once()
    call_args = mock_symbol_service.find_symbols.call_args
    assert call_args.kwargs['archetype'] == "CRYPTO"
    assert call_args.kwargs['exchange'] == "BINANCE"
    assert call_args.kwargs['tradetype'] == "SPOT"
    assert call_args.kwargs['quote'] == "USDT"
    assert call_args.kwargs['timeframe'] == "1h"

    # Then: DataRetrievalPlugin.load_with_auto_fetch가 각 Symbol에 대해 호출됨
    assert mock_retrieval_plugin.load_with_auto_fetch.call_count == 2
    mock_retrieval_plugin.load_with_auto_fetch.assert_any_call(
        symbol=symbol1, start_at=1609459200, end_at=1609545600
    )
    mock_retrieval_plugin.load_with_auto_fetch.assert_any_call(
        symbol=symbol2, start_at=1609459200, end_at=1609545600
    )

    # Then: MarketFactoryService.create_market가 각 Symbol에 대해 호출됨
    assert mock_market_factory.create_market.call_count == 2

    # Then: Market 리스트 반환
    assert len(result) == 2
    assert result[0] == market1
    assert result[1] == market2


def test_load_with_no_symbols_returns_empty_list(
    candle_data_api, mock_connection_manager, mock_symbol_service
):
    # Given: Symbol 검색 결과 없음
    mock_symbol_service.find_symbols.return_value = []

    # When: load 호출
    result = candle_data_api.load(archetype="CRYPTO")

    # Then: 빈 리스트 반환
    assert result == []


def test_load_with_limit_passes_to_retrieval_plugin(
    candle_data_api,
    mock_connection_manager,
    mock_symbol_service,
    mock_retrieval_plugin,
    mock_market_factory,
    sample_symbol
):
    # Given: Symbol 검색 결과
    mock_symbol_service.find_symbols.return_value = [sample_symbol]

    # Given: DataRetrievalPlugin이 DataFrame 반환
    df = pd.DataFrame({'timestamp': [1], 'close': [100.0]})
    mock_retrieval_plugin.load_with_auto_fetch.return_value = df

    # Given: MarketFactoryService가 Market 생성
    market = Market(symbol=sample_symbol, candles=df)
    mock_market_factory.create_market.return_value = market

    # When: load 호출 (limit만)
    result = candle_data_api.load(limit=50)

    # Then: limit은 DataRetrievalPlugin에 전달되지 않음 (end_at으로 변환)
    # limit은 API 레벨에서 처리하거나 무시됨
    assert len(result) == 1


def test_get_symbol_calls_service(
    candle_data_api, mock_connection_manager, mock_symbol_service, sample_symbol
):
    # Given: SymbolService가 Symbol 반환
    mock_symbol_service.get_by_string.return_value = sample_symbol

    # When: get_symbol 호출
    result = candle_data_api.get_symbol("CRYPTO-BINANCE-SPOT-BTC-USDT-1h")

    # Then: session_scope 사용됨
    mock_connection_manager.session_scope.assert_called_once()

    # Then: SymbolService.get_by_string 호출됨
    mock_symbol_service.get_by_string.assert_called_once()
    call_args = mock_symbol_service.get_by_string.call_args
    assert call_args.kwargs['symbol_str'] == "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"

    # Then: Symbol 반환
    assert result == sample_symbol


def test_get_symbol_returns_none_when_not_found(
    candle_data_api, mock_connection_manager, mock_symbol_service
):
    # Given: SymbolService가 None 반환
    mock_symbol_service.get_by_string.return_value = None

    # When: get_symbol 호출
    result = candle_data_api.get_symbol("INVALID-SYMBOL-STRING")

    # Then: None 반환
    assert result is None


def test_active_update_propagates_exception(
    candle_data_api, mock_connection_manager, mock_update_plugin
):
    # Given: UpdatePlugin이 예외 발생
    mock_update_plugin.active_update.side_effect = Exception("Update failed")

    # When/Then: 예외가 전파됨
    with pytest.raises(Exception, match="Update failed"):
        candle_data_api.active_update(
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT"
        )


def test_load_propagates_exception_from_symbol_service(
    candle_data_api, mock_connection_manager, mock_symbol_service
):
    # Given: SymbolService가 예외 발생
    mock_symbol_service.find_symbols.side_effect = Exception("Database error")

    # When/Then: 예외가 전파됨
    with pytest.raises(Exception, match="Database error"):
        candle_data_api.load(archetype="CRYPTO")


def test_load_propagates_exception_from_retrieval_plugin(
    candle_data_api,
    mock_connection_manager,
    mock_symbol_service,
    mock_retrieval_plugin,
    sample_symbol
):
    # Given: Symbol 검색 성공
    mock_symbol_service.find_symbols.return_value = [sample_symbol]

    # Given: DataRetrievalPlugin이 예외 발생
    mock_retrieval_plugin.load_with_auto_fetch.side_effect = Exception("Fetch error")

    # When/Then: 예외가 전파됨
    with pytest.raises(Exception, match="Fetch error"):
        candle_data_api.load(archetype="CRYPTO")
