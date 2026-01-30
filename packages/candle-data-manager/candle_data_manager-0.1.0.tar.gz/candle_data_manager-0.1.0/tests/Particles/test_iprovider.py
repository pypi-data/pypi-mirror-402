import pytest
from candle_data_manager.Particles.IProvider import IProvider
from candle_data_manager.Core.Models.Symbol import Symbol


class MockProvider:
    @property
    def archetype(self) -> str:
        return "CRYPTO"

    @property
    def exchange(self) -> str:
        return "BINANCE"

    @property
    def tradetype(self) -> str:
        return "SPOT"

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        return [
            {
                'timestamp': 1700000000,
                'open': 5000000000000,
                'high': 5100000000000,
                'low': 4900000000000,
                'close': 5050000000000,
                'volume': 1000000000
            }
        ]

    def get_market_list(self) -> list[dict]:
        return [
            {
                "base": "BTC",
                "quote": "USDT",
                "timeframes": ["1m", "1h", "1d"],
                "listed_at": 1600000000,
                "full_name": "Bitcoin/Tether"
            }
        ]

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        return (1600000000, 1700000000)


def test_mock_provider_satisfies_protocol():
    # MockProvider가 IProvider Protocol을 만족하는지 확인
    provider: IProvider = MockProvider()

    assert provider.archetype == "CRYPTO"
    assert provider.exchange == "BINANCE"
    assert provider.tradetype == "SPOT"

    # Symbol 생성
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )

    # fetch 메서드 테스트
    candles = provider.fetch(symbol, 1700000000, 1700003600)
    assert isinstance(candles, list)
    assert len(candles) > 0
    assert 'timestamp' in candles[0]
    assert 'open' in candles[0]
    assert 'high' in candles[0]
    assert 'low' in candles[0]
    assert 'close' in candles[0]
    assert 'volume' in candles[0]

    # get_market_list 메서드 테스트
    markets = provider.get_market_list()
    assert isinstance(markets, list)
    assert len(markets) > 0
    assert 'base' in markets[0]
    assert 'quote' in markets[0]
    assert 'timeframes' in markets[0]

    # get_data_range 메서드 테스트
    data_range = provider.get_data_range(symbol)
    assert isinstance(data_range, tuple)
    assert len(data_range) == 2


def test_fetch_returns_correct_data_structure():
    # fetch가 올바른 데이터 구조를 반환하는지 확인
    provider: IProvider = MockProvider()
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )

    candles = provider.fetch(symbol, 1700000000, 1700003600)

    # 각 캔들 데이터가 정확한 타입인지 확인
    for candle in candles:
        assert isinstance(candle['timestamp'], int)
        assert isinstance(candle['open'], int)
        assert isinstance(candle['high'], int)
        assert isinstance(candle['low'], int)
        assert isinstance(candle['close'], int)
        assert isinstance(candle['volume'], int)


def test_get_market_list_returns_correct_structure():
    # get_market_list가 올바른 구조를 반환하는지 확인
    provider: IProvider = MockProvider()

    markets = provider.get_market_list()

    for market in markets:
        assert isinstance(market['base'], str)
        assert isinstance(market['quote'], str)
        assert isinstance(market['timeframes'], list)
        assert market['listed_at'] is None or isinstance(market['listed_at'], int)
        assert market['full_name'] is None or isinstance(market['full_name'], str)


def test_get_data_range_returns_optional_values():
    # get_data_range가 옵셔널 값을 올바르게 반환하는지 확인
    provider: IProvider = MockProvider()
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )

    data_range = provider.get_data_range(symbol)

    # 각 값은 int 또는 None
    assert data_range[0] is None or isinstance(data_range[0], int)
    assert data_range[1] is None or isinstance(data_range[1], int)
