# NullHandlingService

누락된 데이터 처리. volume은 0으로, 가격은 이전값 또는 DB 조회로 채움.

_conn_manager: ConnectionManager  # DB 연결 관리자

## 초기화

__init__(conn_manager: ConnectionManager) -> None
    NullHandlingService 초기화

    Args:
        conn_manager: DB 연결 관리자 (마지막 캔들 조회용)

## Null 처리

handle(data: list[dict], symbol: Symbol) -> list[dict]
    누락된 데이터 채우기

    Args:
        data: 정규화된 캔들 데이터 (null 포함 가능)
        symbol: Symbol 객체 (DB 조회용)

    Returns:
        list[dict]: Null 처리 완료된 데이터

    Raises:
        InvalidDataError: 이전값도 DB도 없어서 채울 수 없는 경우

    Notes:
        - volume이 null → 0
        - 가격(OHLC)이 null:
          1. 응답 내 이전 캔들의 close 값 사용
          2. 이전 캔들도 null → DB에서 마지막 캔들 조회
          3. DB에도 없음 → InvalidDataError

---

**사용 예시:**
```python
service = NullHandlingService(conn_manager)

data = [
    {'timestamp': 1, 'open': 100, 'high': 110, 'low': 90, 'close': 105, 'volume': 1000},
    {'timestamp': 2, 'open': None, 'high': None, 'low': None, 'close': None, 'volume': None}
]

handled = service.handle(data, symbol)
# [
#     {'timestamp': 1, 'open': 100, ...},
#     {'timestamp': 2, 'open': 105, 'high': 105, 'low': 105, 'close': 105, 'volume': 0}
# ]
```

**의존성:**
- Core/ConnectionManager: DB 연결
- Core/Models/CandleRepository: 마지막 캔들 조회
