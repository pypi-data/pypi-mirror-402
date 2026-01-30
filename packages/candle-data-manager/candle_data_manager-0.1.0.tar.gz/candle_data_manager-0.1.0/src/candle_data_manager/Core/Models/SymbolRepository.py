from sqlalchemy.orm import Session
from .Symbol import Symbol


class SymbolRepository:
    """Symbol 테이블 CRUD (static methods)"""

    @staticmethod
    def get_by_id(session: Session, symbol_id: int) -> Symbol | None:
        # ID로 Symbol 조회
        return session.get(Symbol, symbol_id)

    @staticmethod
    def get_by_components(
        session: Session,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str,
        quote: str,
        timeframe: str
    ) -> Symbol | None:
        """컴포넌트로 Symbol 조회"""
        return session.query(Symbol).filter_by(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe
        ).first()

    @staticmethod
    def get_or_create(
        session: Session,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str,
        quote: str,
        timeframe: str,
        **optional
    ) -> tuple[Symbol, bool]:
        """Symbol 조회 또는 생성

        Args:
            session: SQLAlchemy Session
            archetype: CRYPTO, STOCK 등
            exchange: BINANCE, KRX 등
            tradetype: SPOT, FUTURES
            base: BTC, 005930 등
            quote: USDT, KRW 등
            timeframe: 1h, 1d, 1m 등
            **optional: full_name, listed_at 등 옵션 필드

        Returns:
            (Symbol, created): Symbol 객체와 생성 여부
        """
        # 기존 Symbol 조회
        existing = SymbolRepository.get_by_components(
            session, archetype, exchange, tradetype, base, quote, timeframe
        )

        if existing:
            return existing, False

        # 새로 생성
        new_symbol = Symbol(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe,
            **optional
        )
        session.add(new_symbol)
        session.flush()  # ID 생성

        return new_symbol, True

    @staticmethod
    def list_all(session: Session) -> list[Symbol]:
        """모든 Symbol 조회"""
        return session.query(Symbol).all()

    @staticmethod
    def list_by_exchange(
        session: Session,
        exchange: str,
        tradetype: str = None
    ) -> list[Symbol]:
        """거래소별 Symbol 조회

        Args:
            session: SQLAlchemy Session
            exchange: 거래소명 (BINANCE, KRX 등)
            tradetype: 거래타입 (SPOT, FUTURES, 선택사항)

        Returns:
            Symbol 리스트
        """
        query = session.query(Symbol).filter_by(exchange=exchange)

        if tradetype is not None:
            query = query.filter_by(tradetype=tradetype)

        return query.all()

    @staticmethod
    def update_last_timestamp(session: Session, symbol_id: int, timestamp: int) -> None:
        # 마지막 타임스탬프 업데이트
        symbol = session.get(Symbol, symbol_id)

        if symbol is None:
            raise ValueError(f"Symbol with id {symbol_id} not found")

        symbol.last_timestamp = timestamp
        session.flush()

    @staticmethod
    def delete(session: Session, symbol_id: int) -> None:
        # Symbol 삭제
        symbol = session.get(Symbol, symbol_id)

        if symbol is None:
            raise ValueError(f"Symbol with id {symbol_id} not found")

        session.delete(symbol)
        session.flush()
