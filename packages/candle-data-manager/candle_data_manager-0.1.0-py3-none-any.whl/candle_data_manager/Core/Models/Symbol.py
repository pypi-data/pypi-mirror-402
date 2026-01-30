from typing import List
from sqlalchemy import String, BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Symbol(Base):
    __tablename__ = 'symbols'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archetype: Mapped[str] = mapped_column(String(10), nullable=False)  # CRYPTO, STOCK, FUTURES
    exchange: Mapped[str] = mapped_column(String(10), nullable=False)  # BINANCE, KRAKEN, KRX
    tradetype: Mapped[str] = mapped_column(String(10), nullable=False)  # SPOT, FUTURES
    base: Mapped[str] = mapped_column(String(10), nullable=False)  # BTC, ETH, 005930
    quote: Mapped[str] = mapped_column(String(10), nullable=False)  # USDT, KRW, USD
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)  # 1d, 4h, 1m
    full_name: Mapped[str] = mapped_column(String(100), nullable=True)
    listed_at: Mapped[int] = mapped_column(BigInteger, nullable=True)
    last_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=True)

    # Relationships
    adjust_histories: Mapped[List["AdjustHistory"]] = relationship(back_populates="symbol")
    adjust_migration_histories: Mapped[List["AdjustMigrationHistory"]] = relationship(back_populates="symbol")

    __table_args__ = (
        UniqueConstraint('archetype', 'exchange', 'tradetype', 'base', 'quote', 'timeframe', name='uq_symbol'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )

    def __hash__(self):
        return hash((self.archetype, self.exchange, self.tradetype, self.base, self.quote, self.timeframe))

    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return False
        return (
            self.archetype == other.archetype and
            self.exchange == other.exchange and
            self.tradetype == other.tradetype and
            self.base == other.base and
            self.quote == other.quote and
            self.timeframe == other.timeframe
        )

    def is_unified(self) -> bool:
        # 'm'으로 끝나지 않으면 통합 테이블
        return not self.timeframe.endswith('m')

    def get_table_name(self) -> str:
        # 테이블명 생성
        if self.is_unified():
            # 통합: archetype_exchange_tradetype_timeframe
            return f"{self.archetype}_{self.exchange}_{self.tradetype}_{self.timeframe}".lower()
        else:
            # 개별: archetype_exchange_tradetype_base_quote_timeframe
            return f"{self.archetype}_{self.exchange}_{self.tradetype}_{self.base}_{self.quote}_{self.timeframe}".lower()

    @classmethod
    def from_string(cls, symbol_str: str) -> "Symbol":
        """문자열을 Symbol 객체로 변환

        Args:
            symbol_str: "CRYPTO-BINANCE-SPOT-BTC-USDT-1h" 형식의 문자열

        Returns:
            Symbol 객체

        Raises:
            ValueError: 형식이 올바르지 않은 경우
        """
        parts = symbol_str.split('-')
        if len(parts) != 6:
            raise ValueError(f"Invalid symbol string format: {symbol_str}. Expected format: ARCHETYPE-EXCHANGE-TRADETYPE-BASE-QUOTE-TIMEFRAME")

        return cls(
            archetype=parts[0].upper(),
            exchange=parts[1].upper(),
            tradetype=parts[2].upper(),
            base=parts[3].upper(),
            quote=parts[4].upper(),
            timeframe=parts[5]
        )

    def to_string(self) -> str:
        """Symbol 객체를 문자열로 변환

        Returns:
            "CRYPTO-BINANCE-SPOT-BTC-USDT-1h" 형식의 문자열
        """
        return f"{self.archetype}-{self.exchange}-{self.tradetype}-{self.base}-{self.quote}-{self.timeframe}"

    def __str__(self) -> str:
        return self.to_string()
