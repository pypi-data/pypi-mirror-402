from loguru import logger

from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata


class SymbolPreparationPlugin:
    # Symbol 등록 + 테이블 준비 조합 Plugin

    def __init__(self, symbol_service: SymbolService, symbol_metadata: SymbolMetadata):
        self.symbol_service = symbol_service
        self.symbol_metadata = symbol_metadata
        logger.info("SymbolPreparationPlugin 초기화 완료")

    def register_and_prepare(
        self,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str,
        quote: str,
        timeframe: str,
        **optional
    ) -> Symbol:
        # Symbol 등록 및 테이블 준비 (즉시 커밋)

        logger.debug(
            f"Symbol 등록 및 준비: {archetype}-{exchange}-{tradetype}-{base}-{quote}-{timeframe}"
        )

        # 1. SymbolService로 Symbol 등록 (즉시 커밋)
        symbol = self.symbol_service.register_symbol_immediate(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe,
            **optional
        )

        # 2. SymbolMetadata로 테이블 준비
        self.symbol_metadata.prepare_table(symbol)

        logger.info(f"Symbol 등록 및 테이블 준비 완료: {symbol.to_string()}")

        # 3. Symbol 반환
        return symbol
