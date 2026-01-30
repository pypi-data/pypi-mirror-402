from dataclasses import dataclass
import pandas as pd
from ..Core.Models.Symbol import Symbol


@dataclass
class Market:
    symbol: Symbol
    candles: pd.DataFrame
