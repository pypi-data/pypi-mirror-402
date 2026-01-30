import pandas as pd
from loguru import logger

from candle_data_manager.Core.Models.CandleRepository import CandleRepository
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager


class DataLoadService:
    def __init__(self, conn_manager: ConnectionManager):
        self.conn_manager = conn_manager

    def load(
        self,
        symbol: Symbol,
        start_at: int = None,
        end_at: int = None,
        limit: int = None
    ) -> pd.DataFrame:
        # DB에서 캔들 데이터 로드 후 DataFrame 반환
        with self.conn_manager.get_connection() as conn:
            df = CandleRepository.query_to_dataframe(
                conn=conn,
                symbol=symbol,
                symbol_id=symbol.id,
                start_ts=start_at,
                end_ts=end_at
            )

            # limit 적용
            if limit is not None and not df.empty:
                df = df.head(limit)

            return df
