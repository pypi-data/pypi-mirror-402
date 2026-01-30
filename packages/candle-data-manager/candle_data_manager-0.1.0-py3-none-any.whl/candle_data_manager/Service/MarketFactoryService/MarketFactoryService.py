import pandas as pd
from loguru import logger
from ...Particles.Market import Market
from ...Core.Models.Symbol import Symbol


class MarketFactoryService:
    def __init__(self):
        pass

    def create_market(self, symbol: Symbol, candles: pd.DataFrame) -> Market:
        # Symbol과 DataFrame으로 Market 객체 생성
        return Market(symbol=symbol, candles=candles)
