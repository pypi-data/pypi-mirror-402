# MarketFactoryService

Symbol과 캔들 데이터를 받아 Market 객체를 생성하는 팩토리 서비스.
단순한 데이터 조합 책임만 가지며, 다른 Service에 의존하지 않는다.

## create_market(symbol: Symbol, candles: pd.DataFrame) -> Market
Symbol과 DataFrame을 받아 Market 객체를 생성하여 반환한다.
DataFrame 참조를 그대로 유지한다.
