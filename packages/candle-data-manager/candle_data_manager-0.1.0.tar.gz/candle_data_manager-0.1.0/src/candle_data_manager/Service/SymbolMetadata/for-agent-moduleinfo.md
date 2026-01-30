# SymbolMetadata

Symbol의 메타데이터 관리 서비스.
테이블 존재 여부, 데이터 통계 (개수, 첫/마지막 타임스탬프) 조회 및 테이블 준비 기능 제공.

## SymbolMetadata

__init__(conn_manager: ConnectionManager) -> None
    ConnectionManager로 초기화

prepare_table(symbol: Symbol) -> None
    Symbol의 캔들 테이블 준비 (없으면 생성)

get_table_status(symbol: Symbol, symbol_id: int = None) -> dict
    raise ValueError  # 통합 테이블에서 symbol_id 없을 시
    Symbol의 테이블 상태 조회
    반환: {
        "exists": bool,          # 테이블 존재 여부
        "has_data": bool,        # 데이터 존재 여부
        "count": int,            # 레코드 개수
        "first_timestamp": int | None,  # 첫 타임스탬프
        "last_timestamp": int | None    # 마지막 타임스탬프
    }

## 사용 예시

```python
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.Models.Symbol import Symbol
from candle_data_manager.Service.SymbolMetadata.SymbolMetadata import SymbolMetadata

# 초기화
conn_manager = ConnectionManager()
manager = SymbolMetadata(conn_manager)

# Symbol 생성
symbol = Symbol.from_string("CRYPTO-BINANCE-SPOT-BTC-USDT-1m")

# 테이블 준비
manager.prepare_table(symbol)

# 테이블 상태 조회
status = manager.get_table_status(symbol)
print(f"테이블 존재: {status['exists']}")
print(f"데이터 존재: {status['has_data']}")
print(f"레코드 개수: {status['count']}")
print(f"첫 타임스탬프: {status['first_timestamp']}")
print(f"마지막 타임스탬프: {status['last_timestamp']}")

# 통합 테이블의 경우 symbol_id 제공
symbol_unified = Symbol.from_string("CRYPTO-BINANCE-SPOT-BTC-USDT-1h")
status = manager.get_table_status(symbol_unified, symbol_id=1)
```

## 의존성

- Core/ConnectionManager: DB 연결 관리
- Core/Models/CandleRepository: 캔들 데이터 저장소
- Core/Models/Symbol: Symbol 모델

## 주요 특징

- 테이블 자동 생성 (prepare_table)
- 테이블 존재 여부만 확인하고 생성하지 않음 (get_table_status에서 exists=False 가능)
- 통합/개별 테이블 모두 지원
- 통합 테이블은 symbol_id 필수
