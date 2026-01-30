from typing import Union
import pandas as pd
from sqlalchemy import Table, Column, Integer, BigInteger, Index, inspect, PrimaryKeyConstraint, select, func
from sqlalchemy.engine import Connection
from sqlalchemy.dialects.mysql import insert as mysql_insert

from . import Base


class CandleRepository:
    PRICE_SCALE = 100_000_000  # 10^8

    @staticmethod
    def to_storage(price: float) -> int:
        # float -> int64 (× 10^8)
        return int(round(price * CandleRepository.PRICE_SCALE))

    @staticmethod
    def from_storage(value: int) -> float:
        # int64 -> float (÷ 10^8)
        return value / CandleRepository.PRICE_SCALE

    @staticmethod
    def get_or_create_table(conn: Connection, symbol) -> Table:
        # Symbol 객체로부터 동적 테이블 생성
        from . import Base

        table_name = symbol.get_table_name()
        metadata = Base.metadata

        # 이미 metadata에 등록된 테이블이면 그대로 반환
        if table_name in metadata.tables:
            candle_table = metadata.tables[table_name]
            # DB에 테이블이 없으면 생성
            inspector = inspect(conn)
            if table_name not in inspector.get_table_names():
                candle_table.create(conn)
            return candle_table

        if symbol.is_unified():
            # 통합 테이블: symbol_id, timestamp, OHLCV
            candle_table = Table(
                table_name,
                metadata,
                Column('symbol_id', Integer, nullable=False),
                Column('timestamp', BigInteger, nullable=False),
                Column('high', BigInteger, nullable=False),
                Column('low', BigInteger, nullable=False),
                Column('open', BigInteger, nullable=False),
                Column('close', BigInteger, nullable=False),
                Column('volume', BigInteger, nullable=False),
                PrimaryKeyConstraint('symbol_id', 'timestamp'),
                extend_existing=True,
                mysql_engine='InnoDB',
                mysql_charset='utf8mb4',
            )
            Index(f'idx_{table_name}_symbol', candle_table.c.symbol_id)
            Index(f'idx_{table_name}_timestamp', candle_table.c.timestamp)
        else:
            # 개별 테이블: timestamp, OHLCV
            candle_table = Table(
                table_name,
                metadata,
                Column('timestamp', BigInteger, primary_key=True),
                Column('high', BigInteger, nullable=False),
                Column('low', BigInteger, nullable=False),
                Column('open', BigInteger, nullable=False),
                Column('close', BigInteger, nullable=False),
                Column('volume', BigInteger, nullable=False),
                extend_existing=True,
                mysql_engine='InnoDB',
                mysql_charset='utf8mb4',
            )
            Index(f'idx_{table_name}_timestamp', candle_table.c.timestamp)

        # DB에 테이블이 없으면 생성
        inspector = inspect(conn)
        if table_name not in inspector.get_table_names():
            candle_table.create(conn)

        return candle_table

    @staticmethod
    def upsert(conn: Connection, symbol, data: Union[dict, list[dict]]) -> None:
        # 단일/대량 UPSERT (MySQL only)
        if not data:
            return

        table = CandleRepository.get_or_create_table(conn, symbol)
        candles_data = data if isinstance(data, list) else [data]

        if conn.dialect.name != 'mysql':
            raise NotImplementedError("Only MySQL is supported")

        stmt = mysql_insert(table)
        update_dict = {
            'high': stmt.inserted.high,
            'low': stmt.inserted.low,
            'open': stmt.inserted.open,
            'close': stmt.inserted.close,
            'volume': stmt.inserted.volume
        }
        stmt = stmt.on_duplicate_key_update(**update_dict)
        conn.execute(stmt, candles_data)

    @staticmethod
    def query_to_dataframe(conn: Connection, symbol, symbol_id: int = None, start_ts: int = None, end_ts: int = None) -> pd.DataFrame:
        # pandas로 조회 후 가격 변환
        table = CandleRepository.get_or_create_table(conn, symbol)
        stmt = select(table)

        # 통합 테이블: symbol_id 필터 필요
        if symbol.is_unified():
            if symbol_id is None:
                raise ValueError("Unified table requires symbol_id parameter")
            stmt = stmt.where(table.c.symbol_id == symbol_id)

        if start_ts is not None:
            stmt = stmt.where(table.c.timestamp >= start_ts)
        if end_ts is not None:
            stmt = stmt.where(table.c.timestamp < end_ts)

        stmt = stmt.order_by(table.c.timestamp)

        # pandas.read_sql 사용
        df = pd.read_sql(stmt, conn)

        # 가격 컬럼 변환
        price_cols = ['high', 'low', 'open', 'close']
        df[price_cols] = df[price_cols] / CandleRepository.PRICE_SCALE

        return df

    @staticmethod
    def table_exists(conn: Connection, symbol) -> bool:
        """테이블 존재 여부 확인 (생성하지 않음)"""
        table_name = symbol.get_table_name()
        inspector = inspect(conn)
        return table_name in inspector.get_table_names()

    @staticmethod
    def get_last_timestamp(conn: Connection, symbol, symbol_id: int = None) -> int:
        """마지막 타임스탬프 조회"""
        # 통합 테이블: symbol_id 필수 (테이블 생성 전 체크)
        if symbol.is_unified() and symbol_id is None:
            raise ValueError("Unified table requires symbol_id parameter")

        table = CandleRepository.get_or_create_table(conn, symbol)

        if symbol.is_unified():
            stmt = select(func.max(table.c.timestamp)).where(table.c.symbol_id == symbol_id)
        else:
            stmt = select(func.max(table.c.timestamp))

        result = conn.execute(stmt)
        return result.scalar()

    @staticmethod
    def get_first_timestamp(conn: Connection, symbol, symbol_id: int = None) -> int:
        """첫 타임스탬프 조회"""
        # 통합 테이블: symbol_id 필수 (테이블 생성 전 체크)
        if symbol.is_unified() and symbol_id is None:
            raise ValueError("Unified table requires symbol_id parameter")

        table = CandleRepository.get_or_create_table(conn, symbol)

        if symbol.is_unified():
            stmt = select(func.min(table.c.timestamp)).where(table.c.symbol_id == symbol_id)
        else:
            stmt = select(func.min(table.c.timestamp))

        result = conn.execute(stmt)
        return result.scalar()

    @staticmethod
    def count(conn: Connection, symbol, symbol_id: int = None) -> int:
        """레코드 개수 조회"""
        # 통합 테이블: symbol_id 필수 (테이블 생성 전 체크)
        if symbol.is_unified() and symbol_id is None:
            raise ValueError("Unified table requires symbol_id parameter")

        table = CandleRepository.get_or_create_table(conn, symbol)

        if symbol.is_unified():
            stmt = select(func.count()).select_from(table).where(table.c.symbol_id == symbol_id)
        else:
            stmt = select(func.count()).select_from(table)

        result = conn.execute(stmt)
        return result.scalar()

    @staticmethod
    def has_data(conn: Connection, symbol, symbol_id: int = None) -> bool:
        """데이터 존재 여부 확인"""
        return CandleRepository.count(conn, symbol, symbol_id) > 0
