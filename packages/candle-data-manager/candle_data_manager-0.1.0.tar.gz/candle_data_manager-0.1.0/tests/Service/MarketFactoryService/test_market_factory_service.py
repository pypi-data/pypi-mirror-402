import pytest
import pandas as pd
from candle_data_manager.Service.MarketFactoryService import MarketFactoryService
from candle_data_manager.Particles.Market import Market
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def service():
    return MarketFactoryService()


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


@pytest.fixture
def sample_candles():
    return pd.DataFrame({
        'timestamp': [1700000000, 1700003600, 1700007200],
        'open': [50000.0, 50100.0, 50200.0],
        'high': [50500.0, 50600.0, 50700.0],
        'low': [49500.0, 49600.0, 49700.0],
        'close': [50050.0, 50150.0, 50250.0],
        'volume': [1000.0, 1100.0, 1200.0]
    })


def test_create_market_success(service, sample_symbol, sample_candles):
    # MarketFactoryService.create_market를 호출하여 Market 객체 생성
    market = service.create_market(sample_symbol, sample_candles)

    # Market 객체가 정상적으로 생성되었는지 확인
    assert isinstance(market, Market)
    assert market.symbol == sample_symbol
    assert market.candles is sample_candles
    assert len(market.candles) == 3


def test_create_market_with_empty_dataframe(service, sample_symbol):
    # 빈 DataFrame으로 Market 생성
    empty_candles = pd.DataFrame()
    market = service.create_market(sample_symbol, empty_candles)

    # 빈 DataFrame도 정상적으로 처리
    assert isinstance(market, Market)
    assert market.symbol == sample_symbol
    assert len(market.candles) == 0


def test_create_market_preserves_dataframe_reference(service, sample_symbol, sample_candles):
    # 같은 DataFrame 참조를 유지하는지 확인
    market = service.create_market(sample_symbol, sample_candles)

    # DataFrame 참조가 동일한지 확인
    assert market.candles is sample_candles


def test_create_market_with_different_symbols(service, sample_candles):
    # 다양한 Symbol로 Market 생성
    symbols = [
        Symbol(archetype="CRYPTO", exchange="BINANCE", tradetype="SPOT", base="ETH", quote="USDT", timeframe="1h"),
        Symbol(archetype="CRYPTO", exchange="UPBIT", tradetype="SPOT", base="BTC", quote="KRW", timeframe="1d"),
        Symbol(archetype="STOCK", exchange="KRX", tradetype="SPOT", base="005930", quote="KRW", timeframe="1d"),
    ]

    for symbol in symbols:
        market = service.create_market(symbol, sample_candles)
        assert isinstance(market, Market)
        assert market.symbol == symbol
        assert market.candles is sample_candles
