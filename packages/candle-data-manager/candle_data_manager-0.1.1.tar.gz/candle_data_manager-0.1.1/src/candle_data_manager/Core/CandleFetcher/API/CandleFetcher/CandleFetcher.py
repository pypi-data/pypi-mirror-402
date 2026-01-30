from ....ConnectionManager.ConnectionManager import ConnectionManager
from ....Models.Symbol import Symbol
from ...Core.TimeConverter.TimeConverter import TimeConverter
from ...Plugin.BinanceSpotProvider import BinanceSpotProvider
from ...Plugin.BinanceFuturesProvider import BinanceFuturesProvider
from ...Plugin.UpbitProvider import UpbitProvider
from ...Plugin.FdrProvider import FdrProvider
from ...Exceptions.ProviderNotImplementedError import ProviderNotImplementedError


class CandleFetcher:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._conn_manager = conn_manager
        self._providers = {}

    def fetch(self, symbol: Symbol, start_at: str | int, end_at: str | int) -> list[dict]:
        provider = self._get_provider(symbol)

        start_timestamp = TimeConverter.mutate_to(start_at, "timestamp")
        end_timestamp = TimeConverter.mutate_to(end_at, "timestamp")

        return provider.fetch(symbol, start_timestamp, end_timestamp)

    def _get_provider_key(self, symbol: Symbol) -> str:
        if symbol.exchange == "BINANCE":
            return f"BINANCE_{symbol.tradetype}"
        elif symbol.exchange == "UPBIT":
            return "UPBIT"
        elif symbol.exchange in ["KRX", "NYSE", "NASDAQ", "AMEX", "SSE", "SZSE", "HKEX", "TSE"]:
            return "FDR"
        else:
            raise ProviderNotImplementedError(symbol.exchange)

    def _get_provider(self, symbol: Symbol):
        key = self._get_provider_key(symbol)

        if key not in self._providers:
            if key == "BINANCE_SPOT":
                self._providers[key] = BinanceSpotProvider(self._conn_manager)
            elif key == "BINANCE_FUTURES":
                self._providers[key] = BinanceFuturesProvider(self._conn_manager)
            elif key == "UPBIT":
                self._providers[key] = UpbitProvider(self._conn_manager)
            elif key == "FDR":
                self._providers[key] = FdrProvider(self._conn_manager)

        return self._providers[key]
