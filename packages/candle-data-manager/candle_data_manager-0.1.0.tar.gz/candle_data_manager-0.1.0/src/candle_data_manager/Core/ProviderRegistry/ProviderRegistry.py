from ..ConnectionManager.ConnectionManager import ConnectionManager
from ..Models.Symbol import Symbol
from ..Providers.BinanceSpotProvider import BinanceSpotProvider
from ..Providers.BinanceFuturesProvider import BinanceFuturesProvider
from ..Providers.UpbitProvider import UpbitProvider
from ..Providers.KrxProvider import KrxProvider
from ..Providers.NyseProvider import NyseProvider
from ..Providers.NasdaqProvider import NasdaqProvider
from ...Particles.ProviderNotImplementedError import ProviderNotImplementedError


class ProviderRegistry:
    # Symbol → Provider 인스턴스 선택 및 캐싱

    def __init__(self, conn_manager: ConnectionManager):
        self._conn_manager = conn_manager
        self._instance_cache = {}

    _provider_class_mapping = {
        ("CRYPTO", "BINANCE", "SPOT"): BinanceSpotProvider,
        ("CRYPTO", "BINANCE", "FUTURES"): BinanceFuturesProvider,
        ("CRYPTO", "UPBIT", "SPOT"): UpbitProvider,
        ("STOCK", "KRX", "SPOT"): KrxProvider,
        ("STOCK", "NYSE", "SPOT"): NyseProvider,
        ("STOCK", "NASDAQ", "SPOT"): NasdaqProvider,
    }

    def get_provider(self, symbol: Symbol):
        # Symbol의 archetype, exchange, tradetype에 맞는 Provider 인스턴스 반환
        return self.get_provider_by_key(symbol.archetype, symbol.exchange, symbol.tradetype)

    def get_provider_by_key(self, archetype: str, exchange: str, tradetype: str):
        # archetype, exchange, tradetype으로 Provider 인스턴스 반환
        key = (archetype.upper(), exchange.upper(), tradetype.upper())

        if key in self._instance_cache:
            return self._instance_cache[key]

        if key not in self._provider_class_mapping:
            raise ProviderNotImplementedError(f"{archetype}-{exchange}-{tradetype}")

        provider_class = self._provider_class_mapping[key]
        provider_instance = provider_class(self._conn_manager)
        self._instance_cache[key] = provider_instance

        return provider_instance
