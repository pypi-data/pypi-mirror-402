# SymbolService

Symbol 등록/조회 Service. SymbolRepository를 통해 DB 작업을 수행하며, 입력값 정규화(대문자 변환)를 담당한다.

## 의존성

- Core: SymbolRepository, ConnectionManager
- Particles: Symbol

## 메서드

### register_symbol(session, archetype, exchange, tradetype, base, quote, timeframe, **optional) -> Symbol

Symbol 등록 (이미 존재하면 기존 반환)

- archetype, exchange, tradetype, base, quote를 자동으로 대문자 변환
- optional: full_name, listed_at 등 추가 필드
- SymbolRepository.get_or_create() 사용

### find_symbols(session, archetype=None, exchange=None, tradetype=None, base=None, quote=None, timeframe=None) -> list[Symbol]

조건으로 Symbol 검색

- 모든 파라미터 선택사항
- 조건 없으면 전체 조회
- 입력값 자동 대문자 변환 (timeframe 제외)
- 여러 조건 AND 조합

### get_by_string(session, symbol_str: str) -> Symbol | None

문자열로 Symbol 조회

- 형식: "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"
- Symbol.from_string()으로 파싱
- DB에 없으면 None 반환
- ValueError: 잘못된 형식

## 사용 예시

```python
# 등록
symbol = symbol_service.register_symbol(
    session,
    archetype='CRYPTO',
    exchange='BINANCE',
    tradetype='SPOT',
    base='BTC',
    quote='USDT',
    timeframe='1h',
    full_name='Bitcoin/USDT'
)

# 조건 검색
symbols = symbol_service.find_symbols(
    session,
    archetype='CRYPTO',
    exchange='BINANCE'
)

# 문자열 조회
symbol = symbol_service.get_by_string(
    session,
    'CRYPTO-BINANCE-SPOT-BTC-USDT-1h'
)
```

## 특징

- 입력값 정규화: archetype, exchange, tradetype, base, quote를 대문자로 자동 변환
- 중복 방지: get_or_create로 동일 Symbol 중복 생성 방지
- 유연한 검색: 조건 조합으로 다양한 Symbol 필터링
