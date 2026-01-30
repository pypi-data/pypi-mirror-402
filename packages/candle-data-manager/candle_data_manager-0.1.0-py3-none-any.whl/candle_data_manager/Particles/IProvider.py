from typing import Protocol
from ..Core.Models.Symbol import Symbol


class IProvider(Protocol):
    # Provider가 구현해야 할 인터페이스

    @property
    def archetype(self) -> str:
        # CRYPTO, STOCK 등
        ...

    @property
    def exchange(self) -> str:
        # BINANCE, UPBIT, KRX 등
        ...

    @property
    def tradetype(self) -> str:
        # SPOT, FUTURES
        ...

    def fetch(self, symbol: Symbol, start_at: int, end_at: int) -> list[dict]:
        # 캔들 데이터 조회
        # Args: symbol (Symbol 객체), start_at (시작 Unix timestamp 초), end_at (종료 Unix timestamp 초)
        # Returns: list[dict] - 캔들 데이터 리스트 [{'timestamp': int, 'open': int, 'high': int, 'low': int, 'close': int, 'volume': int}]
        ...

    def get_market_list(self) -> list[dict]:
        # 현재 거래 가능한 모든 마켓 정보
        # Returns: list[dict] - 마켓 정보 리스트 [{"base": str, "quote": str, "timeframes": list[str], "listed_at": int | None, "full_name": str | None}]
        ...

    def get_data_range(self, symbol: Symbol) -> tuple[int | None, int | None]:
        # 거래소가 제공하는 데이터 범위
        # Args: symbol (Symbol 객체)
        # Returns: tuple[int | None, int | None] - (oldest_timestamp, latest_timestamp) 제공 안 하면 (None, None)
        ...

    def get_supported_timeframes(self) -> list[str]:
        # Provider가 지원하는 타임프레임 목록
        # Returns: list[str] - 지원 타임프레임 리스트 ["1m", "5m", "1h", "1d", ...]
        ...
