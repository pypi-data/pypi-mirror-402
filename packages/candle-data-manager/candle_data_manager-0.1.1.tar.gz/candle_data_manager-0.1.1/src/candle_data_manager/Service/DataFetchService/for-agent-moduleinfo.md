# DataFetchService

Provider를 선택하여 캔들 데이터를 획득하는 Service.
ProviderRegistry를 통해 Symbol에 맞는 Provider를 찾고, Provider의 fetch 메서드를 호출하여 데이터를 가져온다.

## DataFetchService

_provider_registry: ProviderRegistry    # Provider 선택을 위한 레지스트리

fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    raise ProviderNotImplementedError
    지정된 기간의 캔들 데이터 획득
    - Symbol에 맞는 Provider 선택
    - Provider의 fetch 메서드 호출
    - 정규화된 캔들 데이터 반환 [{'timestamp': int, 'open': int, 'high': int, 'low': int, 'close': int, 'volume': int}]

fetch_all_data(symbol: Symbol) -> list[dict]
    raise ProviderNotImplementedError
    Provider가 제공하는 전체 기간의 캔들 데이터 획득
    - Symbol에 맞는 Provider 선택
    - Provider의 get_data_range로 데이터 범위 조회
    - oldest_ts와 latest_ts가 모두 있으면 전체 데이터 fetch
    - 범위가 없으면 (None, None) 빈 리스트 반환

get_market_list(archetype: str, exchange: str, tradetype: str) -> list[dict]
    raise ProviderNotImplementedError
    거래소의 전체 마켓 리스트 조회
    - archetype, exchange, tradetype으로 임시 Symbol 생성
    - 임시 Symbol로 Provider 선택
    - Provider의 get_market_list 호출
    - 마켓 정보 리스트 반환 [{"base": str, "quote": str, "timeframes": list[str], "listed_at": int | None, "full_name": str | None}]

## 사용 예시

```python
from candle_data_manager.Core.ConnectionManager.ConnectionManager import ConnectionManager
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Service.DataFetchService.DataFetchService import DataFetchService
from candle_data_manager.Core.Models.Symbol import Symbol

# ConnectionManager와 ProviderRegistry 초기화
conn_manager = ConnectionManager()
provider_registry = ProviderRegistry(conn_manager)

# DataFetchService 생성
fetch_service = DataFetchService(provider_registry)

# Symbol 생성
symbol = Symbol(
    archetype="CRYPTO",
    exchange="BINANCE",
    tradetype="SPOT",
    base="BTC",
    quote="USDT",
    timeframe="1h"
)

# 특정 기간 데이터 획득 (Unix timestamp 초 단위)
start_ts = 1609459200  # 2021-01-01 00:00:00 UTC
end_ts = 1609545600    # 2021-01-02 00:00:00 UTC
candles = fetch_service.fetch(symbol, start_ts, end_ts)
# [
#     {'timestamp': 1609459200, 'open': 29000, 'high': 29500, 'low': 28500, 'close': 29200, 'volume': 1000},
#     {'timestamp': 1609462800, 'open': 29200, 'high': 29800, 'low': 29000, 'close': 29500, 'volume': 1200},
#     ...
# ]

# 전체 데이터 획득 (Provider가 제공하는 모든 기간)
all_candles = fetch_service.fetch_all_data(symbol)

# 마켓 리스트 조회
markets = fetch_service.get_market_list("CRYPTO", "BINANCE", "SPOT")
# [
#     {"base": "BTC", "quote": "USDT", "timeframes": ["1m", "1h", "1d"], "listed_at": None, "full_name": "Bitcoin"},
#     {"base": "ETH", "quote": "USDT", "timeframes": ["1m", "1h", "1d"], "listed_at": None, "full_name": "Ethereum"},
#     ...
# ]
```

## 설계 원칙

1. **Service는 Core만 의존**: ProviderRegistry와 Provider만 사용
2. **단일 책임**: 데이터 획득만 담당, 저장/로드는 다른 Service의 책임
3. **Provider 추상화**: Symbol에 맞는 Provider를 자동 선택하여 사용
4. **예외 전파**: ProviderNotImplementedError 등 Provider 예외를 상위로 전파

## 의존성

- Core/ProviderRegistry: Provider 선택
- Core/Providers: 실제 데이터 획득
- Core/Models/Symbol: Symbol 정보
- Particles/Exceptions: 예외 처리
