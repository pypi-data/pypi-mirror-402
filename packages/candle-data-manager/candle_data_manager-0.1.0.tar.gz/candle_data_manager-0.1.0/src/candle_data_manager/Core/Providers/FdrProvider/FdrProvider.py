from datetime import datetime

import FinanceDataReader as fdr

from ...ConnectionManager.ConnectionManager import ConnectionManager
from ...Models.Symbol import Symbol
from ...Utils.NormalizationService.NormalizationService import NormalizationService
from ...Utils.NullHandlingService.NullHandlingService import NullHandlingService
from ....Particles.NoApiKeyError import NoApiKeyError
from ....Particles.ServerNotRespondedError import ServerNotRespondedError
from ....Particles.InvalidDataError import InvalidDataError


# FinanceDataReader를 사용한 금융 데이터 조회
class FdrProvider:
    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._normalization = NormalizationService()
        self._null_handling = NullHandlingService(conn_manager)

    @property
    def archetype(self) -> str:
        return "STOCK"

    @property
    def exchange(self) -> str:
        # FDR은 여러 거래소 지원하지만, 현재 설계상 KRX/NYSE/NASDAQ 모두 FdrProvider 사용
        # exchange property는 고정값이어야 하므로 "MULTI"로 설정
        return "MULTI"

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
        raise NotImplementedError("get_market_list not implemented yet")

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        raise NotImplementedError("get_data_range not implemented yet")
