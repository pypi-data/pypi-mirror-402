from datetime import datetime

import FinanceDataReader as fdr

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService


class FdrProvider:
    """
    FinanceDataReader를 사용한 금융 데이터 조회

    지원 거래소:
    - KRX (한국): KOSPI, KOSDAQ, KONEX
    - NYSE (미국): 뉴욕증권거래소
    - NASDAQ (미국): 나스닥
    - AMEX (미국): 미국증권거래소
    - SSE, SZSE (중국), HKEX (홍콩), TSE (일본)

    API 키 불필요 (공개 데이터)
    """
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

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
