# CandleDataAPI

CandleDataManager 패키지의 단일 진입점(Controller). 사용자에게 간단한 인터페이스를 제공하며, Plugin 조합으로 최상위 워크플로우를 구성한다.

## 책임범위

- Active/Passive Update 워크플로우 조율
- 조건 기반 캔들 데이터 로드 (자동 획득 포함)
- Symbol 조회
- ConnectionManager를 통한 세션 관리

## 의존성

- ConnectionManager: DB 세션 관리
- UpdateOrchestrationPlugin: Active/Passive Update 수행
- DataRetrievalPlugin: 데이터 로드 및 자동 획득
- SymbolService: Symbol 검색 및 조회
- MarketFactoryService: Market 객체 생성

## 메서드

### __init__(connection_manager, update_plugin, retrieval_plugin, symbol_service, market_factory)
CandleDataAPI 초기화. 필요한 모든 Plugin과 Service를 주입받는다.

### active_update(archetype=None, exchange=None, tradetype=None) -> UpdateResult
신규 Symbol 등록 및 전체 데이터 수집.
- UpdateOrchestrationPlugin.active_update() 호출
- 마켓 리스트 획득 → Symbol 등록 → 전체 데이터 수집
- 성공/실패 Symbol 및 총 row 수 반환

### passive_update(archetype=None, exchange=None, tradetype=None, base=None, quote=None, timeframe=None, buffer_size=None) -> UpdateResult
기존 Symbol의 증분 업데이트.
- UpdateOrchestrationPlugin.passive_update() 호출
- 조건으로 Symbol 검색 → 마지막 timestamp 이후 데이터 수집
- 성공/실패 Symbol 및 총 row 수 반환

### load(archetype=None, exchange=None, tradetype=None, base=None, quote=None, timeframe=None, start_at=None, end_at=None, limit=None) -> list[Market]
조건 기반 캔들 데이터 로드 (자동 획득).
1. SymbolService.find_symbols()로 조건에 맞는 Symbol 검색
2. 각 Symbol에 대해 DataRetrievalPlugin.load_with_auto_fetch() 호출
3. MarketFactoryService.create_market()로 Market 객체 생성
4. Market 리스트 반환
- start_at 기본값: 0
- end_at 기본값: 현재 시간
- limit 파라미터는 현재 사용되지 않음

### get_symbol(symbol_str: str) -> Symbol | None
문자열로 Symbol 조회.
- SymbolService.get_by_string() 호출
- Symbol이 존재하지 않으면 None 반환

## Usage

```python
from candle_data_manager.API.CandleDataAPI.CandleDataAPI import CandleDataAPI
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
# ... 기타 의존성 import

# ConnectionManager 및 의존성 초기화
connection_manager = ConnectionManager()
# ... Plugin, Service 초기화

# CandleDataAPI 생성
api = CandleDataAPI(
    connection_manager=connection_manager,
    update_plugin=update_plugin,
    retrieval_plugin=retrieval_plugin,
    symbol_service=symbol_service,
    market_factory=market_factory
)

# Active Update (신규 Symbol 전체 수집)
result = api.active_update(
    archetype="CRYPTO",
    exchange="BINANCE",
    tradetype="SPOT"
)

# Passive Update (기존 Symbol 증분 갱신)
result = api.passive_update(
    archetype="CRYPTO",
    exchange="BINANCE"
)

# 데이터 로드 (자동 획득)
markets = api.load(
    archetype="CRYPTO",
    exchange="BINANCE",
    tradetype="SPOT",
    timeframe="1h",
    start_at=1609459200,
    end_at=1609545600
)

# Symbol 조회
symbol = api.get_symbol("CRYPTO-BINANCE-SPOT-BTC-USDT-1h")
```

## 특징

- **단일 진입점**: 모든 기능을 하나의 API로 제공
- **세션 관리**: ConnectionManager.session_scope()로 자동 세션 관리
- **자동 획득**: load() 시 데이터가 없으면 자동으로 fetch
- **부분 성공 허용**: Update 시 일부 실패해도 계속 진행
- **유연한 조건**: 모든 파라미터는 선택적으로 제공 가능
