from loguru import logger

from ...Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from ...Core.Models.Symbol import Symbol


class DataFetchService:
    def __init__(self, provider_registry: ProviderRegistry):
        self._provider_registry = provider_registry

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        # Symbol에 맞는 Provider 선택
        provider = self._provider_registry.get_provider(symbol)

        # Provider로부터 데이터 획득
        data = provider.fetch(symbol, start_at, end_at)

        return data

    def fetch_all_data(self, symbol: Symbol) -> list[dict]:
        # Symbol에 맞는 Provider 선택
        provider = self._provider_registry.get_provider(symbol)

        # Provider로부터 데이터 범위 조회
        oldest_ts, latest_ts = provider.get_data_range(symbol)

        # 범위가 없으면 빈 리스트 반환
        if oldest_ts is None or latest_ts is None:
            return []

        # 전체 범위 데이터 획득
        data = provider.fetch(symbol, oldest_ts, latest_ts)

        return data

    def get_market_list(self, archetype: str, exchange: str, tradetype: str) -> list[dict]:
        # Provider 선택
        provider = self._provider_registry.get_provider_by_key(archetype, exchange, tradetype)

        # 마켓 리스트 조회
        market_list = provider.get_market_list()

        return market_list

    def get_supported_timeframes(self, archetype: str, exchange: str, tradetype: str) -> list[str]:
        # Provider 선택
        provider = self._provider_registry.get_provider_by_key(archetype, exchange, tradetype)

        # 지원 타임프레임 조회
        return provider.get_supported_timeframes()
