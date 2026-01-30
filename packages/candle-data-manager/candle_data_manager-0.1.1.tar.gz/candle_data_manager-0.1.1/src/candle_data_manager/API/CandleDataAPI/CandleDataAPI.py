import time
from loguru import logger

from ...Core.ConnectionManager.ConnectionManager import ConnectionManager
from ...Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from ...Core.Initializer.Initializer import Initializer
from ...Service.SymbolService.SymbolService import SymbolService
from ...Service.DataFetchService.DataFetchService import DataFetchService
from ...Service.DataSaveService.DataSaveService import DataSaveService
from ...Service.DataLoadService.DataLoadService import DataLoadService
from ...Service.SymbolMetadata.SymbolMetadata import SymbolMetadata
from ...Service.MarketFactoryService.MarketFactoryService import MarketFactoryService
from ...Plugin.SymbolPreparationPlugin.SymbolPreparationPlugin import SymbolPreparationPlugin
from ...Plugin.UpdateOrchestrationPlugin.UpdateOrchestrationPlugin import UpdateOrchestrationPlugin
from ...Plugin.DataRetrievalPlugin.DataRetrievalPlugin import DataRetrievalPlugin
from ...Particles.UpdateResult import UpdateResult
from ...Particles.Market import Market
from ...Core.Models.Symbol import Symbol


class CandleDataAPI:
    def __init__(self, database_url: str = None):
        # DB 초기화
        if database_url is None:
            database_url = "mysql+pymysql://root@localhost/candle_data_manager"

        initializer = Initializer(database_url)
        initializer.initialize()

        # Core
        self._connection_manager = ConnectionManager(database_url)
        provider_registry = ProviderRegistry(self._connection_manager)

        # Service
        self._symbol_service = SymbolService(self._connection_manager)
        fetch_service = DataFetchService(provider_registry)
        save_service = DataSaveService(self._connection_manager)
        load_service = DataLoadService(self._connection_manager)
        symbol_metadata = SymbolMetadata(self._connection_manager)
        self._market_factory = MarketFactoryService()

        # Plugin
        symbol_prep_plugin = SymbolPreparationPlugin(self._symbol_service, symbol_metadata)
        self._update_plugin = UpdateOrchestrationPlugin(
            symbol_service=self._symbol_service,
            data_fetch_service=fetch_service,
            data_save_service=save_service,
            symbol_metadata=symbol_metadata,
            symbol_prep_plugin=symbol_prep_plugin
        )
        self._retrieval_plugin = DataRetrievalPlugin(load_service, fetch_service, save_service)

        logger.info("CandleDataAPI 초기화 완료")

    def active_update(
        self,
        archetype: str = None,
        exchange: str = None,
        tradetype: str = None,
        base: str | list[str] = None,
        quote: str | list[str] = None,
        timeframe: str | list[str] = None
    ) -> UpdateResult:
        # UpdateOrchestrationPlugin.active_update() 호출
        return self._update_plugin.active_update(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe
        )

    def passive_update(
        self,
        archetype: str = None,
        exchange: str = None,
        tradetype: str = None,
        base: str = None,
        quote: str = None,
        timeframe: str = None,
        buffer_size: int = None
    ) -> UpdateResult:
        # UpdateOrchestrationPlugin.passive_update() 호출
        return self._update_plugin.passive_update(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe,
            buffer_size=buffer_size
        )

    def load(
        self,
        archetype: str = None,
        exchange: str = None,
        tradetype: str = None,
        base: str = None,
        quote: str = None,
        timeframe: str = None,
        start_at: int = None,
        end_at: int = None,
        limit: int = None
    ) -> list[Market]:
        # 1. SymbolService.find_symbols_immediate()로 조건에 맞는 Symbol 검색
        symbols = self._symbol_service.find_symbols_immediate(
            archetype=archetype,
            exchange=exchange,
            tradetype=tradetype,
            base=base,
            quote=quote,
            timeframe=timeframe
        )

        # start_at, end_at 기본값 설정
        actual_start_at = start_at if start_at is not None else 0
        actual_end_at = end_at if end_at is not None else int(time.time())

        # 2. 각 Symbol에 대해 DataRetrievalPlugin.load_with_auto_fetch() 호출
        markets = []
        for symbol in symbols:
            # DataRetrievalPlugin으로 데이터 로드 (자동 획득 포함)
            df = self._retrieval_plugin.load_with_auto_fetch(
                symbol=symbol,
                start_at=actual_start_at,
                end_at=actual_end_at
            )

            # 3. MarketFactoryService.create_market()로 Market 생성
            market = self._market_factory.create_market(
                symbol=symbol,
                candles=df
            )

            markets.append(market)

        return markets

    def get_symbol(self, symbol_str: str) -> Symbol | None:
        # SymbolService.get_symbol() 호출 (내부에서 세션 관리)
        return self._symbol_service.get_symbol(symbol_str)

    def close(self) -> None:
        # 연결 종료
        self._connection_manager.close()
        logger.info("CandleDataAPI 종료")
