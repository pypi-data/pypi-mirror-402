import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
from candle_data_manager.Service.DataLoadService.DataLoadService import DataLoadService
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_conn_manager():
    """Mock ConnectionManager"""
    return MagicMock()


@pytest.fixture
def symbol_individual():
    """개별 테이블용 Symbol"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )
    symbol.id = 1
    return symbol


@pytest.fixture
def symbol_unified():
    """통합 테이블용 Symbol"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )
    symbol.id = 2
    return symbol


class TestLoad:
    """load 메서드 테스트"""

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_individual_all_data(self, mock_repo, mock_conn_manager, symbol_individual):
        """개별 테이블 전체 데이터 로드"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        # Mock DataFrame
        expected_df = pd.DataFrame({
            'timestamp': [1600000000, 1600000060],
            'open': [10000.0, 10100.0],
            'high': [10200.0, 10300.0],
            'low': [9900.0, 10000.0],
            'close': [10100.0, 10200.0],
            'volume': [100.0, 150.0]
        })
        mock_repo.query_to_dataframe.return_value = expected_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_individual)

        # 검증
        mock_repo.query_to_dataframe.assert_called_once_with(
            conn=mock_conn,
            symbol=symbol_individual,
            symbol_id=symbol_individual.id,
            start_ts=None,
            end_ts=None
        )
        assert result.equals(expected_df)

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_individual_with_time_range(self, mock_repo, mock_conn_manager, symbol_individual):
        """개별 테이블 시간 범위 지정 로드"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        expected_df = pd.DataFrame({
            'timestamp': [1600000000],
            'open': [10000.0],
            'high': [10200.0],
            'low': [9900.0],
            'close': [10100.0],
            'volume': [100.0]
        })
        mock_repo.query_to_dataframe.return_value = expected_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_individual, start_at=1600000000, end_at=1600001000)

        # 검증
        mock_repo.query_to_dataframe.assert_called_once_with(
            conn=mock_conn,
            symbol=symbol_individual,
            symbol_id=symbol_individual.id,
            start_ts=1600000000,
            end_ts=1600001000
        )
        assert result.equals(expected_df)

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_individual_with_limit(self, mock_repo, mock_conn_manager, symbol_individual):
        """개별 테이블 limit 지정 로드"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        # 10개 데이터 생성 후 3개만 반환
        full_df = pd.DataFrame({
            'timestamp': list(range(1600000000, 1600000600, 60)),
            'open': [10000.0] * 10,
            'high': [10200.0] * 10,
            'low': [9900.0] * 10,
            'close': [10100.0] * 10,
            'volume': [100.0] * 10
        })
        mock_repo.query_to_dataframe.return_value = full_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_individual, limit=3)

        # limit 적용 확인
        assert len(result) == 3
        assert result['timestamp'].iloc[0] == 1600000000

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_unified_table(self, mock_repo, mock_conn_manager, symbol_unified):
        """통합 테이블 데이터 로드"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        expected_df = pd.DataFrame({
            'symbol_id': [2, 2],
            'timestamp': [1600000000, 1600003600],
            'open': [10000.0, 10100.0],
            'high': [10200.0, 10300.0],
            'low': [9900.0, 10000.0],
            'close': [10100.0, 10200.0],
            'volume': [100.0, 150.0]
        })
        mock_repo.query_to_dataframe.return_value = expected_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_unified)

        # 통합 테이블은 symbol_id 전달
        mock_repo.query_to_dataframe.assert_called_once_with(
            conn=mock_conn,
            symbol=symbol_unified,
            symbol_id=symbol_unified.id,
            start_ts=None,
            end_ts=None
        )
        assert result.equals(expected_df)

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_empty_result(self, mock_repo, mock_conn_manager, symbol_individual):
        """데이터가 없는 경우 빈 DataFrame 반환"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        empty_df = pd.DataFrame()
        mock_repo.query_to_dataframe.return_value = empty_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_individual)

        assert result.empty

    @patch('candle_data_manager.Service.DataLoadService.DataLoadService.CandleRepository')
    def test_load_limit_larger_than_data(self, mock_repo, mock_conn_manager, symbol_individual):
        """limit이 데이터 개수보다 큰 경우"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        small_df = pd.DataFrame({
            'timestamp': [1600000000, 1600000060],
            'open': [10000.0, 10100.0],
            'high': [10200.0, 10300.0],
            'low': [9900.0, 10000.0],
            'close': [10100.0, 10200.0],
            'volume': [100.0, 150.0]
        })
        mock_repo.query_to_dataframe.return_value = small_df

        service = DataLoadService(mock_conn_manager)
        result = service.load(symbol_individual, limit=1000)

        # 전체 데이터만 반환
        assert len(result) == 2
