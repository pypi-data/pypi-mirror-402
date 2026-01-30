from loguru import logger

from ...Service.DataFetchService.DataFetchService import DataFetchService
from ...Service.DataSaveService.DataSaveService import DataSaveService
from ...Core.Models.Symbol import Symbol


class DataAcquisitionPlugin:
    def __init__(self, fetch_service: DataFetchService, save_service: DataSaveService):
        self._fetch_service = fetch_service
        self._save_service = save_service

    def acquire_and_save(self, symbol: Symbol, start_at: int, end_at: int) -> None:
        # 1. DataFetchService.fetch()로 데이터 획득
        data = self._fetch_service.fetch(symbol, start_at, end_at)

        # 2. DataSaveService.save()로 저장
        self._save_service.save(symbol, data)
