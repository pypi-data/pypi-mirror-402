import pytest
from candle_data_manager.Core.Models.Symbol import Symbol


class TestSymbolStringConversion:
    """Symbol 문자열 변환 기능 테스트"""

    def test_from_string_valid(self):
        """정상적인 문자열을 Symbol 객체로 변환"""
        symbol_str = "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"
        symbol = Symbol.from_string(symbol_str)

        assert symbol.archetype == "CRYPTO"
        assert symbol.exchange == "BINANCE"
        assert symbol.tradetype == "SPOT"
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"
        assert symbol.timeframe == "1h"

    def test_from_string_lowercase_converted_to_uppercase(self):
        """소문자 입력도 대문자로 변환되는지 확인 (timeframe 제외)"""
        symbol_str = "crypto-binance-spot-btc-usdt-1h"
        symbol = Symbol.from_string(symbol_str)

        assert symbol.archetype == "CRYPTO"
        assert symbol.exchange == "BINANCE"
        assert symbol.tradetype == "SPOT"
        assert symbol.base == "BTC"
        assert symbol.quote == "USDT"
        assert symbol.timeframe == "1h"

    def test_from_string_invalid_too_few_parts(self):
        """파트 개수가 부족한 경우 ValueError"""
        symbol_str = "CRYPTO-BINANCE-SPOT-BTC-USDT"
        with pytest.raises(ValueError, match="Invalid symbol string format"):
            Symbol.from_string(symbol_str)

    def test_from_string_invalid_too_many_parts(self):
        """파트 개수가 초과한 경우 ValueError"""
        symbol_str = "CRYPTO-BINANCE-SPOT-BTC-USDT-1h-EXTRA"
        with pytest.raises(ValueError, match="Invalid symbol string format"):
            Symbol.from_string(symbol_str)

    def test_from_string_empty_string(self):
        """빈 문자열인 경우 ValueError"""
        with pytest.raises(ValueError, match="Invalid symbol string format"):
            Symbol.from_string("")

    def test_to_string_valid(self):
        """Symbol 객체를 문자열로 변환"""
        symbol = Symbol(
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="BTC",
            quote="USDT",
            timeframe="1h"
        )

        result = symbol.to_string()
        assert result == "CRYPTO-BINANCE-SPOT-BTC-USDT-1h"

    def test_str_calls_to_string(self):
        """__str__이 to_string과 동일한 결과 반환"""
        symbol = Symbol(
            archetype="CRYPTO",
            exchange="UPBIT",
            tradetype="SPOT",
            base="BTC",
            quote="KRW",
            timeframe="1d"
        )

        assert str(symbol) == symbol.to_string()
        assert str(symbol) == "CRYPTO-UPBIT-SPOT-BTC-KRW-1d"

    def test_round_trip_conversion(self):
        """문자열 -> Symbol -> 문자열 왕복 변환"""
        original_str = "STOCK-KRX-SPOT-005930-KRW-1d"
        symbol = Symbol.from_string(original_str)
        result_str = symbol.to_string()

        assert result_str == original_str

    def test_round_trip_with_lowercase(self):
        """소문자 입력 -> Symbol -> 문자열 (대문자로 변환됨)"""
        input_str = "crypto-binance-futures-eth-usdt-4h"
        symbol = Symbol.from_string(input_str)
        result_str = symbol.to_string()

        assert result_str == "CRYPTO-BINANCE-FUTURES-ETH-USDT-4h"

    def test_various_exchanges(self):
        """다양한 거래소 문자열 변환 테스트"""
        test_cases = [
            "CRYPTO-BINANCE-SPOT-BTC-USDT-1h",
            "CRYPTO-UPBIT-SPOT-BTC-KRW-1d",
            "STOCK-KRX-SPOT-005930-KRW-1d",
            "STOCK-NYSE-SPOT-AAPL-USD-1d",
            "CRYPTO-BINANCE-FUTURES-ETH-USDT-15m"
        ]

        for test_str in test_cases:
            symbol = Symbol.from_string(test_str)
            result = symbol.to_string()
            assert result == test_str
