# SymbolPreparationPlugin

Symbol 등록 + 테이블 준비를 조합하는 Plugin. SymbolService와 SymbolMetadata를 사용하여 Symbol 생성과 DB 테이블 준비를 원자적으로 수행한다.

## 의존성

- Service: SymbolService, SymbolMetadata
- Particles: Symbol

## 메서드

### register_and_prepare(session, archetype, exchange, tradetype, base, quote, timeframe, **optional) -> Symbol

Symbol 등록 및 테이블 준비

**동작:**
1. SymbolService.register_symbol()로 Symbol 등록 (이미 존재하면 기존 반환)
2. SymbolMetadata.prepare_table()로 캔들 테이블 준비 (없으면 생성)
3. Symbol 반환

**파라미터:**
- session: SQLAlchemy Session
- archetype: 자산 유형 (CRYPTO, STOCK 등)
- exchange: 거래소 (BINANCE, UPBIT, KRX 등)
- tradetype: 거래 유형 (SPOT, FUTURES 등)
- base: 기준 자산 (BTC, ETH, 005930 등)
- quote: 견적 자산 (USDT, KRW, USD 등)
- timeframe: 시간대 (1h, 4h, 1d, 1m 등)
- **optional: full_name, listed_at 등 추가 필드

**반환:**
- Symbol: 생성되거나 조회된 Symbol 객체

## 사용 예시

```python
# 새 Symbol 등록 및 테이블 준비
symbol = plugin.register_and_prepare(
    session,
    archetype='CRYPTO',
    exchange='BINANCE',
    tradetype='SPOT',
    base='BTC',
    quote='USDT',
    timeframe='1h',
    full_name='Bitcoin/USDT'
)

# 동일 Symbol 재등록 (기존 반환, 테이블은 이미 존재하면 건너뜀)
symbol2 = plugin.register_and_prepare(
    session,
    archetype='CRYPTO',
    exchange='BINANCE',
    tradetype='SPOT',
    base='BTC',
    quote='USDT',
    timeframe='1h'
)
# symbol.id == symbol2.id
```

## 특징

- **원자적 처리**: Symbol 등록과 테이블 준비를 하나의 작업으로 처리
- **중복 안전**: 이미 존재하는 Symbol과 테이블은 재생성하지 않음
- **자동 정규화**: SymbolService를 통해 archetype, exchange 등 자동 대문자 변환
- **단순 인터페이스**: 여러 Service 조합을 하나의 메서드로 제공

## 사용 위치

- UpdateOrchestrationPlugin: Active Update 시 각 마켓의 Symbol 등록 및 준비
- 다른 Plugin이나 Controller에서 새로운 Symbol 추가 시 사용
