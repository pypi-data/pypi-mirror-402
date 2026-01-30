import time
from loguru import logger

from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Service.DataSaveService.DataSaveService import DataSaveService
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata
from candle_data_manager.Plugin.SymbolPreparationPlugin.SymbolPreparationPlugin import SymbolPreparationPlugin
from candle_data_manager.Particles.UpdateResult import UpdateResult


class UpdateOrchestrationPlugin:
    # Active/Passive Update 조율 Plugin

    def __init__(
        self,
        symbol_service: SymbolService,
        data_fetch_service: DataFetchService,
        data_save_service: DataSaveService,
        symbol_metadata: SymbolMetadata,
        symbol_prep_plugin: SymbolPreparationPlugin,
        buffer_size: int = 50000
    ):
        self.symbol_service = symbol_service
        self.data_fetch_service = data_fetch_service
        self.data_save_service = data_save_service
        self.symbol_metadata = symbol_metadata
        self.symbol_prep_plugin = symbol_prep_plugin
        self.buffer_size = buffer_size
        logger.info(f"UpdateOrchestrationPlugin 초기화 완료 (buffer_size={buffer_size})")

    def active_update(
        self,
        archetype: str,
        exchange: str,
        tradetype: str,
        base: str | list[str] = None,
        quote: str | list[str] = None,
        timeframe: str | list[str] = None
    ) -> UpdateResult:
        # 마켓 리스트 획득 → Symbol 등록 → 전체 데이터 수집

        logger.info(f"Active Update 시작: {archetype}-{exchange}-{tradetype}" + (f" (base={base})" if base else "") + (f" (quote={quote})" if quote else "") + (f" (timeframe={timeframe})" if timeframe else ""))

        # 메모리 버퍼 초기화
        buffer = {}
        buffer_row_count = 0
        success_symbols = []
        failed_symbols = []
        total_rows = 0

        try:
            # 1. 마켓 리스트 획득
            market_list = self.data_fetch_service.get_market_list(archetype, exchange, tradetype)
            logger.info(f"마켓 리스트 조회 완료: {len(market_list)}개 마켓")

            # 1-1. base 필터링 (지정된 경우)
            if base is not None:
                base_list = [base.upper()] if isinstance(base, str) else [b.upper() for b in base]
                market_list = [m for m in market_list if m.get("base", "").upper() in base_list]
                logger.info(f"base={base} 필터링 후: {len(market_list)}개 마켓")

            # 1-2. quote 필터링 (지정된 경우)
            if quote is not None:
                quote_list = [quote.upper()] if isinstance(quote, str) else [q.upper() for q in quote]
                market_list = [m for m in market_list if m.get("quote", "").upper() in quote_list]
                logger.info(f"quote={quote} 필터링 후: {len(market_list)}개 마켓")

            # 1-3. timeframe 결정
            supported_timeframes = self.data_fetch_service.get_supported_timeframes(archetype, exchange, tradetype)

            if timeframe is None:
                # 미지정시 전체 지원 타임프레임
                target_timeframes = supported_timeframes
            else:
                # 지정시 지원 타임프레임과 교집합
                requested = [timeframe] if isinstance(timeframe, str) else timeframe
                target_timeframes = [tf for tf in requested if tf in supported_timeframes]

            logger.info(f"대상 타임프레임: {target_timeframes}")

            if not target_timeframes:
                logger.warning("대상 타임프레임이 없습니다")
                return UpdateResult(success_symbols=[], failed_symbols=[], total_rows=0)

            # 2. 각 마켓의 각 timeframe에 대해 처리
            total_symbols = len(market_list) * len(target_timeframes)
            processed = 0

            for market_info in market_list:
                base = market_info["base"]
                market_quote = market_info["quote"]
                full_name = market_info.get("full_name")
                listed_at = market_info.get("listed_at")

                for tf in target_timeframes:
                    processed += 1
                    logger.debug(f"처리 중 ({processed}/{total_symbols}): {base}-{market_quote}-{tf}")

                    try:
                        # 2-1. Symbol 등록 및 테이블 준비 (즉시 커밋)
                        symbol = self.symbol_prep_plugin.register_and_prepare(
                            archetype=archetype,
                            exchange=exchange,
                            tradetype=tradetype,
                            base=base,
                            quote=market_quote,
                            timeframe=tf,
                            full_name=full_name,
                            listed_at=listed_at
                        )

                        # 2-2. 전체 데이터 fetch
                        data = self.data_fetch_service.fetch_all_data(symbol)
                        logger.debug(f"데이터 조회 완료: {symbol.to_string()} - {len(data)} rows")

                        # 2-3. 버퍼에 축적
                        if data:
                            buffer[symbol] = data
                            buffer_row_count += len(data)
                            total_rows += len(data)

                        success_symbols.append(symbol)

                        # 2-4. 버퍼 오버플로우 체크
                        if buffer_row_count >= self.buffer_size:
                            logger.info(f"버퍼 오버플로우 ({buffer_row_count} rows) - bulk_save 실행")
                            self.data_save_service.bulk_save(buffer)
                            buffer.clear()
                            buffer_row_count = 0
                            logger.debug(f"버퍼 초기화 완료 (buffer size: {len(buffer)}, row_count: {buffer_row_count})")

                    except Exception as e:
                        # 개별 Symbol 실패 시 계속 진행
                        error_msg = str(e)
                        logger.error(f"Symbol 처리 실패: {base}-{market_quote}-{tf} - {error_msg}")
                        failed_symbols.append((
                            Symbol(archetype=archetype, exchange=exchange, tradetype=tradetype,
                                  base=base, quote=market_quote, timeframe=tf),
                            error_msg
                        ))

            # 3. 남은 버퍼 flush
            if buffer:
                logger.info(f"마지막 버퍼 flush ({buffer_row_count} rows)")
                self.data_save_service.bulk_save(buffer)

            logger.info(f"Active Update 완료: 성공 {len(success_symbols)}, 실패 {len(failed_symbols)}, 총 {total_rows} rows")

            return UpdateResult(
                success_symbols=success_symbols,
                failed_symbols=failed_symbols,
                total_rows=total_rows
            )

        except Exception as e:
            logger.error(f"Active Update 실패: {str(e)}")
            raise

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
        # 기존 Symbol의 증분 업데이트

        logger.info(f"Passive Update 시작: archetype={archetype}, exchange={exchange}, tradetype={tradetype}")

        # 버퍼 크기 설정
        if buffer_size is None:
            buffer_size = self.buffer_size

        # 메모리 버퍼 초기화
        buffer = {}
        buffer_row_count = 0
        success_symbols = []
        failed_symbols = []
        total_rows = 0

        try:
            # 1. 조건으로 Symbol 검색 (None이 아닌 파라미터만 전달)
            kwargs = {}
            if archetype is not None:
                kwargs['archetype'] = archetype
            if exchange is not None:
                kwargs['exchange'] = exchange
            if tradetype is not None:
                kwargs['tradetype'] = tradetype
            if base is not None:
                kwargs['base'] = base
            if quote is not None:
                kwargs['quote'] = quote
            if timeframe is not None:
                kwargs['timeframe'] = timeframe

            symbols = self.symbol_service.find_symbols_immediate(**kwargs)
            logger.info(f"조건에 맞는 Symbol 개수: {len(symbols)}")

            # 2. 각 Symbol에 대해 증분 업데이트
            for idx, symbol in enumerate(symbols, 1):
                logger.debug(f"처리 중 ({idx}/{len(symbols)}): {symbol.to_string()}")

                try:
                    # 2-1. 테이블 상태 조회 (last_timestamp)
                    status = self.symbol_metadata.get_table_status(
                        symbol,
                        symbol_id=symbol.id if symbol.is_unified() else None
                    )
                    last_timestamp = status.get("last_timestamp")

                    # 2-2. last_timestamp 이후의 데이터 fetch
                    if last_timestamp is not None:
                        start_at = last_timestamp + 1
                    else:
                        # 데이터가 없으면 전체 fetch
                        start_at = 0

                    end_at = int(time.time())
                    data = self.data_fetch_service.fetch(symbol, start_at, end_at)
                    logger.debug(f"데이터 조회 완료: {symbol.to_string()} - {len(data)} rows")

                    # 2-3. 버퍼에 축적
                    if data:
                        buffer[symbol] = data
                        buffer_row_count += len(data)
                        total_rows += len(data)

                    success_symbols.append(symbol)

                    # 2-4. 버퍼 오버플로우 체크
                    if buffer_row_count >= buffer_size:
                        logger.info(f"버퍼 오버플로우 ({buffer_row_count} rows) - bulk_save 실행")
                        self.data_save_service.bulk_save(buffer)
                        buffer.clear()
                        buffer_row_count = 0

                except Exception as e:
                    # 개별 Symbol 실패 시 계속 진행
                    error_msg = str(e)
                    logger.error(f"Symbol 처리 실패: {symbol.to_string()} - {error_msg}")
                    failed_symbols.append((symbol, error_msg))

            # 3. 남은 버퍼 flush
            if buffer:
                logger.info(f"마지막 버퍼 flush ({buffer_row_count} rows)")
                self.data_save_service.bulk_save(buffer)

            logger.info(f"Passive Update 완료: 성공 {len(success_symbols)}, 실패 {len(failed_symbols)}, 총 {total_rows} rows")

            return UpdateResult(
                success_symbols=success_symbols,
                failed_symbols=failed_symbols,
                total_rows=total_rows
            )

        except Exception as e:
            logger.error(f"Passive Update 실패: {str(e)}")
            raise
