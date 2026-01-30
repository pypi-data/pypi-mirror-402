import pandas as pd
from candle_data_manager.Core.CandleFetcher.Core.TimeConverter.TimeConverter import TimeConverter
from candle_data_manager.Core.Models.CandleRepository import CandleRepository


class NormalizationService:

    def normalize_binance(self, raw_data: list[dict]) -> list[dict]:
        # Binance API 응답 정규화
        if not raw_data:
            return []

        result = []
        for candle in raw_data:
            # 키 매핑: t→timestamp, o→open, h→high, l→low, c→close, v→volume
            timestamp_ms = candle["t"]
            timestamp_sec = TimeConverter.mutate_to(timestamp_ms, "timestamp")

            # string → float → int (× 10^8)
            normalized = {
                "timestamp": timestamp_sec,
                "open": CandleRepository.to_storage(float(candle["o"])),
                "high": CandleRepository.to_storage(float(candle["h"])),
                "low": CandleRepository.to_storage(float(candle["l"])),
                "close": CandleRepository.to_storage(float(candle["c"])),
                "volume": CandleRepository.to_storage(float(candle["v"]))
            }
            result.append(normalized)

        return result

    def normalize_upbit(self, raw_data: list[dict]) -> list[dict]:
        # Upbit API 응답 정규화
        if not raw_data:
            return []

        result = []
        for candle in raw_data:
            # 키 매핑
            timestamp_ms = candle["timestamp"]
            timestamp_sec = TimeConverter.mutate_to(timestamp_ms, "timestamp")

            # 가격 int 변환
            normalized = {
                "timestamp": timestamp_sec,
                "open": CandleRepository.to_storage(candle["opening_price"]),
                "high": CandleRepository.to_storage(candle["high_price"]),
                "low": CandleRepository.to_storage(candle["low_price"]),
                "close": CandleRepository.to_storage(candle["trade_price"]),
                "volume": CandleRepository.to_storage(candle["candle_acc_trade_volume"])
            }
            result.append(normalized)

        return result

    def normalize_binance_spot(self, raw_data: list) -> list[dict]:
        # Binance Spot API 응답 정규화
        if not raw_data:
            return []

        result = []
        for candle in raw_data:
            # candle: [timestamp_ms, open, high, low, close, volume, ...]
            timestamp_ms = candle[0]
            timestamp_sec = TimeConverter.mutate_to(timestamp_ms, "timestamp")

            # string → float → int (× 10^8)
            normalized = {
                "timestamp": timestamp_sec,
                "open": CandleRepository.to_storage(float(candle[1])),
                "high": CandleRepository.to_storage(float(candle[2])),
                "low": CandleRepository.to_storage(float(candle[3])),
                "close": CandleRepository.to_storage(float(candle[4])),
                "volume": CandleRepository.to_storage(float(candle[5]))
            }
            result.append(normalized)

        return result

    def normalize_binance_futures(self, raw_data: list) -> list[dict]:
        # Binance Futures API 응답 정규화 (Spot과 동일한 형식)
        if not raw_data:
            return []

        result = []
        for candle in raw_data:
            # candle: [timestamp_ms, open, high, low, close, volume, ...]
            timestamp_ms = candle[0]
            timestamp_sec = TimeConverter.mutate_to(timestamp_ms, "timestamp")

            # string → float → int (× 10^8)
            normalized = {
                "timestamp": timestamp_sec,
                "open": CandleRepository.to_storage(float(candle[1])),
                "high": CandleRepository.to_storage(float(candle[2])),
                "low": CandleRepository.to_storage(float(candle[3])),
                "close": CandleRepository.to_storage(float(candle[4])),
                "volume": CandleRepository.to_storage(float(candle[5]))
            }
            result.append(normalized)

        return result

    def normalize_fdr(self, raw_data: pd.DataFrame) -> list[dict]:
        # FDR DataFrame 정규화
        if raw_data.empty:
            return []

        result = []
        for timestamp, row in raw_data.iterrows():
            # index(datetime)를 timestamp로 변환
            timestamp_sec = TimeConverter.mutate_to(timestamp, "timestamp")

            # 가격 int 변환
            normalized = {
                "timestamp": timestamp_sec,
                "open": CandleRepository.to_storage(row["Open"]),
                "high": CandleRepository.to_storage(row["High"]),
                "low": CandleRepository.to_storage(row["Low"]),
                "close": CandleRepository.to_storage(row["Close"]),
                "volume": CandleRepository.to_storage(row["Volume"])
            }
            result.append(normalized)

        return result
