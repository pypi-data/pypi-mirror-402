import pytest
from unittest.mock import MagicMock, patch, call
from candle_data_manager.Service.DataSaveService.DataSaveService import DataSaveService
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_conn_manager():
    """Mock ConnectionManager"""
    return MagicMock()


@pytest.fixture
def symbol_unified_1h():
    """통합 테이블용 Symbol (1h)"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )
    symbol.id = 1
    return symbol


@pytest.fixture
def symbol_unified_1h_eth():
    """통합 테이블용 Symbol (1h, ETH)"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="ETH",
        quote="USDT",
        timeframe="1h"
    )
    symbol.id = 2
    return symbol


@pytest.fixture
def symbol_individual_1m_btc():
    """개별 테이블용 Symbol (1m, BTC)"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1m"
    )
    symbol.id = 3
    return symbol


@pytest.fixture
def symbol_individual_1m_eth():
    """개별 테이블용 Symbol (1m, ETH)"""
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="ETH",
        quote="USDT",
        timeframe="1m"
    )
    symbol.id = 4
    return symbol


@pytest.fixture
def sample_data():
    """샘플 캔들 데이터"""
    return [
        {
            "timestamp": 1600000000,
            "open": 10000.5,
            "high": 10100.0,
            "low": 9900.0,
            "close": 10050.0,
            "volume": 1000.0
        },
        {
            "timestamp": 1600003600,
            "open": 10050.0,
            "high": 10200.0,
            "low": 10000.0,
            "close": 10150.0,
            "volume": 1500.0
        }
    ]


class TestSave:
    """save 메서드 테스트"""

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_save_individual_table(self, mock_upsert, mock_symbol_repo, mock_conn_manager, symbol_individual_1m_btc, sample_data):
        """개별 테이블에 데이터 저장"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        service = DataSaveService(mock_conn_manager)
        service.save(symbol_individual_1m_btc, sample_data)

        # upsert 호출 확인
        assert mock_upsert.called
        call_args = mock_upsert.call_args[0]
        saved_symbol = call_args[1]
        saved_data = call_args[2]

        # Symbol 확인
        assert saved_symbol == symbol_individual_1m_btc

        # 데이터 변환 확인 (float -> int64)
        assert len(saved_data) == 2
        assert saved_data[0]["timestamp"] == 1600000000
        assert saved_data[0]["open"] == 1000050000000
        assert saved_data[0]["high"] == 1010000000000
        assert saved_data[0]["low"] == 990000000000
        assert saved_data[0]["close"] == 1005000000000
        assert saved_data[0]["volume"] == 100000000000

        # symbol_id가 없어야 함 (개별 테이블)
        assert "symbol_id" not in saved_data[0]

        # last_timestamp 업데이트 확인
        mock_symbol_repo.update_last_timestamp.assert_called_once_with(mock_session, symbol_individual_1m_btc.id, 1600003600)

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_save_unified_table(self, mock_upsert, mock_symbol_repo, mock_conn_manager, symbol_unified_1h, sample_data):
        """통합 테이블에 데이터 저장 (symbol_id 추가)"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        service = DataSaveService(mock_conn_manager)
        service.save(symbol_unified_1h, sample_data)

        # upsert 호출 확인
        assert mock_upsert.called
        call_args = mock_upsert.call_args[0]
        saved_symbol = call_args[1]
        saved_data = call_args[2]

        # Symbol 확인
        assert saved_symbol == symbol_unified_1h

        # 데이터 변환 및 symbol_id 추가 확인
        assert len(saved_data) == 2
        assert saved_data[0]["symbol_id"] == 1
        assert saved_data[0]["timestamp"] == 1600000000
        assert saved_data[0]["open"] == 1000050000000
        assert saved_data[0]["high"] == 1010000000000
        assert saved_data[0]["low"] == 990000000000
        assert saved_data[0]["close"] == 1005000000000
        assert saved_data[0]["volume"] == 100000000000

        mock_symbol_repo.update_last_timestamp.assert_called_once_with(mock_session, symbol_unified_1h.id, 1600003600)

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_save_empty_data(self, mock_upsert, mock_symbol_repo, mock_conn_manager, symbol_individual_1m_btc):
        """빈 데이터는 저장하지 않음"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        service = DataSaveService(mock_conn_manager)
        service.save(symbol_individual_1m_btc, [])

        # upsert 호출 안 됨
        mock_upsert.assert_not_called()
        # last_timestamp 업데이트 안 됨
        mock_symbol_repo.update_last_timestamp.assert_not_called()


