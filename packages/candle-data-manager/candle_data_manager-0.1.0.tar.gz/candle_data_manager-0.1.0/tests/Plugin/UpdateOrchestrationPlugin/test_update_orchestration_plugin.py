import pytest
from unittest.mock import Mock, patch, call
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from candle_data_manager.Core.Models import Base
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Plugin.UpdateOrchestrationPlugin.UpdateOrchestrationPlugin import UpdateOrchestrationPlugin
from candle_data_manager.Particles.UpdateResult import UpdateResult


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


@pytest.fixture
def symbol_service():
    return Mock()


@pytest.fixture
def data_fetch_service():
    return Mock()


@pytest.fixture
def data_save_service():
    return Mock()


@pytest.fixture
def symbol_metadata():
    return Mock()


@pytest.fixture
def symbol_prep_plugin():
    return Mock()


@pytest.fixture
def plugin(symbol_service, data_fetch_service, data_save_service, symbol_metadata, symbol_prep_plugin):
    return UpdateOrchestrationPlugin(
        symbol_service=symbol_service,
        data_fetch_service=data_fetch_service,
        data_save_service=data_save_service,
        symbol_metadata=symbol_metadata,
        symbol_prep_plugin=symbol_prep_plugin
    )


class TestUpdateOrchestrationPluginActiveUpdate:
    """active_update 메서드 테스트"""

    def test_active_update_basic_flow(self, plugin, data_fetch_service, symbol_prep_plugin, data_save_service, session):
        # Given
        archetype = 'CRYPTO'
        exchange = 'BINANCE'
        tradetype = 'SPOT'

        # Mock market list
        market_list = [
            {"base": "BTC", "quote": "USDT", "timeframes": ["1h"], "listed_at": None, "full_name": "Bitcoin"},
            {"base": "ETH", "quote": "USDT", "timeframes": ["1h"], "listed_at": None, "full_name": "Ethereum"},
        ]
        data_fetch_service.get_market_list.return_value = market_list

        # Mock symbols
        btc_symbol = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="BTC", quote="USDT", timeframe="1h")
        eth_symbol = Symbol(id=2, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="ETH", quote="USDT", timeframe="1h")

        symbol_prep_plugin.register_and_prepare.side_effect = [btc_symbol, eth_symbol]

        # Mock fetch data (작은 데이터셋)
        btc_data = [
            {"timestamp": 1000, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100}
        ]
        eth_data = [
            {"timestamp": 1000, "open": 2000, "high": 2100, "low": 1900, "close": 2050, "volume": 200}
        ]
        data_fetch_service.fetch_all_data.side_effect = [btc_data, eth_data]

        # When
        result = plugin.active_update(session, archetype, exchange, tradetype)

        # Then
        # market list 조회 확인
        data_fetch_service.get_market_list.assert_called_once_with(archetype, exchange, tradetype)

        # Symbol 등록 및 준비 확인 (각 timeframe마다)
        assert symbol_prep_plugin.register_and_prepare.call_count == 2

        # fetch_all_data 호출 확인
        assert data_fetch_service.fetch_all_data.call_count == 2

        # bulk_save 호출 확인 (마지막 Symbol이므로 버퍼 flush)
        data_save_service.bulk_save.assert_called_once()

        # UpdateResult 확인
        assert isinstance(result, UpdateResult)
        assert len(result.success_symbols) == 2
        assert len(result.failed_symbols) == 0
        assert result.total_rows == 2

    def test_active_update_with_buffer_overflow(self, plugin, data_fetch_service, symbol_prep_plugin, data_save_service, session):
        # Given - 버퍼 크기를 10으로 설정하고 테스트
        plugin.buffer_size = 10

        archetype = 'CRYPTO'
        exchange = 'BINANCE'
        tradetype = 'SPOT'

        # 3개의 마켓, 각각 6, 5, 4개의 row (총 15 rows)
        # 6+5=11>10이므로 첫번째 오버플로우, 남은 4개는 마지막 flush
        market_list = [
            {"base": "BTC", "quote": "USDT", "timeframes": ["1h"]},
            {"base": "ETH", "quote": "USDT", "timeframes": ["1h"]},
            {"base": "XRP", "quote": "USDT", "timeframes": ["1h"]},
        ]
        data_fetch_service.get_market_list.return_value = market_list

        btc_symbol = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="BTC", quote="USDT", timeframe="1h")
        eth_symbol = Symbol(id=2, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="ETH", quote="USDT", timeframe="1h")
        xrp_symbol = Symbol(id=3, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="XRP", quote="USDT", timeframe="1h")

        symbol_prep_plugin.register_and_prepare.side_effect = [btc_symbol, eth_symbol, xrp_symbol]

        # BTC 6개, ETH 5개, XRP 4개
        btc_data = [{"timestamp": i, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100} for i in range(6)]
        eth_data = [{"timestamp": i, "open": 2000, "high": 2100, "low": 1900, "close": 2050, "volume": 200} for i in range(5)]
        xrp_data = [{"timestamp": i, "open": 3000, "high": 3100, "low": 2900, "close": 3050, "volume": 300} for i in range(4)]

        data_fetch_service.fetch_all_data.side_effect = [btc_data, eth_data, xrp_data]

        # When
        result = plugin.active_update(session, archetype, exchange, tradetype)

        # Then
        # bulk_save가 2번 호출되어야 함 (버퍼 오버플로우 + 마지막 flush)
        assert data_save_service.bulk_save.call_count == 2
        assert result.total_rows == 15

    def test_active_update_with_partial_failure(self, plugin, data_fetch_service, symbol_prep_plugin, data_save_service, session):
        # Given - 일부 Symbol에서 실패 발생
        archetype = 'CRYPTO'
        exchange = 'BINANCE'
        tradetype = 'SPOT'

        market_list = [
            {"base": "BTC", "quote": "USDT", "timeframes": ["1h"]},
            {"base": "ETH", "quote": "USDT", "timeframes": ["1h"]},
            {"base": "XRP", "quote": "USDT", "timeframes": ["1h"]},
        ]
        data_fetch_service.get_market_list.return_value = market_list

        btc_symbol = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="BTC", quote="USDT", timeframe="1h")
        eth_symbol = Symbol(id=2, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="ETH", quote="USDT", timeframe="1h")
        xrp_symbol = Symbol(id=3, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base="XRP", quote="USDT", timeframe="1h")

        symbol_prep_plugin.register_and_prepare.side_effect = [btc_symbol, eth_symbol, xrp_symbol]

        btc_data = [{"timestamp": 1000, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100}]
        # ETH에서 에러 발생
        data_fetch_service.fetch_all_data.side_effect = [
            btc_data,
            Exception("Network error"),
            []  # XRP는 빈 데이터
        ]

        # When
        result = plugin.active_update(session, archetype, exchange, tradetype)

        # Then
        assert len(result.success_symbols) == 2  # BTC, XRP
        assert len(result.failed_symbols) == 1  # ETH
        # 실패한 Symbol의 base 확인
        assert result.failed_symbols[0][0].base == "ETH"
        assert "Network error" in result.failed_symbols[0][1]
        assert result.total_rows == 1  # BTC만 저장됨

    def test_active_update_multiple_timeframes(self, plugin, data_fetch_service, symbol_prep_plugin, data_save_service, session):
        # Given - 하나의 마켓이 여러 timeframe을 가질 경우
        archetype = 'CRYPTO'
        exchange = 'BINANCE'
        tradetype = 'SPOT'

        market_list = [
            {"base": "BTC", "quote": "USDT", "timeframes": ["1h", "1d", "1m"]},
        ]
        data_fetch_service.get_market_list.return_value = market_list

        btc_1h = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype=tradetype,
                       base="BTC", quote="USDT", timeframe="1h")
        btc_1d = Symbol(id=2, archetype=archetype, exchange=exchange, tradetype=tradetype,
                       base="BTC", quote="USDT", timeframe="1d")
        btc_1m = Symbol(id=3, archetype=archetype, exchange=exchange, tradetype=tradetype,
                       base="BTC", quote="USDT", timeframe="1m")

        symbol_prep_plugin.register_and_prepare.side_effect = [btc_1h, btc_1d, btc_1m]

        data_1h = [{"timestamp": 1000, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100}]
        data_1d = [{"timestamp": 2000, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100}]
        data_1m = [{"timestamp": 3000, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100}]

        data_fetch_service.fetch_all_data.side_effect = [data_1h, data_1d, data_1m]

        # When
        result = plugin.active_update(session, archetype, exchange, tradetype)

        # Then
        assert symbol_prep_plugin.register_and_prepare.call_count == 3
        assert data_fetch_service.fetch_all_data.call_count == 3
        assert len(result.success_symbols) == 3
        assert result.total_rows == 3


