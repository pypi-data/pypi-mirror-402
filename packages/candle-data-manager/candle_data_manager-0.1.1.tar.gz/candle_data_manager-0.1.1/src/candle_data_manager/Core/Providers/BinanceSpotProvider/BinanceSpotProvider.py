from binance.spot import Spot

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.ApiValidationService.ApiValidationService import ApiValidationService
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService
from ...Utils.Throttler import SyncThrottler


class BinanceSpotProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._api_validation = ApiValidationService()
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

        # Throttler 설정 (분당 6000 weight, klines=2 weight → 분당 3000회 → 초당 50회)
        self._throttler = SyncThrottler(
            requests_per_second=50,
            requests_per_minute=3000,
            name="BinanceSpot"
        )

        api_key = self._api_validation.get_api_key("BINANCE")
        api_secret = self._api_validation.get_api_secret("BINANCE")

        self._api_validation.check_server("BINANCE", api_key)

        self._client = Spot(api_key=api_key, api_secret=api_secret)

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
        ticker = f"{symbol.base}{symbol.quote}"
        interval = self._map_timeframe_to_interval(symbol.timeframe)

        all_data = []
        current_start_ms = start_at * 1000
        end_time_ms = end_at * 1000

        # 페이지네이션: limit=1000씩 반복 요청
        while current_start_ms < end_time_ms:
            self._throttler.wait()
            response = self._client.klines(
                symbol=ticker,
                interval=interval,
                startTime=current_start_ms,
                endTime=end_time_ms,
                limit=1000
            )

            if not response:
                break

            all_data.extend(response)

            # 마지막 candle의 close_time + 1ms를 다음 시작점으로
            last_close_time = response[-1][6]
            current_start_ms = last_close_time + 1

            # 1000개 미만이면 더 이상 데이터 없음
            if len(response) < 1000:
                break

        if not all_data:
            return []

        normalized_data = self._normalization.normalize_binance_spot(all_data)
        result = self._null_handling.handle(normalized_data, symbol)

        return result

    def get_market_list(self) -> list[dict]:
        """거래 가능한 심볼 목록 반환"""
        self._throttler.wait()
        response = self._client.exchange_info()
        symbols = response.get("symbols", [])

        result = []
        for s in symbols:
            if s.get("status") == "TRADING":
                result.append({
                    "symbol": s.get("symbol"),
                    "base": s.get("baseAsset"),
                    "quote": s.get("quoteAsset"),
                    "status": s.get("status"),
                })
        return result

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        """심볼의 데이터 범위 (oldest_timestamp, latest_timestamp) 반환 (초 단위)"""
        ticker = f"{symbol.base}{symbol.quote}"
        interval = self._map_timeframe_to_interval(symbol.timeframe)

        # Binance API는 startTime=0 조회 시 가장 오래된 데이터 반환
        self._throttler.wait()
        oldest_response = self._client.klines(symbol=ticker, interval=interval, startTime=0, limit=1)
        self._throttler.wait()
        latest_response = self._client.klines(symbol=ticker, interval=interval, limit=1)

        if not oldest_response or not latest_response:
            return (None, None)

        oldest_ts = oldest_response[0][0] // 1000  # ms -> s
        latest_ts = latest_response[0][0] // 1000

        return (oldest_ts, latest_ts)

    def get_supported_timeframes(self) -> list[str]:
        """지원하는 타임프레임 목록 반환"""
        return ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]

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
