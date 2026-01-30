# FdrProvider

FinanceDataReader를 사용한 금융 데이터 조회. API 키 불필요.

## 지원 거래소

**검증됨 (2026-01):**
- **KRX** (한국거래소): KOSPI, KOSDAQ, KONEX
- **NYSE** (뉴욕증권거래소): 2,728개 종목
- **NASDAQ**: 3,780개 종목
- **AMEX** (미국증권거래소): 300개 종목

**추가 지원 (문서 기준):**
- **SSE** (상하이증권거래소)
- **SZSE** (선전증권거래소)
- **HKEX** (홍콩거래소)
- **TSE** (도쿄증권거래소)

## 초기화

__init__(conn_manager: ConnectionManager) -> None
    API 키 검증 불필요 (공개 데이터)

    Notes:
        - ApiValidationService 사용 안 함
        - NormalizationService, NullHandlingService만 초기화

## 데이터 조회

fetch(symbol: Symbol, start_at: int, end_at: int) -> list[dict]
    금융 데이터 조회

    Args:
        symbol: Symbol 객체
        start_at: 시작 타임스탬프 (초 단위)
        end_at: 종료 타임스탬프 (초 단위)

    Returns:
        list[dict]: 정규화된 캔들 데이터

    Notes:
        - symbol.base를 ticker로 사용
        - KRX: 숫자 종목코드 (예: "005930")
        - 해외: 티커 심볼 (예: "AAPL", "MSFT")
        - 타임스탬프를 datetime으로 변환하여 API 호출
        - FDR은 주로 일봉 데이터 제공

## Ticker 형식

- **KRX**: 6자리 숫자 (예: "005930" - 삼성전자)
- **NYSE/NASDAQ/AMEX**: 알파벳 심볼 (예: "AAPL", "MSFT", "SPY")
- **자동 감지**: 숫자만 → KRX, 알파벳 포함 → 미국 시장 우선 검색

## 응답 형식

FDR DataFrame 컬럼:
- Open: 시가
- High: 고가
- Low: 저가
- Close: 종가
- Volume: 거래량
- Change: 변화율 (KRX만)
- Adj Close: 조정 종가 (미국 시장만)

---

**사용 예시:**
```python
provider = FdrProvider(conn_manager)

# 한국 주식 (삼성전자)
symbol = Symbol(archetype="stock", exchange="KRX", tradetype="SPOT",
                base="005930", quote="KRW", timeframe="1d")
data = provider.fetch(symbol, start_at, end_at)

# 미국 주식 (Apple)
symbol = Symbol(archetype="stock", exchange="NYSE", tradetype="SPOT",
                base="AAPL", quote="USD", timeframe="1d")
data = provider.fetch(symbol, start_at, end_at)
```

**의존성:**
- FinanceDataReader: 금융 데이터 조회
- pandas: DataFrame 처리
