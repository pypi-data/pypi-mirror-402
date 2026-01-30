# DataLoadService

DB에서 캔들 데이터를 로드하여 DataFrame으로 반환하는 서비스. Symbol, 시간 범위, limit을 지정하여 조회 가능.

## 속성

conn_manager: ConnectionManager  # DB 연결 관리자

## 메서드

__init__(conn_manager: ConnectionManager)
    ConnectionManager를 주입받아 초기화

load(symbol: Symbol, start_at: int = None, end_at: int = None, limit: int = None) -> pd.DataFrame
    DB에서 캔들 데이터를 로드하여 DataFrame 반환
    - symbol: 로드할 Symbol 객체
    - start_at: 시작 timestamp (초 단위, None이면 처음부터)
    - end_at: 종료 timestamp (초 단위, None이면 끝까지)
    - limit: 반환할 최대 행 수 (None이면 전체)

    CandleRepository.query_to_dataframe()를 호출하여 데이터 조회
    통합/개별 테이블 모두 symbol.id를 symbol_id로 전달
    limit이 지정된 경우 DataFrame.head(limit)로 제한

## 의존성

- CandleRepository: 캔들 데이터 조회
- ConnectionManager: DB 연결 관리

## 사용 예시

```python
from candle_data_manager.Service.DataLoadService.DataLoadService import DataLoadService
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager

conn_manager = ConnectionManager("mysql+pymysql://root@localhost/candle_data_manager")
service = DataLoadService(conn_manager)

# 전체 데이터 로드
df = service.load(symbol)

# 시간 범위 지정 로드
df = service.load(symbol, start_at=1600000000, end_at=1700000000)

# 최신 100개만 로드
df = service.load(symbol, limit=100)
```
