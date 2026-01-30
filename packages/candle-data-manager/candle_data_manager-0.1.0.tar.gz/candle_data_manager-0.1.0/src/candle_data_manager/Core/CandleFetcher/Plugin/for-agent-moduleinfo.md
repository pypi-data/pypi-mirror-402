# BinanceProvider

Binance API 호출 및 데이터 정규화.

_api_validation: ApiValidationService
_normalization: NormalizationService
_null_handling: NullHandlingService

__init__() -> None
    Service 인스턴스 생성

fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    raise NoApiKeyError, ServerNotRespondedError, InvalidDataError
    Binance에서 캔들 획득

# UpbitProvider

Upbit API 호출 및 데이터 정규화.

_api_validation: ApiValidationService
_normalization: NormalizationService
_null_handling: NullHandlingService

__init__() -> None
    Service 인스턴스 생성

fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    raise NoApiKeyError, ServerNotRespondedError, InvalidDataError
    Upbit에서 캔들 획득

# FdrProvider

FinanceDataReader를 통한 데이터 획득.

_normalization: NormalizationService
_null_handling: NullHandlingService

__init__() -> None
    Service 인스턴스 생성 (API 키 불필요)

fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    raise ServerNotRespondedError, InvalidDataError
    FDR에서 캔들 획득

---

**공통 특징:**
- 모든 Provider는 동일한 인터페이스 `fetch(symbol, start_at, end_at) -> list[dict]`
- Service 계층을 조합하여 각자의 워크플로우 구현
- 반환값은 정규화된 dict (CandleRepository.upsert() 호환)
