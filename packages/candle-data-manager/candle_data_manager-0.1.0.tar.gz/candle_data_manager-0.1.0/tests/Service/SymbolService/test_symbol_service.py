import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from candle_data_manager.Core.Models import Base
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService


@pytest.fixture(scope='function')
def engine():
    # In-memory SQLite for testing
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope='function')
def session(engine):
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope='function')
def connection_manager(engine):
    # Mock ConnectionManager - 테스트용
    class MockConnectionManager:
        pass

    cm = MockConnectionManager()
    cm.engine = engine
    cm.Session = sessionmaker(bind=engine)
    return cm


@pytest.fixture(scope='function')
def symbol_service(connection_manager):
    return SymbolService(connection_manager)


class TestSymbolServiceRegister:
    """register_symbol 메서드 테스트"""

    def test_register_new_symbol(self, symbol_service, session):
        # 새로운 Symbol 등록
        symbol = symbol_service.register_symbol(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        assert symbol is not None
        assert symbol.id is not None
        assert symbol.archetype == 'CRYPTO'
        assert symbol.exchange == 'BINANCE'
        assert symbol.tradetype == 'SPOT'
        assert symbol.base == 'BTC'
        assert symbol.quote == 'USDT'
        assert symbol.timeframe == '1h'

    def test_register_existing_symbol(self, symbol_service, session):
        # 첫 번째 등록
        symbol1 = symbol_service.register_symbol(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        # 동일한 Symbol 재등록 (get_or_create이므로 기존 반환)
        symbol2 = symbol_service.register_symbol(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        assert symbol1.id == symbol2.id

    def test_register_with_optional_fields(self, symbol_service, session):
        # 옵션 필드 포함 등록
        symbol = symbol_service.register_symbol(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h',
            full_name='Bitcoin/USDT',
            listed_at=1609459200
        )

        assert symbol.full_name == 'Bitcoin/USDT'
        assert symbol.listed_at == 1609459200

    def test_register_lowercase_converts_to_uppercase(self, symbol_service, session):
        # 소문자 입력 시 대문자로 변환 (timeframe 제외)
        symbol = symbol_service.register_symbol(
            session,
            archetype='crypto',
            exchange='binance',
            tradetype='spot',
            base='btc',
            quote='usdt',
            timeframe='1h'
        )

        assert symbol.archetype == 'CRYPTO'
        assert symbol.exchange == 'BINANCE'
        assert symbol.tradetype == 'SPOT'
        assert symbol.base == 'BTC'
        assert symbol.quote == 'USDT'
        assert symbol.timeframe == '1h'


class TestSymbolServiceFind:
    """find_symbols 메서드 테스트"""

    @pytest.fixture(autouse=True)
    def setup_symbols(self, symbol_service, session):
        # 테스트용 Symbol들 생성
        symbol_service.register_symbol(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'BTC', 'USDT', '1h'
        )
        symbol_service.register_symbol(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'ETH', 'USDT', '1h'
        )
        symbol_service.register_symbol(
            session, 'CRYPTO', 'BINANCE', 'FUTURES', 'BTC', 'USDT', '1h'
        )
        symbol_service.register_symbol(
            session, 'CRYPTO', 'UPBIT', 'SPOT', 'BTC', 'KRW', '1d'
        )
        symbol_service.register_symbol(
            session, 'STOCK', 'KRX', 'SPOT', '005930', 'KRW', '1d'
        )
        session.commit()

    def test_find_all_symbols(self, symbol_service, session):
        # 조건 없이 전체 조회
        symbols = symbol_service.find_symbols(session)
        assert len(symbols) == 5

    def test_find_by_archetype(self, symbol_service, session):
        # archetype으로 필터링
        symbols = symbol_service.find_symbols(session, archetype='CRYPTO')
        assert len(symbols) == 4
        assert all(s.archetype == 'CRYPTO' for s in symbols)

    def test_find_by_exchange(self, symbol_service, session):
        # exchange로 필터링
        symbols = symbol_service.find_symbols(session, exchange='BINANCE')
        assert len(symbols) == 3
        assert all(s.exchange == 'BINANCE' for s in symbols)

    def test_find_by_tradetype(self, symbol_service, session):
        # tradetype으로 필터링
        symbols = symbol_service.find_symbols(session, tradetype='FUTURES')
        assert len(symbols) == 1
        assert symbols[0].tradetype == 'FUTURES'

    def test_find_by_timeframe(self, symbol_service, session):
        # timeframe으로 필터링
        symbols = symbol_service.find_symbols(session, timeframe='1h')
        assert len(symbols) == 3
        assert all(s.timeframe == '1h' for s in symbols)

    def test_find_by_base(self, symbol_service, session):
        # base로 필터링
        symbols = symbol_service.find_symbols(session, base='BTC')
        assert len(symbols) == 3
        assert all(s.base == 'BTC' for s in symbols)

    def test_find_by_quote(self, symbol_service, session):
        # quote로 필터링
        symbols = symbol_service.find_symbols(session, quote='USDT')
        assert len(symbols) == 3
        assert all(s.quote == 'USDT' for s in symbols)

    def test_find_by_multiple_conditions(self, symbol_service, session):
        # 여러 조건 조합
        symbols = symbol_service.find_symbols(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT'
        )
        assert len(symbols) == 2
        assert all(
            s.archetype == 'CRYPTO' and
            s.exchange == 'BINANCE' and
            s.tradetype == 'SPOT'
            for s in symbols
        )

    def test_find_no_match(self, symbol_service, session):
        # 매칭되는 Symbol이 없는 경우
        symbols = symbol_service.find_symbols(session, exchange='KRAKEN')
        assert len(symbols) == 0

    def test_find_lowercase_converts_to_uppercase(self, symbol_service, session):
        # 소문자 입력 시 대문자로 변환하여 검색
        symbols = symbol_service.find_symbols(
            session,
            archetype='crypto',
            exchange='binance'
        )
        assert len(symbols) == 3


class TestSymbolServiceGetByString:
    """get_by_string 메서드 테스트"""

    @pytest.fixture(autouse=True)
    def setup_symbol(self, symbol_service, session):
        # 테스트용 Symbol 생성
        symbol_service.register_symbol(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'BTC', 'USDT', '1h'
        )
        session.commit()

    def test_get_by_string_success(self, symbol_service, session):
        # 올바른 문자열로 Symbol 조회
        symbol = symbol_service.get_by_string(
            session,
            'CRYPTO-BINANCE-SPOT-BTC-USDT-1h'
        )

        assert symbol is not None
        assert symbol.archetype == 'CRYPTO'
        assert symbol.exchange == 'BINANCE'
        assert symbol.tradetype == 'SPOT'
        assert symbol.base == 'BTC'
        assert symbol.quote == 'USDT'
        assert symbol.timeframe == '1h'

    def test_get_by_string_not_found(self, symbol_service, session):
        # DB에 존재하지 않는 Symbol
        symbol = symbol_service.get_by_string(
            session,
            'CRYPTO-BINANCE-SPOT-ETH-USDT-1h'
        )

        assert symbol is None

    def test_get_by_string_invalid_format(self, symbol_service, session):
        # 잘못된 형식의 문자열
        with pytest.raises(ValueError) as exc_info:
            symbol_service.get_by_string(session, 'INVALID-FORMAT')

        assert 'Invalid symbol string format' in str(exc_info.value)

    def test_get_by_string_lowercase(self, symbol_service, session):
        # 소문자 입력도 처리 가능
        symbol = symbol_service.get_by_string(
            session,
            'crypto-binance-spot-btc-usdt-1h'
        )

        assert symbol is not None
        assert symbol.archetype == 'CRYPTO'
