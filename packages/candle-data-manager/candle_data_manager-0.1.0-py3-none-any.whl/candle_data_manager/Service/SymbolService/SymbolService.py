from sqlalchemy.orm import Session
from loguru import logger

from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Core.Models.SymbolRepository import SymbolRepository


class SymbolService:
    # Symbol 등록/조회 Service

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        logger.info("SymbolService 초기화 완료")

    def register_symbol(
        self,
        session: Session,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str,
        quote: str,
        timeframe: str,
        **optional
    ) -> Symbol:
        # Symbol 등록 (이미 있으면 기존 반환)

        # 대문자 변환 (timeframe 제외)
        archetype = archetype.upper()
        exchange = exchange.upper()
        tradetype = tradetype.upper()
        base = base.upper()
        quote = quote.upper()

        logger.debug(
            f"Symbol 등록: {archetype}-{exchange}-{tradetype}-{base}-{quote}-{timeframe}"
        )

        symbol, created = SymbolRepository.get_or_create(
            session,
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe,
            **optional
        )

        if created:
            logger.info(f"새로운 Symbol 생성: {symbol.to_string()}")
        else:
            logger.debug(f"기존 Symbol 반환: {symbol.to_string()}")

        return symbol

    def find_symbols(
        self,
        session: Session,
        archetype: str = None,
        exchange: str = None,
        tradetype: str = None,
        base: str = None,
        quote: str = None,
        timeframe: str = None
    ) -> list[Symbol]:
        # 조건으로 Symbol 검색

        # 대문자 변환 (None이 아닌 경우, timeframe 제외)
        if archetype is not None:
            archetype = archetype.upper()
        if exchange is not None:
            exchange = exchange.upper()
        if tradetype is not None:
            tradetype = tradetype.upper()
        if base is not None:
            base = base.upper()
        if quote is not None:
            quote = quote.upper()

        logger.debug(
            f"Symbol 검색: archetype={archetype}, exchange={exchange}, "
            f"tradetype={tradetype}, base={base}, quote={quote}, timeframe={timeframe}"
        )

        # 쿼리 빌드
        query = session.query(Symbol)

        if archetype is not None:
            query = query.filter_by(archetype=archetype)
        if exchange is not None:
            query = query.filter_by(exchange=exchange)
        if tradetype is not None:
            query = query.filter_by(tradetype=tradetype)
        if base is not None:
            query = query.filter_by(base=base)
        if quote is not None:
            query = query.filter_by(quote=quote)
        if timeframe is not None:
            query = query.filter_by(timeframe=timeframe)

        symbols = query.all()

        logger.info(f"Symbol 검색 결과: {len(symbols)}개")

        return symbols

    def get_by_string(self, session: Session, symbol_str: str) -> Symbol | None:
        # 문자열로 Symbol 조회 (세션 필요)

        logger.debug(f"문자열로 Symbol 조회: {symbol_str}")

        # Symbol.from_string으로 파싱 (ValueError 발생 가능)
        try:
            parsed = Symbol.from_string(symbol_str)
        except ValueError as e:
            logger.error(f"Symbol 문자열 파싱 실패: {e}")
            raise

        # DB에서 조회
        symbol = SymbolRepository.get_by_components(
            session,
            archetype=parsed.archetype,
            exchange=parsed.exchange,
            tradetype=parsed.tradetype,
            base=parsed.base,
            quote=parsed.quote,
            timeframe=parsed.timeframe
        )

        if symbol:
            logger.info(f"Symbol 조회 성공: {symbol.to_string()}")
        else:
            logger.warning(f"Symbol 조회 실패 (존재하지 않음): {symbol_str}")

        return symbol

    def find_symbols_immediate(
        self,
        archetype: str = None,
        exchange: str = None,
        tradetype: str = None,
        base: str = None,
        quote: str = None,
        timeframe: str = None
    ) -> list[Symbol]:
        # Symbol 검색 (세션 내부 관리)

        with self.connection_manager.session_scope() as session:
            symbols = self.find_symbols(
                session,
                archetype=archetype,
                exchange=exchange,
                tradetype=tradetype,
                base=base,
                quote=quote,
                timeframe=timeframe
            )
            # expunge로 세션에서 분리
            for symbol in symbols:
                session.expunge(symbol)
            return symbols

    def get_symbol(self, symbol_str: str) -> Symbol | None:
        # 문자열로 Symbol 조회 (세션 불필요 - 내부에서 관리)

        with self.connection_manager.session_scope() as session:
            symbol = self.get_by_string(session, symbol_str)
            if symbol:
                session.expunge(symbol)
            return symbol

    def register_symbol_immediate(
        self,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str,
        quote: str,
        timeframe: str,
        **optional
    ) -> Symbol:
        # Symbol 등록 (즉시 커밋, 세션 내부 관리)

        with self.connection_manager.session_scope() as session:
            symbol = self.register_symbol(
                session,
                archetype=archetype,
                exchange=exchange,
                tradetype=tradetype,
                base=base,
                quote=quote,
                timeframe=timeframe,
                **optional
            )
            session.expunge(symbol)
            return symbol
