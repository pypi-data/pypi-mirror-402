# Models

데이터베이스 모델 정의.
ORM 모델(Symbol, AdjustHistory, AdjustMigrationHistory)과 동적 테이블 관리(CandleRepository).

## Symbol
심볼 정보 ORM 모델.

archetype: str  # CRYPTO, STOCK (자동 대문자 변환)
exchange: str  # BINANCE, KRAKEN (자동 대문자 변환)
tradetype: str  # SPOT, FUTURES (자동 대문자 변환)
base: str  # BTC, ETH (자동 대문자 변환)
quote: str  # USDT, KRW (자동 대문자 변환)
timeframe: str  # 1d, 4h, 1m
full_name: str = None
listed_at: int = None
last_timestamp: int = None

from_string(symbol_str: str) -> Symbol  # classmethod
    raise ValueError  # 형식이 잘못된 경우
    문자열을 Symbol 객체로 변환
    형식: "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"

to_string() -> str
    Symbol 객체를 문자열로 변환
    형식: "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"

is_unified() -> bool
    timeframe이 'm'으로 끝나지 않으면 True

get_table_name() -> str
    캔들 테이블명 생성 (소문자)

## AdjustHistory
가격 조정 이력 ORM 모델.

symbol_id: int  # FK(symbols.id)
timestamp: int
old_price_multiplier: float
reason: str = None
created_at: int

## AdjustMigrationHistory
조정 마이그레이션 이력 ORM 모델.

symbol_id: int  # FK(symbols.id)
migration_type: str
executed_at: int
status: str  # pending, running, completed, failed

## SymbolRepository
Symbol 테이블 CRUD (static 메서드).

get_by_id(session, symbol_id: int) -> Symbol | None
    ID로 Symbol 조회

get_by_components(session, archetype, exchange, tradetype, base, quote, timeframe) -> Symbol | None
    컴포넌트로 Symbol 조회

get_or_create(session, archetype, exchange, tradetype, base, quote, timeframe, **optional) -> tuple[Symbol, bool]
    Symbol 조회 또는 생성
    반환: (Symbol, created)

list_all(session) -> list[Symbol]
    모든 Symbol 조회

list_by_exchange(session, exchange: str, tradetype: str = None) -> list[Symbol]
    거래소별 Symbol 조회

update_last_timestamp(session, symbol_id: int, timestamp: int) -> None
    raise ValueError  # Symbol이 존재하지 않는 경우
    마지막 타임스탬프 업데이트

delete(session, symbol_id: int) -> None
    raise ValueError  # Symbol이 존재하지 않는 경우
    Symbol 삭제

## CandleRepository
동적 캔들 테이블 관리 (static 메서드).

PRICE_SCALE = 100_000_000

to_storage(price: float) -> int
    float → int64 (× 10^8)

from_storage(value: int) -> float
    int64 → float (÷ 10^8)

table_exists(conn, symbol) -> bool
    테이블 존재 여부 확인 (생성하지 않음)

get_last_timestamp(conn, symbol, symbol_id=None) -> int | None
    raise ValueError  # 통합 테이블에서 symbol_id 없을 시
    마지막 타임스탬프 조회

get_first_timestamp(conn, symbol, symbol_id=None) -> int | None
    raise ValueError  # 통합 테이블에서 symbol_id 없을 시
    첫 타임스탬프 조회

count(conn, symbol, symbol_id=None) -> int
    raise ValueError  # 통합 테이블에서 symbol_id 없을 시
    레코드 개수 조회

has_data(conn, symbol, symbol_id=None) -> bool
    데이터 존재 여부 확인

upsert(conn, symbol, data: dict | list[dict]) -> None
    MySQL, PostgreSQL, SQLite 자동 분기

query_to_dataframe(conn, symbol, symbol_id=None, start_ts=None, end_ts=None) -> pd.DataFrame
    가격 자동 변환
