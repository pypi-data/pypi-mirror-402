import pytest
from unittest.mock import MagicMock
from candle_data_manager.Core.Models.SymbolRepository import SymbolRepository
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def mock_session():
    """Mock SQLAlchemy Session"""
    return MagicMock()


@pytest.fixture
def sample_symbol():
    """샘플 Symbol 객체"""
    return Symbol(
        id=1,
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h",
        full_name="Bitcoin/Tether",
        listed_at=1600000000,
        last_timestamp=1700000000
    )


class TestGetById:
    """get_by_id 메서드 테스트"""

    def test_get_by_id_found(self, mock_session, sample_symbol):
        """ID로 조회 성공"""
        mock_session.query.return_value.get.return_value = sample_symbol

        result = SymbolRepository.get_by_id(mock_session, 1)

        assert result == sample_symbol
        mock_session.query.assert_called_once_with(Symbol)
        mock_session.query.return_value.get.assert_called_once_with(1)

    def test_get_by_id_not_found(self, mock_session):
        """ID로 조회 실패 (None 반환)"""
        mock_session.query.return_value.get.return_value = None

        result = SymbolRepository.get_by_id(mock_session, 999)

        assert result is None


class TestGetByComponents:
    """get_by_components 메서드 테스트"""

    def test_get_by_components_found(self, mock_session, sample_symbol):
        """컴포넌트로 조회 성공"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = sample_symbol

        result = SymbolRepository.get_by_components(
            mock_session,
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="BTC",
            quote="USDT",
            timeframe="1h"
        )

        assert result == sample_symbol
        mock_session.query.return_value.filter_by.assert_called_once_with(
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="BTC",
            quote="USDT",
            timeframe="1h"
        )

    def test_get_by_components_not_found(self, mock_session):
        """컴포넌트로 조회 실패"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = SymbolRepository.get_by_components(
            mock_session,
            archetype="CRYPTO",
            exchange="UNKNOWN",
            tradetype="SPOT",
            base="XYZ",
            quote="USDT",
            timeframe="1h"
        )

        assert result is None


class TestGetOrCreate:
    """get_or_create 메서드 테스트"""

    def test_get_or_create_existing(self, mock_session, sample_symbol):
        """이미 존재하는 경우 조회만"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = sample_symbol

        result, created = SymbolRepository.get_or_create(
            mock_session,
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="BTC",
            quote="USDT",
            timeframe="1h"
        )

        assert result == sample_symbol
        assert created is False
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()

    def test_get_or_create_new(self, mock_session):
        """존재하지 않는 경우 생성"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result, created = SymbolRepository.get_or_create(
            mock_session,
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="ETH",
            quote="USDT",
            timeframe="1h",
            full_name="Ethereum/Tether",
            listed_at=1600000000
        )

        assert created is True
        assert result.archetype == "CRYPTO"
        assert result.exchange == "BINANCE"
        assert result.base == "ETH"
        assert result.full_name == "Ethereum/Tether"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestListAll:
    """list_all 메서드 테스트"""

    def test_list_all_with_data(self, mock_session, sample_symbol):
        """전체 목록 조회 (데이터 있음)"""
        symbol2 = Symbol(
            id=2,
            archetype="STOCK",
            exchange="KRX",
            tradetype="SPOT",
            base="005930",
            quote="KRW",
            timeframe="1d"
        )
        mock_session.query.return_value.all.return_value = [sample_symbol, symbol2]

        result = SymbolRepository.list_all(mock_session)

        assert len(result) == 2
        assert result[0] == sample_symbol
        assert result[1] == symbol2

    def test_list_all_empty(self, mock_session):
        """전체 목록 조회 (데이터 없음)"""
        mock_session.query.return_value.all.return_value = []

        result = SymbolRepository.list_all(mock_session)

        assert result == []


class TestListByExchange:
    """list_by_exchange 메서드 테스트"""

    def test_list_by_exchange_only(self, mock_session, sample_symbol):
        """거래소만 지정하여 조회"""
        mock_session.query.return_value.filter_by.return_value.all.return_value = [sample_symbol]

        result = SymbolRepository.list_by_exchange(mock_session, exchange="BINANCE")

        assert len(result) == 1
        assert result[0] == sample_symbol
        mock_session.query.return_value.filter_by.assert_called_once_with(exchange="BINANCE")

    def test_list_by_exchange_and_tradetype(self, mock_session, sample_symbol):
        """거래소 + 거래타입으로 조회"""
        mock_query = mock_session.query.return_value
        mock_query.filter_by.return_value.filter_by.return_value.all.return_value = [sample_symbol]

        result = SymbolRepository.list_by_exchange(
            mock_session,
            exchange="BINANCE",
            tradetype="SPOT"
        )

        assert len(result) == 1
        assert result[0] == sample_symbol

    def test_list_by_exchange_empty(self, mock_session):
        """조회 결과 없음"""
        mock_session.query.return_value.filter_by.return_value.all.return_value = []

        result = SymbolRepository.list_by_exchange(mock_session, exchange="UNKNOWN")

        assert result == []


class TestUpdateLastTimestamp:
    """update_last_timestamp 메서드 테스트"""

    def test_update_last_timestamp_success(self, mock_session, sample_symbol):
        """마지막 타임스탬프 업데이트 성공"""
        mock_session.query.return_value.get.return_value = sample_symbol

        SymbolRepository.update_last_timestamp(mock_session, symbol_id=1, timestamp=1800000000)

        assert sample_symbol.last_timestamp == 1800000000
        mock_session.flush.assert_called_once()

    def test_update_last_timestamp_not_found(self, mock_session):
        """존재하지 않는 Symbol (에러 발생)"""
        mock_session.query.return_value.get.return_value = None

        with pytest.raises(ValueError, match="Symbol with id 999 not found"):
            SymbolRepository.update_last_timestamp(mock_session, symbol_id=999, timestamp=1800000000)


class TestDelete:
    """delete 메서드 테스트"""

    def test_delete_success(self, mock_session, sample_symbol):
        """삭제 성공"""
        mock_session.query.return_value.get.return_value = sample_symbol

        SymbolRepository.delete(mock_session, symbol_id=1)

        mock_session.delete.assert_called_once_with(sample_symbol)
        mock_session.flush.assert_called_once()

    def test_delete_not_found(self, mock_session):
        """존재하지 않는 Symbol (에러 발생)"""
        mock_session.query.return_value.get.return_value = None

        with pytest.raises(ValueError, match="Symbol with id 999 not found"):
            SymbolRepository.delete(mock_session, symbol_id=999)
