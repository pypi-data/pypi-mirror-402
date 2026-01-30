import pytest
from unittest.mock import MagicMock, patch
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_conn_manager():
    """Mock ConnectionManager"""
    return MagicMock()


@pytest.fixture
def symbol_individual():
    """개별 테이블용 Symbol"""
    return Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )


@pytest.fixture
def symbol_unified():
    """통합 테이블용 Symbol"""
    return Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )


class TestPrepareTable:
    """prepare_table 메서드 테스트"""

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_prepare_table_creates_if_not_exists(self, mock_repo, mock_conn_manager, symbol_individual):
        """테이블이 없으면 생성"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_repo.table_exists.return_value = False

        manager = SymbolMetadata(mock_conn_manager)
        manager.prepare_table(symbol_individual)

        # _get_or_create_table 호출로 테이블 생성 확인
        mock_repo._get_or_create_table.assert_called_once_with(mock_conn, symbol_individual)

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_prepare_table_skips_if_exists(self, mock_repo, mock_conn_manager, symbol_individual):
        """테이블이 이미 있으면 건너뜀"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_repo.table_exists.return_value = True

        manager = SymbolMetadata(mock_conn_manager)
        manager.prepare_table(symbol_individual)

        # _get_or_create_table 호출 안 됨
        mock_repo._get_or_create_table.assert_not_called()


class TestGetTableStatus:
    """get_table_status 메서드 테스트"""

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_get_table_status_with_data(self, mock_repo, mock_conn_manager, symbol_individual):
        """데이터가 있는 테이블 상태 조회"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        mock_repo.table_exists.return_value = True
        mock_repo.has_data.return_value = True
        mock_repo.count.return_value = 1000
        mock_repo.get_first_timestamp.return_value = 1600000000
        mock_repo.get_last_timestamp.return_value = 1700000000

        manager = SymbolMetadata(mock_conn_manager)
        status = manager.get_table_status(symbol_individual)

        assert status["exists"] is True
        assert status["has_data"] is True
        assert status["count"] == 1000
        assert status["first_timestamp"] == 1600000000
        assert status["last_timestamp"] == 1700000000

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_get_table_status_no_data(self, mock_repo, mock_conn_manager, symbol_individual):
        """데이터가 없는 테이블 상태 조회"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        mock_repo.table_exists.return_value = True
        mock_repo.has_data.return_value = False
        mock_repo.count.return_value = 0
        mock_repo.get_first_timestamp.return_value = None
        mock_repo.get_last_timestamp.return_value = None

        manager = SymbolMetadata(mock_conn_manager)
        status = manager.get_table_status(symbol_individual)

        assert status["exists"] is True
        assert status["has_data"] is False
        assert status["count"] == 0
        assert status["first_timestamp"] is None
        assert status["last_timestamp"] is None

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_get_table_status_not_exists(self, mock_repo, mock_conn_manager, symbol_individual):
        """테이블이 없는 경우"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        mock_repo.table_exists.return_value = False

        manager = SymbolMetadata(mock_conn_manager)
        status = manager.get_table_status(symbol_individual)

        assert status["exists"] is False
        assert status["has_data"] is False
        assert status["count"] == 0
        assert status["first_timestamp"] is None
        assert status["last_timestamp"] is None

    @patch('candle_data_manager.Service.SymbolMetadata.SymbolMetadata.CandleRepository')
    def test_get_table_status_unified_requires_symbol_id(self, mock_repo, mock_conn_manager, symbol_unified):
        """통합 테이블은 symbol_id 필수"""
        mock_conn = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn

        mock_repo.table_exists.return_value = True
        mock_repo.has_data.return_value = True
        mock_repo.count.return_value = 500
        mock_repo.get_first_timestamp.return_value = 1600000000
        mock_repo.get_last_timestamp.return_value = 1700000000

        manager = SymbolMetadata(mock_conn_manager)
        status = manager.get_table_status(symbol_unified, symbol_id=1)

        assert status["exists"] is True
        assert status["has_data"] is True
        # CandleRepository 메서드들이 symbol_id와 함께 호출되었는지 확인
        mock_repo.has_data.assert_called_with(mock_conn, symbol_unified, 1)
        mock_repo.count.assert_called_with(mock_conn, symbol_unified, 1)
