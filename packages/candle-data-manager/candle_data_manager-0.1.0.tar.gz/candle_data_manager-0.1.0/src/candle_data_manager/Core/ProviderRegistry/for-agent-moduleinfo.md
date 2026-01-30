# ProviderRegistry

Symbol의 archetype, exchange, tradetype에 맞는 Provider를 선택하고 관리하는 레지스트리.
현재는 Provider 클래스 이름(문자열)을 반환하며, 실제 Provider 클래스들이 Core/Providers로 이동하면 인스턴스를 반환하도록 확장 예정.

## ProviderRegistry

_providers: dict = {}    # Provider 인스턴스 캐시 (향후 사용)

_get_provider_mapping() -> dict[tuple[str, str, str], str]
    매핑 딕셔너리 반환
    - Key: (archetype, exchange, tradetype) 튜플
    - Value: Provider 클래스 이름 문자열
    - 현재 매핑: BINANCE SPOT/FUTURES, UPBIT SPOT, KRX/NYSE/NASDAQ SPOT

get_provider(symbol: Symbol) -> str
    raise ProviderNotImplementedError
    Symbol에 맞는 Provider 클래스 이름 반환
    - 매핑에 없는 조합이면 ProviderNotImplementedError 발생
    - 현재는 문자열 반환, 향후 Provider 인스턴스 반환으로 변경 예정

get_providers_by_condition(archetype: str = None, exchange: str = None, tradetype: str = None) -> list[str]
    조건에 맞는 모든 Provider 클래스 이름 반환
    - 조건이 None이면 해당 조건 무시
    - 중복 제거된 리스트 반환
    - 현재는 문자열 리스트 반환, 향후 Provider 인스턴스 리스트 반환으로 변경 예정

## 사용 예시

```python
from candle_data_manager.Core.ProviderRegistry.ProviderRegistry import ProviderRegistry
from candle_data_manager.Core.Models.Symbol import Symbol

# Symbol 생성
symbol = Symbol(
    archetype="CRYPTO",
    exchange="BINANCE",
    tradetype="SPOT",
    base="BTC",
    quote="USDT",
    timeframe="1h"
)

# Provider 선택
provider_name = ProviderRegistry.get_provider(symbol)
# "BinanceSpotProvider"

# 조건별 Provider 조회
crypto_providers = ProviderRegistry.get_providers_by_condition(archetype="CRYPTO")
# ["BinanceSpotProvider", "BinanceFuturesProvider", "UpbitProvider"]

binance_providers = ProviderRegistry.get_providers_by_condition(exchange="BINANCE")
# ["BinanceSpotProvider", "BinanceFuturesProvider"]

spot_providers = ProviderRegistry.get_providers_by_condition(tradetype="SPOT")
# ["BinanceSpotProvider", "UpbitProvider", "FdrProvider"]

# 여러 조건 동시 적용
crypto_spot = ProviderRegistry.get_providers_by_condition(archetype="CRYPTO", tradetype="SPOT")
# ["BinanceSpotProvider", "UpbitProvider"]
```

## 향후 확장

1. Provider 클래스 이동 후:
   - 실제 Provider 클래스 import
   - 인스턴스 캐싱 (_providers 딕셔너리 활용)
   - get_provider() → IProvider 인스턴스 반환
   - get_providers_by_condition() → list[IProvider] 반환

2. 추가 가능 기능:
   - Provider 동적 등록 메서드
   - Provider 설정 관리
   - Provider 헬스체크
