# DataRetrievalPlugin
데이터 로드와 자동 획득을 조합한 Plugin. 데이터가 없을 경우 자동으로 획득 후 조회하여 반환한다.

## 책임 범위
- DataLoadService와 DataAcquisitionPlugin을 조합
- 데이터 존재 여부 확인 후 자동 획득 워크플로우 제공
- 사용자는 데이터 존재 여부를 신경 쓰지 않고 항상 데이터를 받을 수 있음

## 의존성
- DataLoadService (Service layer)
- DataAcquisitionPlugin (Plugin layer)

## 주요 메서드

### load_with_auto_fetch(symbol: Symbol, start_at: int, end_at: int) -> pd.DataFrame
데이터 로드를 시도하고, 없으면 자동으로 획득 후 다시 로드하여 반환

**동작 흐름:**
1. DataLoadService.load()로 데이터 조회
2. 결과가 None이거나 빈 DataFrame이면:
   - DataAcquisitionPlugin.acquire_and_save()로 데이터 획득 및 저장
   - 다시 DataLoadService.load()로 조회
3. DataFrame 반환

**예외:**
- 첫 번째 load 실패 시: 예외 전파 (acquire 미실행)
- acquire_and_save 실패 시: 예외 전파 (두 번째 load 미실행)

## 사용 예시

```python
from candle_data_manager.Plugin.DataRetrievalPlugin import DataRetrievalPlugin
from candle_data_manager.Service.DataLoadService import DataLoadService
from candle_data_manager.Plugin.DataAcquisitionPlugin import DataAcquisitionPlugin

# 의존성 주입
retrieval_plugin = DataRetrievalPlugin(
    load_service=data_load_service,
    acquisition_plugin=data_acquisition_plugin
)

# 데이터 조회 (없으면 자동 획득)
df = retrieval_plugin.load_with_auto_fetch(
    symbol=btc_symbol,
    start_at=1609459200,
    end_at=1609545600
)
```
