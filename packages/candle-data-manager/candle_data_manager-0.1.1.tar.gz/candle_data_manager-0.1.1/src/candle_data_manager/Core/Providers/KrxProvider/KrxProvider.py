import time
from datetime import datetime, timedelta

import FinanceDataReader as fdr

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService

# 일봉 기준 이진 탐색 시작 지수 (2^12 = 4096일 ≈ 11년)
_INITIAL_SEARCH_EXPONENT = 12
_DAY_SECONDS = 86400


# FinanceDataReader를 사용한 KRX 데이터 조회
class KrxProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

    @property
    def archetype(self) -> str:
        return "STOCK"

    @property
    def exchange(self) -> str:
        return "KRX"

    @property
    def tradetype(self) -> str:
        return "SPOT"

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        ticker = symbol.base

        start_datetime = datetime.fromtimestamp(start_at)
        end_datetime = datetime.fromtimestamp(end_at)

        df = fdr.DataReader(ticker, start_datetime, end_datetime)

        if df is None or df.empty:
            return []

        normalized_data = self._normalization.normalize_fdr(df)

        result = self._null_handling.handle(normalized_data, symbol)

        return result

    def get_market_list(self) -> list[dict]:
        """KRX 상장 종목 목록 반환"""
        df = fdr.StockListing("KRX")

        result = []
        for _, row in df.iterrows():
            result.append({
                "symbol": row.get("Code") or row.get("Symbol"),
                "name": row.get("Name"),
                "market": row.get("Market"),
            })
        return result

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        """심볼의 데이터 범위 (oldest_timestamp, latest_timestamp) 반환 (초 단위)"""
        ticker = symbol.base

        # 최신 데이터 조회
        today = datetime.now().strftime("%Y-%m-%d")
        latest_df = fdr.DataReader(ticker, today)
        if latest_df is None or latest_df.empty:
            # 오늘 데이터 없으면 최근 7일 조회
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            latest_df = fdr.DataReader(ticker, week_ago)
            if latest_df is None or latest_df.empty:
                return (None, None)

        latest_ts = int(latest_df.index[-1].timestamp())

        # 이진 탐색으로 가장 오래된 데이터 찾기
        oldest_ts = self._find_oldest_timestamp(ticker, latest_ts)

        return (oldest_ts, latest_ts)

    def get_supported_timeframes(self) -> list[str]:
        """지원하는 타임프레임 목록 반환 (FDR은 일봉만 지원)"""
        return ["1d"]

    def _find_oldest_timestamp(self, ticker: str, latest_ts: int) -> int | None:
        """이진 탐색으로 가장 오래된 데이터의 timestamp 찾기"""
        now_ts = int(time.time())

        # 1단계: 지수적 확장으로 데이터 없는 시점 찾기 (누적 합 방식)
        total_days = 0
        exponent = _INITIAL_SEARCH_EXPONENT
        has_data_ts = latest_ts
        last_jump = 0

        while exponent < 40:
            jump = 2 ** exponent
            total_days += jump
            check_ts = now_ts - (total_days * _DAY_SECONDS)

            if check_ts < 0:
                break

            check_date = datetime.fromtimestamp(check_ts).strftime("%Y-%m-%d")
            check_end = (datetime.fromtimestamp(check_ts) + timedelta(days=7)).strftime("%Y-%m-%d")
            df = fdr.DataReader(ticker, check_date, check_end)

            if df is not None and not df.empty:
                has_data_ts = int(df.index[0].timestamp())
                last_jump = jump
                exponent += 1
            else:
                total_days -= jump
                break

        # 2단계: 이진 탐색 (감쇄 방식)
        step = last_jump // 2 if last_jump else (2 ** _INITIAL_SEARCH_EXPONENT) // 2

        while step >= 1:
            check_ts = now_ts - ((total_days + step) * _DAY_SECONDS)

            if check_ts < 0:
                step //= 2
                continue

            check_date = datetime.fromtimestamp(check_ts).strftime("%Y-%m-%d")
            check_end = (datetime.fromtimestamp(check_ts) + timedelta(days=7)).strftime("%Y-%m-%d")
            df = fdr.DataReader(ticker, check_date, check_end)

            if df is not None and not df.empty:
                has_data_ts = int(df.index[0].timestamp())
                total_days += step

            step //= 2

        return has_data_ts
