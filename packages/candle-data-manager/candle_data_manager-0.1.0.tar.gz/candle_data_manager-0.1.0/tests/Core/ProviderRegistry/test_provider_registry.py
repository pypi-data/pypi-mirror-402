import pytest
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.Providers.BinanceSpotProvider import BinanceSpotProvider
from candle_data_manager.Core.Providers.BinanceFuturesProvider import BinanceFuturesProvider
from candle_data_manager.Core.Providers.UpbitProvider import UpbitProvider
from candle_data_manager.Core.Providers.KrxProvider import KrxProvider
from candle_data_manager.Core.Providers.NyseProvider import NyseProvider
from candle_data_manager.Particles.ProviderNotImplementedError import ProviderNotImplementedError


@pytest.fixture
def conn_manager():
    return ConnectionManager()


@pytest.fixture
def registry(conn_manager):
    return ProviderRegistry(conn_manager)


@pytest.fixture
def sample_symbol_binance_spot():
    return Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )


@pytest.fixture
def sample_symbol_binance_futures():
    return Symbol(
        archetype="CRYPTO",
        exchange="BINANCE",
        tradetype="FUTURES",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )


@pytest.fixture
def sample_symbol_upbit():
    return Symbol(
        archetype="CRYPTO",
        exchange="UPBIT",
        tradetype="SPOT",
        base="BTC",
        quote="KRW",
        timeframe="1m"
    )


@pytest.fixture
def sample_symbol_krx():
    return Symbol(
        archetype="STOCK",
        exchange="KRX",
        tradetype="SPOT",
        base="005930",
        quote="KRW",
        timeframe="1d"
    )


@pytest.fixture
def sample_symbol_nyse():
    return Symbol(
        archetype="STOCK",
        exchange="NYSE",
        tradetype="SPOT",
        base="AAPL",
        quote="USD",
        timeframe="1d"
    )


def test_get_provider_returns_binance_spot_instance(registry, sample_symbol_binance_spot):
    # Binance Spot Provider 인스턴스 반환 확인
    provider = registry.get_provider(sample_symbol_binance_spot)
    assert isinstance(provider, BinanceSpotProvider)


def test_get_provider_returns_binance_futures_instance(registry, sample_symbol_binance_futures):
    # Binance Futures Provider 인스턴스 반환 확인
    provider = registry.get_provider(sample_symbol_binance_futures)
    assert isinstance(provider, BinanceFuturesProvider)


def test_get_provider_returns_upbit_instance(registry, sample_symbol_upbit):
    # Upbit Provider 인스턴스 반환 확인
    provider = registry.get_provider(sample_symbol_upbit)
    assert isinstance(provider, UpbitProvider)


def test_get_provider_returns_krx_instance(registry, sample_symbol_krx):
    # KRX Provider 인스턴스 반환 확인
    provider = registry.get_provider(sample_symbol_krx)
    assert isinstance(provider, KrxProvider)


def test_get_provider_returns_nyse_instance(registry, sample_symbol_nyse):
    # NYSE Provider 인스턴스 반환 확인
    provider = registry.get_provider(sample_symbol_nyse)
    assert isinstance(provider, NyseProvider)


def test_get_provider_not_implemented(registry):
    # 구현되지 않은 Provider 요청 시 예외 발생
    symbol = Symbol(
        archetype="CRYPTO",
        exchange="UNKNOWN_EXCHANGE",
        tradetype="SPOT",
        base="BTC",
        quote="USDT",
        timeframe="1h"
    )

    with pytest.raises(ProviderNotImplementedError) as exc_info:
        registry.get_provider(symbol)

    assert "CRYPTO-UNKNOWN_EXCHANGE-SPOT" in str(exc_info.value)


def test_get_provider_caching(registry, sample_symbol_binance_spot):
    # 동일한 Symbol에 대해 같은 인스턴스 반환 확인 (캐싱)
    provider1 = registry.get_provider(sample_symbol_binance_spot)
    provider2 = registry.get_provider(sample_symbol_binance_spot)
    assert provider1 is provider2


def test_get_provider_different_symbols_different_instances(registry, sample_symbol_binance_spot, sample_symbol_upbit):
    # 다른 Symbol에 대해 다른 Provider 인스턴스 반환 확인
    provider1 = registry.get_provider(sample_symbol_binance_spot)
    provider2 = registry.get_provider(sample_symbol_upbit)
    assert provider1 is not provider2
    assert isinstance(provider1, BinanceSpotProvider)
    assert isinstance(provider2, UpbitProvider)


def test_provider_has_connection_manager(registry, sample_symbol_binance_spot):
    # Provider가 ConnectionManager를 받았는지 확인
    provider = registry.get_provider(sample_symbol_binance_spot)
    # Provider 내부에서 ConnectionManager를 사용하는지 간접 확인
    assert hasattr(provider, '_null_handling')


def test_provider_properties_binance_spot(registry, sample_symbol_binance_spot):
    # BinanceSpotProvider의 property 확인
    provider = registry.get_provider(sample_symbol_binance_spot)
    assert provider.archetype == "CRYPTO"
    assert provider.exchange == "BINANCE"
    assert provider.tradetype == "SPOT"


def test_provider_properties_krx(registry, sample_symbol_krx):
    # KrxProvider의 property 확인
    provider = registry.get_provider(sample_symbol_krx)
    assert provider.archetype == "STOCK"
    assert provider.exchange == "KRX"
    assert provider.tradetype == "SPOT"