class TestUpdateOrchestrationPluginPassiveUpdate:
    """passive_update 메서드 테스트"""

    def test_passive_update_basic_flow(self, plugin, symbol_service, symbol_metadata, data_fetch_service, data_save_service, session):
        # Given
        archetype = 'CRYPTO'
        exchange = 'BINANCE'

        # Mock symbols
        btc_symbol = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype='SPOT',
                           base="BTC", quote="USDT", timeframe="1h", last_timestamp=1000)
        eth_symbol = Symbol(id=2, archetype=archetype, exchange=exchange, tradetype='SPOT',
                           base="ETH", quote="USDT", timeframe="1h", last_timestamp=2000)

        symbol_service.find_symbols.return_value = [btc_symbol, eth_symbol]

        # Mock table status
        symbol_metadata.get_table_status.side_effect = [
            {"last_timestamp": 1000},
            {"last_timestamp": 2000}
        ]

        # Mock fetch data (증분 데이터)
        btc_new_data = [{"timestamp": 1100, "open": 10100, "high": 10200, "low": 10000, "close": 10150, "volume": 110}]
        eth_new_data = [{"timestamp": 2100, "open": 2100, "high": 2200, "low": 2000, "close": 2150, "volume": 210}]

        data_fetch_service.fetch.side_effect = [btc_new_data, eth_new_data]

        # When
        result = plugin.passive_update(session, archetype=archetype, exchange=exchange)

        # Then
        # find_symbols 호출 확인 - kwargs로 전달되므로 any_call 사용
        assert symbol_service.find_symbols.call_count == 1
        call_kwargs = symbol_service.find_symbols.call_args[1]
        assert call_kwargs['archetype'] == archetype
        assert call_kwargs['exchange'] == exchange

        # 각 Symbol의 table status 조회
        assert symbol_metadata.get_table_status.call_count == 2

        # fetch 호출 확인 (last_timestamp + 1부터 조회)
        assert data_fetch_service.fetch.call_count == 2

        # bulk_save 호출 확인
        data_save_service.bulk_save.assert_called_once()

        # UpdateResult 확인
        assert isinstance(result, UpdateResult)
        assert len(result.success_symbols) == 2
        assert len(result.failed_symbols) == 0
        assert result.total_rows == 2

    def test_passive_update_with_buffer_overflow(self, plugin, symbol_service, symbol_metadata, data_fetch_service, data_save_service, session):
        # Given - 버퍼 크기를 10으로 설정
        plugin.buffer_size = 10

        archetype = 'CRYPTO'

        # 3개의 Symbol, 각각 5, 6, 4개의 새 row (총 15 rows)
        symbols = [
            Symbol(id=1, archetype=archetype, exchange='BINANCE', tradetype='SPOT',
                  base="BTC", quote="USDT", timeframe="1h", last_timestamp=1000),
            Symbol(id=2, archetype=archetype, exchange='BINANCE', tradetype='SPOT',
                  base="ETH", quote="USDT", timeframe="1h", last_timestamp=2000),
            Symbol(id=3, archetype=archetype, exchange='BINANCE', tradetype='SPOT',
                  base="XRP", quote="USDT", timeframe="1h", last_timestamp=3000),
        ]

        symbol_service.find_symbols.return_value = symbols

        symbol_metadata.get_table_status.side_effect = [
            {"last_timestamp": 1000},
            {"last_timestamp": 2000},
            {"last_timestamp": 3000}
        ]

        data_1 = [{"timestamp": i, "open": 10000, "high": 10100, "low": 9900, "close": 10050, "volume": 100} for i in range(1001, 1006)]  # 5 rows
        data_2 = [{"timestamp": i, "open": 2000, "high": 2100, "low": 1900, "close": 2050, "volume": 200} for i in range(2001, 2007)]  # 6 rows
        data_3 = [{"timestamp": i, "open": 3000, "high": 3100, "low": 2900, "close": 3050, "volume": 300} for i in range(3001, 3005)]  # 4 rows

        data_fetch_service.fetch.side_effect = [data_1, data_2, data_3]

        # When
        result = plugin.passive_update(session, archetype=archetype)

        # Then
        # bulk_save가 2번 호출되어야 함 (5 + 6 = 11 > 10에서 1번, 마지막 4개에서 1번)
        assert data_save_service.bulk_save.call_count == 2
        assert result.total_rows == 15

    def test_passive_update_with_partial_failure(self, plugin, symbol_service, symbol_metadata, data_fetch_service, data_save_service, session):
        # Given - 일부 Symbol에서 실패 발생
        symbols = [
            Symbol(id=1, archetype='CRYPTO', exchange='BINANCE', tradetype='SPOT',
                  base="BTC", quote="USDT", timeframe="1h", last_timestamp=1000),
            Symbol(id=2, archetype='CRYPTO', exchange='BINANCE', tradetype='SPOT',
                  base="ETH", quote="USDT", timeframe="1h", last_timestamp=2000),
        ]

        symbol_service.find_symbols.return_value = symbols

        symbol_metadata.get_table_status.side_effect = [
            {"last_timestamp": 1000},
            Exception("Database connection error")
        ]

        btc_data = [{"timestamp": 1100, "open": 10100, "high": 10200, "low": 10000, "close": 10150, "volume": 110}]
        data_fetch_service.fetch.return_value = btc_data

        # When
        result = plugin.passive_update(session)

        # Then
        assert len(result.success_symbols) == 1  # BTC만 성공
        assert len(result.failed_symbols) == 1  # ETH 실패
        assert result.failed_symbols[0][0] == symbols[1]
        assert "Database connection error" in result.failed_symbols[0][1]

    def test_passive_update_no_new_data(self, plugin, symbol_service, symbol_metadata, data_fetch_service, data_save_service, session):
        # Given - 새로운 데이터가 없는 경우
        symbols = [
            Symbol(id=1, archetype='CRYPTO', exchange='BINANCE', tradetype='SPOT',
                  base="BTC", quote="USDT", timeframe="1h", last_timestamp=1000),
        ]

        symbol_service.find_symbols.return_value = symbols
        symbol_metadata.get_table_status.return_value = {"last_timestamp": 1000}
        data_fetch_service.fetch.return_value = []  # 빈 데이터

        # When
        result = plugin.passive_update(session)

        # Then
        # 빈 버퍼는 bulk_save 호출하지 않음
        data_save_service.bulk_save.assert_not_called()
        assert len(result.success_symbols) == 1
        assert result.total_rows == 0

    def test_passive_update_with_conditions(self, plugin, symbol_service, symbol_metadata, data_fetch_service, data_save_service, session):
        # Given - 조건으로 Symbol 필터링
        archetype = 'CRYPTO'
        exchange = 'BINANCE'
        tradetype = 'SPOT'
        base = 'BTC'

        btc_symbol = Symbol(id=1, archetype=archetype, exchange=exchange, tradetype=tradetype,
                           base=base, quote="USDT", timeframe="1h", last_timestamp=1000)

        symbol_service.find_symbols.return_value = [btc_symbol]
        symbol_metadata.get_table_status.return_value = {"last_timestamp": 1000}

        btc_data = [{"timestamp": 1100, "open": 10100, "high": 10200, "low": 10000, "close": 10150, "volume": 110}]
        data_fetch_service.fetch.return_value = btc_data

        # When
        result = plugin.passive_update(
            session,
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base
        )

        # Then
        # find_symbols가 모든 조건과 함께 호출되었는지 확인
        assert symbol_service.find_symbols.call_count == 1
        call_kwargs = symbol_service.find_symbols.call_args[1]
        assert call_kwargs['archetype'] == archetype
        assert call_kwargs['exchange'] == exchange
        assert call_kwargs['tradetype'] == tradetype
        assert call_kwargs['base'] == base
        assert len(result.success_symbols) == 1
        assert result.total_rows == 1
