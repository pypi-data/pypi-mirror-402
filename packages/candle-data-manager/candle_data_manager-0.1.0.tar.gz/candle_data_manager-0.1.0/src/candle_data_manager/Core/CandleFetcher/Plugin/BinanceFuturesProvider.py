from binance.um_futures import UMFutures

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.ApiValidationService.ApiValidationService import ApiValidationService
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService


class BinanceFuturesProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._api_validation = ApiValidationService()
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

        api_key = self._api_validation.get_api_key("BINANCE")
        api_secret = self._api_validation.get_api_secret("BINANCE")

        self._api_validation.check_server("BINANCE", api_key)

        self._client = UMFutures(key=api_key, secret=api_secret)

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        ticker = f"{symbol.base}{symbol.quote}"

        interval = self._map_timeframe_to_interval(symbol.timeframe)

        start_time_ms = start_at * 1000
        end_time_ms = end_at * 1000

        response = self._client.klines(
            symbol=ticker,
            interval=interval,
            startTime=start_time_ms,
            endTime=end_time_ms,
            limit=1000
        )

        if not response:
            return []

        normalized_data = self._normalization.normalize_binance_futures(response)

        result = self._null_handling.handle(normalized_data, symbol)

        return result

    def _map_timeframe_to_interval(self, timeframe: str) -> str:
        mapping = {
            "1m": "1m",
            "3m": "3m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
            "6h": "6h",
            "8h": "8h",
            "12h": "12h",
            "1d": "1d",
            "3d": "3d",
            "1w": "1w",
            "1M": "1M"
        }

        return mapping.get(timeframe, "1d")
