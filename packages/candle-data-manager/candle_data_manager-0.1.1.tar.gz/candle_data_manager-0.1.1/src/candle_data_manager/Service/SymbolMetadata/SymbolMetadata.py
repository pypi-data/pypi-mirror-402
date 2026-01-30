from ...Core.ConnectionManager.ConnectionManager import ConnectionManager
from ...Core.Models.CandleRepository import CandleRepository


class SymbolMetadata:
    """Symbol의 메타데이터 관리 서비스 (테이블 상태, 데이터 통계)"""

    def __init__(self, conn_manager: ConnectionManager) -> None:
        self._conn_manager = conn_manager

    def prepare_table(self, symbol) -> None:
        # Symbol의 캔들 테이블 준비 (없으면 생성)
        with self._conn_manager.get_connection() as conn:
            if not CandleRepository.table_exists(conn, symbol):
                CandleRepository.get_or_create_table(conn, symbol)

    def get_table_status(self, symbol, symbol_id: int = None) -> dict:
        """Symbol의 테이블 상태 조회

        Args:
            symbol: Symbol 객체
            symbol_id: 통합 테이블의 경우 필수

        Returns:
            {
                "exists": bool,
                "has_data": bool,
                "count": int,
                "first_timestamp": int | None,
                "last_timestamp": int | None
            }
        """
        with self._conn_manager.get_connection() as conn:
            # 테이블 존재 여부 확인
            exists = CandleRepository.table_exists(conn, symbol)

            if not exists:
                return {
                    "exists": False,
                    "has_data": False,
                    "count": 0,
                    "first_timestamp": None,
                    "last_timestamp": None
                }

            # 데이터 존재 여부 및 통계
            has_data = CandleRepository.has_data(conn, symbol, symbol_id)
            count = CandleRepository.count(conn, symbol, symbol_id)
            first_ts = CandleRepository.get_first_timestamp(conn, symbol, symbol_id) if has_data else None
            last_ts = CandleRepository.get_last_timestamp(conn, symbol, symbol_id) if has_data else None

            return {
                "exists": True,
                "has_data": has_data,
                "count": count,
                "first_timestamp": first_ts,
                "last_timestamp": last_ts
            }