class TestBulkSave:
    """bulk_save 메서드 테스트 (테이블별 재그룹화)"""

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_bulk_save_unified_tables(self, mock_upsert, mock_symbol_repo, mock_conn_manager,
                                     symbol_unified_1h, symbol_unified_1h_eth, sample_data):
        """통합 테이블: 같은 테이블의 여러 Symbol 데이터를 한번에 저장"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        # 두 Symbol이 같은 테이블 사용
        buffer = {
            symbol_unified_1h: sample_data,
            symbol_unified_1h_eth: sample_data
        }

        service = DataSaveService(mock_conn_manager)
        service.bulk_save(buffer)

        # 테이블별로 재그룹화되어 한번만 호출
        assert mock_upsert.call_count == 1

        # 호출된 데이터 검증
        call_args = mock_upsert.call_args[0]
        saved_symbol = call_args[1]
        saved_data = call_args[2]

        # 같은 테이블명 사용
        assert saved_symbol.get_table_name() == symbol_unified_1h.get_table_name()

        # 모든 데이터가 symbol_id와 함께 통합됨
        assert len(saved_data) == 4  # 2 symbols × 2 rows
        assert any(row["symbol_id"] == 1 for row in saved_data)
        assert any(row["symbol_id"] == 2 for row in saved_data)

        # last_timestamp 업데이트 (각 Symbol마다)
        assert mock_symbol_repo.update_last_timestamp.call_count == 2

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_bulk_save_individual_tables(self, mock_upsert, mock_symbol_repo, mock_conn_manager,
                                         symbol_individual_1m_btc, symbol_individual_1m_eth, sample_data):
        """개별 테이블: 각 Symbol마다 별도 저장"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        buffer = {
            symbol_individual_1m_btc: sample_data,
            symbol_individual_1m_eth: sample_data
        }

        service = DataSaveService(mock_conn_manager)
        service.bulk_save(buffer)

        # 테이블이 다르므로 2번 호출
        assert mock_upsert.call_count == 2

        # last_timestamp 업데이트
        assert mock_symbol_repo.update_last_timestamp.call_count == 2

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_bulk_save_mixed_tables(self, mock_upsert, mock_symbol_repo, mock_conn_manager,
                                   symbol_unified_1h, symbol_unified_1h_eth,
                                   symbol_individual_1m_btc, symbol_individual_1m_eth, sample_data):
        """통합 테이블 + 개별 테이블 혼합"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        buffer = {
            symbol_unified_1h: sample_data,
            symbol_unified_1h_eth: sample_data,
            symbol_individual_1m_btc: sample_data,
            symbol_individual_1m_eth: sample_data
        }

        service = DataSaveService(mock_conn_manager)
        service.bulk_save(buffer)

        # 통합 테이블 1번 + 개별 테이블 2번 = 총 3번
        assert mock_upsert.call_count == 3

        # last_timestamp 업데이트 (4개 Symbol)
        assert mock_symbol_repo.update_last_timestamp.call_count == 4

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_bulk_save_empty_buffer(self, mock_upsert, mock_symbol_repo, mock_conn_manager):
        """빈 버퍼는 처리하지 않음"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        service = DataSaveService(mock_conn_manager)
        service.bulk_save({})

        mock_upsert.assert_not_called()
        mock_symbol_repo.update_last_timestamp.assert_not_called()

    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.SymbolRepository')
    @patch('candle_data_manager.Service.DataSaveService.DataSaveService.CandleRepository.upsert')
    def test_bulk_save_skip_empty_data(self, mock_upsert, mock_symbol_repo, mock_conn_manager,
                                      symbol_unified_1h, symbol_individual_1m_btc, sample_data):
        """빈 데이터를 가진 Symbol은 건너뜀"""
        mock_conn = MagicMock()
        mock_session = MagicMock()
        mock_conn_manager.get_connection.return_value.__enter__.return_value = mock_conn
        mock_conn_manager.session_scope.return_value.__enter__.return_value = mock_session

        buffer = {
            symbol_unified_1h: sample_data,
            symbol_individual_1m_btc: []  # 빈 데이터
        }

        service = DataSaveService(mock_conn_manager)
        service.bulk_save(buffer)

        # symbol_unified_1h만 저장됨
        assert mock_upsert.call_count == 1
        assert mock_symbol_repo.update_last_timestamp.call_count == 1
