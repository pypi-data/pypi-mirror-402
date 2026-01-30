import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from candle_data_manager.Core.Models import Base
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata
from candle_data_manager.Plugin.SymbolPreparationPlugin.SymbolPreparationPlugin import SymbolPreparationPlugin


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
    # Mock ConnectionManager with get_connection support
    mock_cm = Mock()
    mock_cm.engine = engine
    mock_cm.Session = sessionmaker(bind=engine)

    # get_connection context manager support
    mock_conn = Mock()
    mock_conn.__enter__ = Mock(return_value=engine.connect())
    mock_conn.__exit__ = Mock(return_value=False)
    mock_cm.get_connection = Mock(return_value=mock_conn)

    return mock_cm


@pytest.fixture(scope='function')
def symbol_service(connection_manager):
    return SymbolService(connection_manager)


@pytest.fixture(scope='function')
def symbol_metadata(connection_manager):
    # Mock SymbolMetadata
    mock_metadata = Mock(spec=SymbolMetadata)
    mock_metadata.prepare_table = Mock()
    return mock_metadata


@pytest.fixture(scope='function')
def plugin(symbol_service, symbol_metadata):
    return SymbolPreparationPlugin(symbol_service, symbol_metadata)


class TestSymbolPreparationPlugin:
    """SymbolPreparationPlugin 테스트"""

    def test_register_and_prepare_new_symbol(self, plugin, session):
        # 새로운 Symbol 등록 및 테이블 준비
        symbol = plugin.register_and_prepare(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        # Symbol이 정상 생성되었는지 확인
        assert symbol is not None
        assert symbol.id is not None
        assert symbol.archetype == 'CRYPTO'
        assert symbol.exchange == 'BINANCE'
        assert symbol.tradetype == 'SPOT'
        assert symbol.base == 'BTC'
        assert symbol.quote == 'USDT'
        assert symbol.timeframe == '1h'

    def test_register_and_prepare_existing_symbol(self, plugin, session):
        # 첫 번째 등록
        symbol1 = plugin.register_and_prepare(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        # 동일 Symbol 재등록 (기존 반환)
        symbol2 = plugin.register_and_prepare(
            session,
            archetype='CRYPTO',
            exchange='BINANCE',
            tradetype='SPOT',
            base='BTC',
            quote='USDT',
            timeframe='1h'
        )

        # 같은 ID 반환
        assert symbol1.id == symbol2.id

    def test_register_and_prepare_with_optional_fields(self, plugin, session):
        # 옵션 필드 포함 등록
        symbol = plugin.register_and_prepare(
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

        # 옵션 필드 확인
        assert symbol.full_name == 'Bitcoin/USDT'
        assert symbol.listed_at == 1609459200

    def test_register_and_prepare_calls_prepare_table(self, plugin, session):
        # prepare_table이 호출되는지 확인
        with patch.object(plugin.symbol_metadata, 'prepare_table') as mock_prepare:
            symbol = plugin.register_and_prepare(
                session,
                archetype='CRYPTO',
                exchange='BINANCE',
                tradetype='SPOT',
                base='BTC',
                quote='USDT',
                timeframe='1h'
            )

            # prepare_table이 생성된 Symbol과 함께 호출되었는지 확인
            mock_prepare.assert_called_once()
            call_args = mock_prepare.call_args[0]
            assert call_args[0].id == symbol.id

    def test_register_and_prepare_multiple_symbols(self, plugin, session):
        # 여러 Symbol 등록
        symbol1 = plugin.register_and_prepare(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'BTC', 'USDT', '1h'
        )
        symbol2 = plugin.register_and_prepare(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'ETH', 'USDT', '1h'
        )
        symbol3 = plugin.register_and_prepare(
            session, 'CRYPTO', 'UPBIT', 'SPOT', 'BTC', 'KRW', '1d'
        )

        # 각각 다른 ID 할당
        assert symbol1.id != symbol2.id
        assert symbol2.id != symbol3.id
        assert symbol1.id != symbol3.id

    def test_register_and_prepare_lowercase_converts_to_uppercase(self, plugin, session):
        # 소문자 입력 시 대문자 변환
        symbol = plugin.register_and_prepare(
            session,
            archetype='crypto',
            exchange='binance',
            tradetype='spot',
            base='btc',
            quote='usdt',
            timeframe='1h'
        )

        # 대문자로 저장되었는지 확인
        assert symbol.archetype == 'CRYPTO'
        assert symbol.exchange == 'BINANCE'
        assert symbol.tradetype == 'SPOT'
        assert symbol.base == 'BTC'
        assert symbol.quote == 'USDT'
        assert symbol.timeframe == '1h'

    def test_register_and_prepare_unified_table(self, plugin, session):
        # 통합 테이블 Symbol (1h, 4h 등)
        symbol = plugin.register_and_prepare(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'BTC', 'USDT', '1h'
        )

        # is_unified() 확인
        assert symbol.is_unified() == True
        assert symbol.get_table_name() == 'crypto_binance_spot_1h'

    def test_register_and_prepare_individual_table(self, plugin, session):
        # 개별 테이블 Symbol (1m, 3m 등)
        symbol = plugin.register_and_prepare(
            session, 'CRYPTO', 'BINANCE', 'SPOT', 'BTC', 'USDT', '1m'
        )

        # is_unified() 확인
        assert symbol.is_unified() == False
        assert symbol.get_table_name() == 'crypto_binance_spot_btc_usdt_1m'
