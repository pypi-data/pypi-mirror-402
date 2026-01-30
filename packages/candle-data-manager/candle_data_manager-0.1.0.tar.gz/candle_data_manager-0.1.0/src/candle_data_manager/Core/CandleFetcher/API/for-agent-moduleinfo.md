# CandleFetcher

캔들 데이터 획득 모듈의 공개 API. Symbol 객체를 받아 적절한 Provider로 라우팅.

_providers: dict[str, object]  # Provider 인스턴스 캐시

__init__() -> None
    Provider 캐싱용 딕셔너리 초기화

fetch(symbol: Symbol, start_at: str | int, end_at: str | int) -> list[dict]
    raise ProviderNotImplementedError
    캔들 데이터 획득
