# DataAcquisitionPlugin

데이터 획득(Fetch)과 저장(Save)을 조합하는 Plugin.
DataFetchService로 데이터를 가져온 후 즉시 DataSaveService로 저장하는 단일 작업을 수행한다.

## DataAcquisitionPlugin

_fetch_service: DataFetchService    # 데이터 획득 Service
_save_service: DataSaveService      # 데이터 저장 Service

acquire_and_save(symbol: Symbol, start_at: int, end_at: int) -> None
    데이터 획득 후 즉시 저장
    - DataFetchService.fetch()로 데이터 획득
    - DataSaveService.save()로 저장
    - 예외 발생 시 상위로 전파

## 사용 예시

```python
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Service.DataSaveService.DataSaveService import DataSaveService
from candle_data_manager.Plugin.DataAcquisitionPlugin.DataAcquisitionPlugin import DataAcquisitionPlugin
from candle_data_manager.Core.Models.Symbol import Symbol

# ConnectionManager와 Services 초기화
conn_manager = ConnectionManager()
provider_registry = ProviderRegistry(conn_manager)
fetch_service = DataFetchService(provider_registry)
save_service = DataSaveService(conn_manager)

# DataAcquisitionPlugin 생성
acquisition_plugin = DataAcquisitionPlugin(fetch_service, save_service)

# Symbol 생성
symbol = Symbol(
    archetype="CRYPTO",
    exchange="BINANCE",
    tradetype="SPOT",
    base="BTC",
    quote="USDT",
    timeframe="1h"
)

# 데이터 획득 및 저장
start_ts = 1609459200  # 2021-01-01 00:00:00 UTC
end_ts = 1609545600    # 2021-01-02 00:00:00 UTC
acquisition_plugin.acquire_and_save(symbol, start_ts, end_ts)
```

## 설계 원칙

1. **Plugin은 여러 Service 조합**: DataFetchService + DataSaveService
2. **단일 책임**: 데이터 획득 후 즉시 저장만 담당
3. **예외 전파**: Service에서 발생한 예외를 상위로 전파
4. **CPSCP 패턴**: Plugin 계층에서 Service들을 조합하여 복합 작업 수행

## 의존성

Service:
- DataFetchService: fetch()
- DataSaveService: save()

Core:
- Models/Symbol: Symbol 정보

## 워크플로우

```
User → DataRetrievalPlugin
         ↓
       DataAcquisitionPlugin
         ↓
       1. DataFetchService.fetch(symbol, start_at, end_at)
         ↓
       2. DataSaveService.save(symbol, data)
```

## 사용되는 위치

- **DataRetrievalPlugin**: 데이터 로드 시 데이터가 없으면 자동 획득
- **UpdateOrchestrationPlugin**: Passive Update 중 개별 Symbol 데이터 획득

## 특징

1. **간단한 조합**: Fetch + Save의 단순한 흐름
2. **즉시 저장**: 버퍼링 없이 획득한 데이터를 즉시 저장
3. **재사용성**: 단일 Symbol 데이터 획득/저장이 필요한 모든 곳에서 사용
