# Particles

인터페이스, 데이터 구조, 예외를 정의하는 최하위 레이어. 의존성 없음.

## IProvider

Provider가 구현해야 할 인터페이스를 정의하는 Protocol

### Properties
archetype: str - CRYPTO, STOCK 등
exchange: str - BINANCE, UPBIT, KRX 등
tradetype: str - SPOT, FUTURES

### Methods
fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    캔들 데이터 조회. start_at과 end_at는 Unix timestamp(초 단위).
    반환값: [{'timestamp': int, 'open': int, 'high': int, 'low': int, 'close': int, 'volume': int}]
    가격과 거래량은 모두 정수 (× 10^8)

get_market_list() -> list[dict]
    현재 거래 가능한 모든 마켓 정보 조회.
    반환값: [{"base": str, "quote": str, "timeframes": list[str], "listed_at": int | None, "full_name": str | None}]

get_data_range(symbol: Symbol) -> tuple[int | None, int | None]
    거래소가 제공하는 데이터 범위(oldest, latest timestamp).
    제공하지 않으면 (None, None) 반환.

### 용도
- 모든 Provider 구현체(BinanceSpotProvider, UpbitProvider 등)가 따라야 할 인터페이스
- ProviderRegistry가 반환하는 타입
- DataFetchService가 사용하는 추상 타입

## Market

Symbol과 캔들 데이터를 래핑하는 데이터 클래스

### Attributes
symbol: Symbol - Symbol 객체
candles: pd.DataFrame - 캔들 데이터

### 용도
- Symbol과 DataFrame을 하나의 객체로 묶어 반환
- API의 load() 메서드가 반환하는 타입
- MarketFactoryService가 생성

## UpdateResult

Active/Passive Update 작업 결과를 담는 불변 데이터 클래스

### Attributes
success_symbols: list[Symbol] - 성공한 Symbol 리스트
failed_symbols: list[tuple[Symbol, str]] - 실패한 Symbol과 이유 리스트
total_rows: int - 총 저장된 row 수

### 특징
- frozen=True로 불변 객체
- 부분 성공 허용 (일부 Symbol 실패해도 나머지는 진행)

### 용도
- UpdateOrchestrationPlugin의 active_update(), passive_update() 반환 타입
- 성공/실패 Symbol 추적 및 보고

## Exceptions

Provider 및 데이터 처리 관련 예외들.

### ProviderNotImplementedError
구현되지 않은 Provider 호출 시 발생.
exchange: str - 거래소명

### NoApiKeyError
API 키가 환경변수에 없을 때 발생.
exchange: str - 거래소명

### ServerNotRespondedError
서버 응답 없을 때 발생.
exchange: str - 거래소명

### InvalidDataError
잘못된 데이터 형식일 때 발생.
reason: str - 에러 사유
