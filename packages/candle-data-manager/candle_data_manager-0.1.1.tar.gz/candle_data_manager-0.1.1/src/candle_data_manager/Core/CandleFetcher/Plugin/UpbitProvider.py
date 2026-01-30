from datetime import datetime

import pyupbit

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.ApiValidationService.ApiValidationService import ApiValidationService
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService


# Upbit API 호출 및 데이터 정규화
class UpbitProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        # Service 인스턴스 생성
        self._api_validation = ApiValidationService()
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

        # API 키/Secret 필수 체크
        api_key = self._api_validation.get_api_key("UPBIT")
        self._api_validation.get_api_secret("UPBIT")

        # 서버 응답 확인
        self._api_validation.check_server("UPBIT", api_key)

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        # Symbol을 Upbit ticker로 변환 (quote-base)
        ticker = f"{symbol.quote}-{symbol.base}"

        # timeframe을 pyupbit interval로 매핑
        interval = self._map_timeframe_to_interval(symbol.timeframe)

        # pyupbit.get_ohlcv() 호출
        # count는 최대 200으로 설정
        # to는 end_at을 datetime으로 변환
        end_datetime = datetime.fromtimestamp(end_at)

        df = pyupbit.get_ohlcv(ticker=ticker, interval=interval, count=200, to=end_datetime)

        # DataFrame이 None이거나 비어있으면 빈 리스트 반환
        if df is None or df.empty:
            return []

        # DataFrame을 dict 리스트로 변환
        raw_data = []
        for timestamp, row in df.iterrows():
            candle_dict = {
                'timestamp': int(timestamp.timestamp() * 1000),  # ms로 변환
                'opening_price': row['open'],
                'high_price': row['high'],
                'low_price': row['low'],
                'trade_price': row['close'],
                'candle_acc_trade_volume': row['volume']
            }
            raw_data.append(candle_dict)

        # normalize_upbit()로 정규화
        normalized_data = self._normalization.normalize_upbit(raw_data)

        # handle()로 Null 처리
        result = self._null_handling.handle(normalized_data, symbol)

        return result

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
