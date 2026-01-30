import time
from datetime import datetime

import pyupbit

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.ApiValidationService.ApiValidationService import ApiValidationService
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService
from ...Utils.Throttler import SyncThrottler

# 이진 탐색 시작 지수 (timeframe별 10년치 커버)
_INITIAL_SEARCH_EXPONENT = {
    "1d": 12, "4h": 15, "1h": 17, "15m": 19, "5m": 21, "1m": 23,
}

# timeframe → 초 변환
_TIMEFRAME_TO_SECONDS = {
    "1m": 60, "3m": 180, "5m": 300, "10m": 600, "15m": 900, "30m": 1800,
    "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800, "1M": 2592000,
}


# Upbit API 호출 및 데이터 정규화
class UpbitProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        # Service 인스턴스 생성
        self._api_validation = ApiValidationService()
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

        # Throttler 설정 (QUOTATION: 초당 10회, 분당 600회)
        self._throttler = SyncThrottler(
            requests_per_second=10,
            requests_per_minute=600,
            name="Upbit"
        )

        # API 키/Secret 필수 체크
        api_key = self._api_validation.get_api_key("UPBIT")
        self._api_validation.get_api_secret("UPBIT")

        # 서버 응답 확인
        self._api_validation.check_server("UPBIT", api_key)

    @property
    def archetype(self) -> str:
        return "CRYPTO"

    @property
    def exchange(self) -> str:
        return "UPBIT"

    @property
    def tradetype(self) -> str:
        return "SPOT"

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        ticker = f"{symbol.quote}-{symbol.base}"
        interval = self._map_timeframe_to_interval(symbol.timeframe)

        all_data = []
        current_to = datetime.fromtimestamp(end_at)
        start_datetime = datetime.fromtimestamp(start_at)

        # 페이지네이션: to를 이동하면서 200개씩 반복 요청
        while True:
            self._throttler.wait()
            df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=200, to=current_to)

            if df is None or df.empty:
                break

            # DataFrame을 dict 리스트로 변환 (timestamp는 초 단위)
            for ts, row in df.iterrows():
                candle_ts = int(ts.timestamp())

                # start_at 이전 데이터는 무시
                if candle_ts < start_at:
                    continue

                candle_dict = {
                    'timestamp': candle_ts,
                    'opening_price': row['open'],
                    'high_price': row['high'],
                    'low_price': row['low'],
                    'trade_price': row['close'],
                    'candle_acc_trade_volume': row['volume']
                }
                all_data.append(candle_dict)

            # 가장 오래된 데이터의 timestamp 확인
            oldest_ts = int(df.index[0].timestamp())

            # start_at에 도달했거나 지나쳤으면 종료
            if oldest_ts <= start_at:
                break

            # 200개 미만이면 더 이상 데이터 없음
            if len(df) < 200:
                break

            # 다음 요청을 위해 to를 가장 오래된 timestamp로 이동
            current_to = df.index[0]

        if not all_data:
            return []

        # 시간순 정렬 (오름차순)
        all_data.sort(key=lambda x: x['timestamp'])

        # 중복 제거 (timestamp 기준)
        seen = set()
        unique_data = []
        for candle in all_data:
            if candle['timestamp'] not in seen:
                seen.add(candle['timestamp'])
                unique_data.append(candle)

        normalized_data = self._normalization.normalize_upbit(unique_data)
        result = self._null_handling.handle(normalized_data, symbol)

        return result

    def get_market_list(self) -> list[dict]:
        """거래 가능한 마켓 목록 반환"""
        self._throttler.wait()
        tickers = pyupbit.get_tickers()

        result = []
        for ticker in tickers:
            # ticker 형식: "KRW-BTC", "BTC-ETH" 등
            parts = ticker.split("-")
            if len(parts) == 2:
                result.append({
                    "symbol": ticker,
                    "quote": parts[0],  # KRW, BTC, USDT
                    "base": parts[1],   # BTC, ETH 등
                })
        return result

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        """심볼의 데이터 범위 (oldest_timestamp, latest_timestamp) 반환 (초 단위)"""
        ticker = f"{symbol.quote}-{symbol.base}"
        interval = self._map_timeframe_to_interval(symbol.timeframe)

        # 최신 데이터 조회
        self._throttler.wait()
        latest_df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=1)
        if latest_df is None or latest_df.empty:
            return (None, None)

        latest_ts = int(latest_df.index[-1].timestamp())

        # 이진 탐색으로 가장 오래된 데이터 찾기
        oldest_ts = self._find_oldest_timestamp(ticker, interval, symbol.timeframe, latest_ts)

        return (oldest_ts, latest_ts)

    def _find_oldest_timestamp(self, ticker: str, interval: str, timeframe: str, latest_ts: int) -> int | None:
        """이진 탐색으로 가장 오래된 데이터의 timestamp 찾기"""
        tick_seconds = _TIMEFRAME_TO_SECONDS.get(timeframe, 86400)
        initial_exp = _INITIAL_SEARCH_EXPONENT.get(timeframe, 17)

        now_ts = int(time.time())

        # 1단계: 지수적 확장으로 데이터 없는 시점 찾기 (누적 합 방식)
        total_ticks = 0
        exponent = initial_exp
        has_data_ts = latest_ts
        last_jump = 0

        while exponent < 40:
            jump = 2 ** exponent
            total_ticks += jump
            check_ts = now_ts - (total_ticks * tick_seconds)

            if check_ts < 0:
                break

            check_datetime = datetime.fromtimestamp(check_ts)
            self._throttler.wait()
            df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=1, to=check_datetime)

            if df is not None and not df.empty:
                has_data_ts = int(df.index[0].timestamp())
                last_jump = jump
                exponent += 1
            else:
                total_ticks -= jump
                break

        # 2단계: 이진 탐색 (감쇄 방식)
        step = last_jump // 2 if last_jump else (2 ** initial_exp) // 2

        while step >= 1:
            check_ts = now_ts - ((total_ticks + step) * tick_seconds)

            if check_ts < 0:
                step //= 2
                continue

            check_datetime = datetime.fromtimestamp(check_ts)
            self._throttler.wait()
            df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=1, to=check_datetime)

            if df is not None and not df.empty:
                has_data_ts = int(df.index[0].timestamp())
                total_ticks += step

            step //= 2

        return has_data_ts

    def get_supported_timeframes(self) -> list[str]:
        """지원하는 타임프레임 목록 반환"""
        return ["1m", "3m", "5m", "10m", "30m", "1h", "4h", "1d", "1w", "1M"]

    def _map_timeframe_to_interval(self, timeframe: str) -> str:
        # timeframe을 pyupbit interval로 매핑
        mapping = {
            "1m": "minute1",
            "3m": "minute3",
            "5m": "minute5",
            "10m": "minute10",
            "30m": "minute30",
            "1h": "minute60",
            "4h": "minute240",
            "1d": "day",
            "1w": "week",
            "1M": "month"
        }

        return mapping.get(timeframe, "day")
