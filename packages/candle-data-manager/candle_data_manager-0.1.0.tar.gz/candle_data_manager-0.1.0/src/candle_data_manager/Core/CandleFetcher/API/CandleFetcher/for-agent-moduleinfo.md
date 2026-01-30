# CandleFetcher

캔들 데이터 획득의 진입점. Symbol의 exchange와 tradetype을 기반으로 적절한 Provider를 선택하고 캔들 데이터를 가져온다.

_conn_manager: ConnectionManager  # Provider 초기화에 사용
_providers: dict[str, object]  # Provider 인스턴스 캐시 {exchange_key: provider}

## 메서드

__init__(conn_manager: ConnectionManager) -> None
    CandleFetcher 초기화. ConnectionManager를 저장하고 Provider 캐시 딕셔너리 생성.

fetch(symbol: Symbol, start_at: str | int, end_at: str | int) -> list[dict]
    raise ProviderNotImplementedError
    Symbol의 exchange와 tradetype을 기반으로 Provider를 선택하고 캔들 데이터 획득.
    start_at, end_at는 문자열("2021-5-3") 또는 정수(초/밀리초)로 전달 가능.
    TimeConverter를 사용하여 int(초) 형식으로 변환 후 Provider에 전달.

## Provider 매핑 규칙

- BINANCE + SPOT → BinanceSpotProvider (캐시 키: "BINANCE_SPOT")
- BINANCE + FUTURES → BinanceFuturesProvider (캐시 키: "BINANCE_FUTURES")
- UPBIT + any → UpbitProvider (캐시 키: "UPBIT")
- KRX, NYSE, NASDAQ, AMEX, SSE, SZSE, HKEX, TSE → FdrProvider (캐시 키: "FDR")
- 기타 → ProviderNotImplementedError 발생

## 반환 데이터 형식

```python
[
    {
        'timestamp': int,  # Unix timestamp (초)
        'open': int,       # × 10^8
        'high': int,
        'low': int,
        'close': int,
        'volume': int
    }
]
```

## 사용 예시

```python
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.CandleFetcher.API.CandleFetcher.CandleFetcher import CandleFetcher
from candle_data_manager.Core.Models.Symbol import Symbol

conn_manager = ConnectionManager("mysql://...")
fetcher = CandleFetcher(conn_manager)

symbol = Symbol(archetype='CRYPTO', exchange='BINANCE', tradetype='SPOT',
                base='BTC', quote='USDT', timeframe='1d')
data = fetcher.fetch(symbol, "2024-1-1", "2024-1-31")
```
