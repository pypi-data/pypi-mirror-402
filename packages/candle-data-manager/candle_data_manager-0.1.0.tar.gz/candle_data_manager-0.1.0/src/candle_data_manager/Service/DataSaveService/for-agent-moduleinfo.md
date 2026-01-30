# DataSaveService

캔들 데이터 저장 및 bulk insert 최적화.

## DataSaveService

__init__(conn_manager)
    ConnectionManager 주입

save(symbol: Symbol, data: list[dict]) -> None
    단일 Symbol 데이터 저장
    - 가격 변환: float -> int64 (× 10^8)
    - 통합 테이블: symbol_id 추가
    - CandleRepository.upsert 호출
    - last_timestamp 업데이트

bulk_save(buffer: dict[Symbol, list[dict]]) -> None
    여러 Symbol 데이터를 테이블별로 재그룹화하여 bulk insert
    - 테이블별 재그룹화: Symbol별 → 테이블별
    - 통합 테이블: 같은 테이블의 여러 Symbol 데이터를 한번에 저장
    - 개별 테이블: 각 테이블마다 개별 bulk insert
    - 최적화: 테이블 개수만큼만 DB 호출
    - last_timestamp 업데이트 (각 Symbol마다)

_regroup_by_table(buffer: dict) -> dict
    Symbol별 버퍼를 테이블별로 재그룹화
    - 입력: {Symbol: list[dict]}
    - 출력: {table_name: [(Symbol, list[dict])]}

_convert_prices(data: list[dict]) -> list[dict]
    가격을 float에서 int64로 변환
    - CandleRepository.to_storage 사용
    - OHLCV 모두 변환 (× 10^8)

## 알고리즘 예시

```
입력 버퍼:
{
    Symbol(BTC-USDT-1h): [1000 rows],
    Symbol(ETH-USDT-1h): [2000 rows],
    Symbol(BTC-USDT-1m): [50000 rows],
    Symbol(ETH-USDT-1m): [47000 rows]
}

1단계 재그룹화:
{
    'crypto_binance_spot_1h': [
        (BTC-USDT-1h, 1000 rows),
        (ETH-USDT-1h, 2000 rows)
    ],
    'crypto_binance_spot_btc_usdt_1m': [
        (BTC-USDT-1m, 50000 rows)
    ],
    'crypto_binance_spot_eth_usdt_1m': [
        (ETH-USDT-1m, 47000 rows)
    ]
}

2단계 bulk insert:
- crypto_binance_spot_1h: 3000 rows (symbol_id로 구분)
- crypto_binance_spot_btc_usdt_1m: 50000 rows
- crypto_binance_spot_eth_usdt_1m: 47000 rows

총 3번의 bulk insert 실행
```

## 의존성

Core:
- CandleRepository: upsert, to_storage
- SymbolRepository: update_last_timestamp
- ConnectionManager: get_connection, session_scope

## 사용 예시

```python
# 단일 저장
conn_mgr = ConnectionManager(database_url)
service = DataSaveService(conn_mgr)

symbol = Symbol(archetype="CRYPTO", exchange="BINANCE", tradetype="SPOT",
                base="BTC", quote="USDT", timeframe="1h")
data = [
    {"timestamp": 1600000000, "open": 10000.5, "high": 10100.0,
     "low": 9900.0, "close": 10050.0, "volume": 1000.0}
]
service.save(symbol, data)

# 벌크 저장 (메모리 버퍼)
buffer = {
    symbol1: [1000 rows],
    symbol2: [2000 rows],
    symbol3: [50000 rows]
}
service.bulk_save(buffer)
```
