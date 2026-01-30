from loguru import logger
from candle_data_manager.Core.Models.CandleRepository import CandleRepository
from candle_data_manager.Core.Models.SymbolRepository import SymbolRepository


# Note: 가격 변환(float → int64)은 NormalizationService에서 수행됨
# DataSaveService는 이미 변환된 데이터를 받아 저장만 담당


class DataSaveService:
    def __init__(self, conn_manager):
        self.conn_manager = conn_manager

    def save(self, symbol, data: list[dict]) -> None:
        # 단일 Symbol 데이터 저장 (NormalizationService에서 이미 int 변환됨)
        if not data:
            return

        # symbol_id 추가 (통합 테이블인 경우)
        if symbol.is_unified():
            for row in data:
                row["symbol_id"] = symbol.id

        # DB 저장
        with self.conn_manager.get_connection() as conn:
            CandleRepository.upsert(conn, symbol, data)

        # last_timestamp 업데이트
        last_ts = max(row["timestamp"] for row in data)
        with self.conn_manager.session_scope() as session:
            SymbolRepository.update_last_timestamp(session, symbol.id, last_ts)

    def bulk_save(self, buffer: dict) -> None:
        # 여러 Symbol 데이터를 테이블별로 재그룹화하여 bulk insert
        # (NormalizationService에서 이미 int 변환됨)
        if not buffer:
            return

        # 1단계: 테이블별로 재그룹화
        table_groups = self._regroup_by_table(buffer)

        # 2단계: 테이블별 bulk insert
        with self.conn_manager.get_connection() as conn:
            for table_name, symbols_data in table_groups.items():
                # 대표 Symbol 선택 (같은 테이블의 아무 Symbol)
                representative_symbol = symbols_data[0][0]

                # 모든 데이터 통합
                all_data = []
                for symbol, data in symbols_data:
                    # 통합 테이블: symbol_id 추가
                    if symbol.is_unified():
                        for row in data:
                            row["symbol_id"] = symbol.id

                    all_data.extend(data)

                # 한번에 bulk insert
                if all_data:
                    logger.debug(f"Bulk inserting {len(all_data)} rows to {table_name}")
                    CandleRepository.upsert(conn, representative_symbol, all_data)

        # 3단계: last_timestamp 업데이트 (각 Symbol마다)
        with self.conn_manager.session_scope() as session:
            for symbol, data in buffer.items():
                if data:
                    last_ts = max(row["timestamp"] for row in data)
                    SymbolRepository.update_last_timestamp(session, symbol.id, last_ts)

    def _regroup_by_table(self, buffer: dict) -> dict:
        # Symbol별 버퍼를 테이블별로 재그룹화
        table_groups = {}

        for symbol, data in buffer.items():
            if not data:
                continue

            table_name = symbol.get_table_name()

            if table_name not in table_groups:
                table_groups[table_name] = []

            table_groups[table_name].append((symbol, data))

        return table_groups
