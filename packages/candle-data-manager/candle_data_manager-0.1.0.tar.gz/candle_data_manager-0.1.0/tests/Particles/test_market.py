import pytest
import pandas as pd
from candle_data_manager.Particles.Market import Market
from candle_data_manager.Core.Models.Symbol import Symbol


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


def test_market_creation(sample_symbol, sample_candles):
    market = Market(symbol=sample_symbol, candles=sample_candles)

    assert market.symbol == sample_symbol
    assert isinstance(market.candles, pd.DataFrame)
    assert len(market.candles) == 3


def test_market_symbol_access(sample_symbol, sample_candles):
    market = Market(symbol=sample_symbol, candles=sample_candles)

    assert market.symbol.archetype == "CRYPTO"
    assert market.symbol.exchange == "BINANCE"
    assert market.symbol.base == "BTC"
    assert market.symbol.quote == "USDT"


def test_market_candles_access(sample_symbol, sample_candles):
    market = Market(symbol=sample_symbol, candles=sample_candles)

    assert 'timestamp' in market.candles.columns
    assert 'open' in market.candles.columns
    assert 'close' in market.candles.columns

    first_candle = market.candles.iloc[0]
    assert first_candle['timestamp'] == 1700000000
    assert first_candle['open'] == 50000.0


def test_market_with_empty_candles(sample_symbol):
    empty_candles = pd.DataFrame()
    market = Market(symbol=sample_symbol, candles=empty_candles)

    assert market.symbol == sample_symbol
    assert len(market.candles) == 0
