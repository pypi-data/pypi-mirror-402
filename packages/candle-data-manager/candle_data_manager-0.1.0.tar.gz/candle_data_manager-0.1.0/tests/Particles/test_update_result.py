import pytest
from candle_data_manager.Particles.UpdateResult import UpdateResult
from candle_data_manager.Core.Models.Symbol import Symbol


@pytest.fixture
def sample_symbols():
    return [
        Symbol(
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="BTC",
            quote="USDT",
            timeframe="1h"
        ),
        Symbol(
            archetype="CRYPTO",
            exchange="BINANCE",
            tradetype="SPOT",
            base="ETH",
            quote="USDT",
            timeframe="1h"
        ),
        Symbol(
            archetype="CRYPTO",
            exchange="UPBIT",
            tradetype="SPOT",
            base="BTC",
            quote="KRW",
            timeframe="1m"
        )
    ]


def test_update_result_all_success(sample_symbols):
    """모든 Symbol 성공 케이스"""
    result = UpdateResult(
        success_symbols=sample_symbols,
        failed_symbols=[],
        total_rows=150000
    )

    assert len(result.success_symbols) == 3
    assert len(result.failed_symbols) == 0
    assert result.total_rows == 150000


def test_update_result_partial_failure(sample_symbols):
    """일부 Symbol 실패 케이스"""
    result = UpdateResult(
        success_symbols=[sample_symbols[0], sample_symbols[1]],
        failed_symbols=[(sample_symbols[2], "API rate limit exceeded")],
        total_rows=100000
    )

    assert len(result.success_symbols) == 2
    assert len(result.failed_symbols) == 1
    assert result.total_rows == 100000

    failed_symbol, reason = result.failed_symbols[0]
    assert failed_symbol.exchange == "UPBIT"
    assert "rate limit" in reason


def test_update_result_all_failure(sample_symbols):
    """모든 Symbol 실패 케이스"""
    failed = [
        (sample_symbols[0], "Network error"),
        (sample_symbols[1], "Invalid API key"),
        (sample_symbols[2], "Server not responding")
    ]

    result = UpdateResult(
        success_symbols=[],
        failed_symbols=failed,
        total_rows=0
    )

    assert len(result.success_symbols) == 0
    assert len(result.failed_symbols) == 3
    assert result.total_rows == 0


def test_update_result_zero_rows():
    """데이터 없는 경우"""
    result = UpdateResult(
        success_symbols=[],
        failed_symbols=[],
        total_rows=0
    )

    assert len(result.success_symbols) == 0
    assert len(result.failed_symbols) == 0
    assert result.total_rows == 0


def test_update_result_immutability(sample_symbols):
    """UpdateResult 불변성 확인"""
    result = UpdateResult(
        success_symbols=[sample_symbols[0]],
        failed_symbols=[],
        total_rows=1000
    )

    # frozen=True이면 값 변경 시 에러 발생
    with pytest.raises(Exception):
        result.total_rows = 2000

    with pytest.raises(Exception):
        result.success_symbols = []
