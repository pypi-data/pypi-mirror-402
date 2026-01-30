from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.Models.CandleRepository import CandleRepository
from candle_data_manager.Particles.InvalidDataError import InvalidDataError


class NullHandlingService:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._conn_manager = conn_manager

    def handle(self, data: list[dict], symbol: Symbol) -> list[dict]:
        # 빈 리스트 처리
        if not data:
            return []

        result = []
        prev_close = None

        # 첫 번째 캔들이 null인 경우 DB에서 조회
        if self._has_price_null(data[0]):
            prev_close = self._get_last_close_from_db(symbol, data[0]['timestamp'])

        for candle in data:
            processed = candle.copy()

            # volume null 처리
            if processed['volume'] is None:
                processed['volume'] = 0

            # 가격 null 처리
            if self._has_price_null(processed):
                if prev_close is None:
                    raise InvalidDataError("Cannot fill null prices: no previous data available")

                # 모든 null 가격을 이전 close 값으로 채움
                if processed['open'] is None:
                    processed['open'] = prev_close
                if processed['high'] is None:
                    processed['high'] = prev_close
                if processed['low'] is None:
                    processed['low'] = prev_close
                if processed['close'] is None:
                    processed['close'] = prev_close

            # 다음 캔들을 위해 현재 캔들의 close 저장
            prev_close = processed['close']

            result.append(processed)

        return result

    def _has_price_null(self, candle: dict) -> bool:
        # OHLC 중 하나라도 null이면 True
        return (
            candle['open'] is None or
            candle['high'] is None or
            candle['low'] is None or
            candle['close'] is None
        )

    def _get_last_close_from_db(self, symbol: Symbol, first_timestamp: int) -> float:
        # DB에서 마지막 캔들 조회
        with self._conn_manager.get_connection() as conn:
            df = CandleRepository.query_to_dataframe(
                conn,
                symbol,
                symbol_id=symbol.id,
                end_ts=first_timestamp
            )

            if df.empty:
                raise InvalidDataError("Cannot fill null prices: no previous data available in DB")

            # 마지막 행의 close 값 반환 (이미 float로 변환됨)
            return df.iloc[-1]['close']
