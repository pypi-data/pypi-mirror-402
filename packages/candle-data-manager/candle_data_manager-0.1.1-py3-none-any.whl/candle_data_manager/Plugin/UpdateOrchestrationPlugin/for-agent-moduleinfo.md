# UpdateOrchestrationPlugin

Active/Passive Update를 조율하는 Plugin. 여러 Symbol에 대한 업데이트를 반복 처리하며, 메모리 버퍼를 관리하여 대량 데이터 처리를 최적화한다.

## UpdateOrchestrationPlugin

__init__(symbol_service, data_fetch_service, data_save_service, symbol_metadata, symbol_prep_plugin, buffer_size=100000)
    의존성 주입 및 초기화
    - buffer_size: 메모리 버퍼 크기 (기본 100,000 rows)

active_update(session, archetype, exchange, tradetype) -> UpdateResult
    마켓 리스트 획득 → Symbol 등록 → 전체 데이터 수집
    - DataFetchService로 마켓 리스트 조회
    - 각 마켓의 각 timeframe에 대해:
      1. SymbolPreparationPlugin으로 Symbol 등록 및 테이블 준비
      2. DataFetchService로 전체 데이터 fetch
      3. 메모리 버퍼에 축적 (Symbol별 분리)
      4. 버퍼 오버플로우 시 bulk_save
    - 남은 버퍼 flush
    - 실패한 Symbol 수집 및 UpdateResult 반환

passive_update(session, archetype=None, exchange=None, tradetype=None, base=None, quote=None, timeframe=None, buffer_size=None) -> UpdateResult
    기존 Symbol의 증분 업데이트
    - SymbolService로 조건에 맞는 Symbol 검색
    - 각 Symbol에 대해:
      1. SymbolMetadata로 last_timestamp 조회
      2. DataFetchService로 증분 데이터 fetch (last_timestamp + 1 이후)
      3. 메모리 버퍼에 축적 (Symbol별 분리)
      4. 버퍼 오버플로우 시 bulk_save
    - 남은 버퍼 flush
    - 실패한 Symbol 수집 및 UpdateResult 반환

## 메모리 버퍼 관리

버퍼 구조:
```python
buffer: dict[Symbol, list[dict]] = {}
buffer_row_count: int = 0
```

버퍼 알고리즘:
1. Symbol별로 데이터 분리 저장 (추적 용이성)
2. 총 row 수가 buffer_size 도달 시 bulk_save 호출
3. DataSaveService가 테이블별로 재그룹화하여 insert
4. 버퍼 비우기
5. 반복문 종료 후 남은 버퍼 flush

오버플로우 예시:
- buffer_size = 10
- BTC 6개 추가 → buffer_row_count = 6
- ETH 5개 추가 → buffer_row_count = 11 > 10 → bulk_save 실행, 버퍼 비우기
- XRP 4개 추가 → buffer_row_count = 4
- 반복문 종료 → 남은 4개 flush

## 에러 처리

부분 성공 허용:
- 개별 Symbol 처리 중 에러 발생 시 해당 Symbol만 실패 처리
- 나머지 Symbol은 계속 진행
- UpdateResult에 success_symbols, failed_symbols 분리 저장
- failed_symbols에는 (Symbol, error_message) 튜플 저장

## 의존성

Plugin:
- SymbolPreparationPlugin: Symbol 등록 및 테이블 준비

Service:
- SymbolService: Symbol 검색
- DataFetchService: 데이터 획득
- DataSaveService: bulk insert
- SymbolMetadata: 테이블 상태 조회

Particles:
- UpdateResult: 업데이트 결과

## 사용 예시

```python
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Service.SymbolService.SymbolService import SymbolService
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Service.DataSaveService.DataSaveService import DataSaveService
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata
from candle_data_manager.Plugin.SymbolPreparationPlugin.SymbolPreparationPlugin import SymbolPreparationPlugin
from candle_data_manager.Plugin.UpdateOrchestrationPlugin.UpdateOrchestrationPlugin import UpdateOrchestrationPlugin

# 초기화
conn_mgr = ConnectionManager()
provider_registry = ProviderRegistry(conn_mgr)
symbol_service = SymbolService(conn_mgr)
data_fetch_service = DataFetchService(provider_registry)
data_save_service = DataSaveService(conn_mgr)
symbol_metadata = SymbolMetadata(conn_mgr)
symbol_prep_plugin = SymbolPreparationPlugin(symbol_service, symbol_metadata)

plugin = UpdateOrchestrationPlugin(
    symbol_service=symbol_service,
    data_fetch_service=data_fetch_service,
    data_save_service=data_save_service,
    symbol_metadata=symbol_metadata,
    symbol_prep_plugin=symbol_prep_plugin,
    buffer_size=100000
)

# Active Update - 신규 마켓 전체 수집
with conn_mgr.session_scope() as session:
    result = plugin.active_update(session, 'CRYPTO', 'BINANCE', 'SPOT')
    print(f"성공: {len(result.success_symbols)}")
    print(f"실패: {len(result.failed_symbols)}")
    print(f"총 rows: {result.total_rows}")

# Passive Update - 기존 Symbol 증분 업데이트
with conn_mgr.session_scope() as session:
    result = plugin.passive_update(
        session,
        archetype='CRYPTO',
        exchange='BINANCE'
    )
    print(f"성공: {len(result.success_symbols)}")
    print(f"실패: {len(result.failed_symbols)}")
    print(f"총 rows: {result.total_rows}")

# Passive Update - 전체 Symbol 업데이트 (조건 없음)
with conn_mgr.session_scope() as session:
    result = plugin.passive_update(session)
```

## 설계 원칙

1. **Plugin 역할**: 여러 Service를 조합하여 복합 작업 수행
2. **메모리 효율**: 버퍼 크기 제한으로 메모리 사용량 제어
3. **부분 성공 허용**: 일부 실패해도 전체 작업 계속 진행
4. **테이블별 최적화**: DataSaveService가 테이블별로 재그룹화하여 bulk insert 횟수 최소화
5. **명확한 결과 보고**: UpdateResult로 성공/실패 Symbol 분리 보고
