from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class AdjustMigrationHistory(Base):
    __tablename__ = 'adjust_migration_history'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol_id: Mapped[int] = mapped_column(ForeignKey('symbols.id'), nullable=False)
    migration_type: Mapped[str] = mapped_column(String(50), nullable=False)
    executed_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationship
    symbol: Mapped["Symbol"] = relationship(back_populates="adjust_migration_histories")

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
