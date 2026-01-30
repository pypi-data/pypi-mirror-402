"""Basic tests for candle_data_manager package."""

import candle_data_manager


def test_version():
    """Test version is defined."""
    assert hasattr(candle_data_manager, "__version__")
    assert isinstance(candle_data_manager.__version__, str)
