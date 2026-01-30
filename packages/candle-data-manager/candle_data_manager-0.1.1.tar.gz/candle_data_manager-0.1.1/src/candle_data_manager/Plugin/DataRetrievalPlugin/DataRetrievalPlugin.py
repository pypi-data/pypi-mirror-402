import pandas as pd
from loguru import logger

from ...Service.DataLoadService.DataLoadService import DataLoadService
from ...Service.DataFetchService.DataFetchService import DataFetchService
from ...Service.DataSaveService.DataSaveService import DataSaveService
from ...Core.Models.Symbol import Symbol


class DataRetrievalPlugin:
    def __init__(
        self,
        load_service: DataLoadService,
        fetch_service: DataFetchService,
        save_service: DataSaveService
    ):
        self._load_service = load_service
        self._fetch_service = fetch_service
        self._save_service = save_service

    def load_with_auto_fetch(
        self,
        symbol: Symbol,
        start_at: int,
        end_at: int
    ) -> pd.DataFrame:
        # 1. DataLoadService.load()로 데이터 조회
        df = self._load_service.load(symbol, start_at, end_at)

        # 2. 빈 결과면 최초 시작일부터 전체 데이터 획득 후 저장
        if df is None or df.empty:
            logger.info(f"DB에 데이터 없음, 전체 데이터 획득 시작: {symbol.to_string()}")

            # 전체 데이터 Fetch (최초 시작일 ~ 최신)
            data = self._fetch_service.fetch_all_data(symbol)

            if data:
                logger.info(f"획득된 캔들: {len(data)}개")
                # Save
                self._save_service.save(symbol, data)
                logger.info("저장 완료")

            # 3. 다시 DataLoadService.load()로 요청 범위 조회
            df = self._load_service.load(symbol, start_at, end_at)

        # 4. DataFrame 반환
        return df
