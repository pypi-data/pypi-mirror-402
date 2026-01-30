# NormalizationService

거래소별 API 응답을 통일된 형식으로 변환. 키 매핑, 타입 변환, 가격 int 변환 수행.

## 정규화 메서드

normalize_binance(raw_data: list[dict]) -> list[dict]
    Binance API 응답을 정규화

    Args:
        raw_data: Binance API 응답 (예: [{"t": 1234, "o": "100.5", ...}])

    Returns:
        list[dict]: 정규화된 데이터
        [{'timestamp': int, 'open': int, 'high': int, 'low': int, 'close': int, 'volume': int}]

    Notes:
        - 키 매핑: t→timestamp, o→open, h→high, l→low, c→close, v→volume
        - 타입 변환: string → float → int (× 10^8)
        - CandleRepository.to_storage() 활용

normalize_upbit(raw_data: list[dict]) -> list[dict]
    Upbit API 응답을 정규화

    Args:
        raw_data: Upbit API 응답 (예: [{"timestamp": 1234, "opening_price": 100.5, ...}])

    Returns:
        list[dict]: 정규화된 데이터

    Notes:
        - 키 매핑: timestamp→timestamp, opening_price→open, high_price→high,
                   low_price→low, trade_price→close, candle_acc_trade_volume→volume

normalize_fdr(raw_data: pd.DataFrame) -> list[dict]
    FDR DataFrame을 정규화

    Args:
        raw_data: FDR DataFrame (컬럼: Date, Open, High, Low, Close, Volume)

    Returns:
        list[dict]: 정규화된 데이터

    Notes:
        - Date를 Unix timestamp로 변환 (TimeConverter 활용)
        - Open/High/Low/Close를 int로 변환

---

**사용 예시:**
```python
service = NormalizationService()

# Binance
raw = [{"t": 1704067200000, "o": "42000.5", "h": "42500", "l": "41800", "c": "42200", "v": "1000"}]
normalized = service.normalize_binance(raw)
# [{'timestamp': 1704067200, 'open': 4200050000000, ...}]
```

**의존성:**
- Core/TimeConverter: 시간 변환
- Core/Models/CandleRepository: 가격 변환 (to_storage)
