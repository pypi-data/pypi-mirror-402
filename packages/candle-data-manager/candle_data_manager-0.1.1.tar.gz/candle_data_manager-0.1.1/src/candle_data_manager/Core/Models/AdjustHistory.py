from sqlalchemy import String, BigInteger, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class AdjustHistory(Base):
    __tablename__ = 'adjust_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey('symbols.id'), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    old_price_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationship
    symbol: Mapped["Symbol"] = relationship(back_populates="adjust_histories")

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
