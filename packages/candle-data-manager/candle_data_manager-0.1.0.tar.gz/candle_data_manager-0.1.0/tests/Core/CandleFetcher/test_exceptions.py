import pytest
import sys
from pathlib import Path

# src를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'src'))

# Exception 클래스들을 개별 모듈에서 직접 import
import importlib.util

def load_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# 각 Exception 파일의 절대 경로
base_path = Path(__file__).parent.parent.parent.parent / 'src' / 'candle_data_manager' / 'Core' / 'CandleFetcher' / 'Exceptions'

provider_error_module = load_module_from_file(
    base_path / 'ProviderNotImplementedError.py',
    'ProviderNotImplementedError'
)
ProviderNotImplementedError = provider_error_module.ProviderNotImplementedError

no_api_key_module = load_module_from_file(
    base_path / 'NoApiKeyError.py',
    'NoApiKeyError'
)
NoApiKeyError = no_api_key_module.NoApiKeyError

server_error_module = load_module_from_file(
    base_path / 'ServerNotRespondedError.py',
    'ServerNotRespondedError'
)
ServerNotRespondedError = server_error_module.ServerNotRespondedError

invalid_data_module = load_module_from_file(
    base_path / 'InvalidDataError.py',
    'InvalidDataError'
)
InvalidDataError = invalid_data_module.InvalidDataError


class TestProviderNotImplementedError:
    def test_creation(self):
        # Exception 생성 가능
        error = ProviderNotImplementedError("UNKNOWN")
        assert error is not None

    def test_is_exception(self):
        # Exception의 서브클래스
        error = ProviderNotImplementedError("UNKNOWN")
        assert isinstance(error, Exception)

    def test_message(self):
        # 올바른 메시지 포맷
        error = ProviderNotImplementedError("UNKNOWN")
        assert str(error) == "Provider for exchange 'UNKNOWN' is not implemented"

    def test_raise_and_catch(self):
        # raise/catch 정상 작동
        with pytest.raises(ProviderNotImplementedError) as exc_info:
            raise ProviderNotImplementedError("TEST_EXCHANGE")
        assert "TEST_EXCHANGE" in str(exc_info.value)


class TestNoApiKeyError:
    def test_creation(self):
        # Exception 생성 가능
        error = NoApiKeyError("BINANCE")
        assert error is not None

    def test_is_exception(self):
        # Exception의 서브클래스
        error = NoApiKeyError("BINANCE")
        assert isinstance(error, Exception)

    def test_message(self):
        # 올바른 메시지 포맷
        error = NoApiKeyError("BINANCE")
        assert str(error) == "API key for 'BINANCE' not found in environment variables"

    def test_raise_and_catch(self):
        # raise/catch 정상 작동
        with pytest.raises(NoApiKeyError) as exc_info:
            raise NoApiKeyError("UPBIT")
        assert "UPBIT" in str(exc_info.value)


class TestServerNotRespondedError:
    def test_creation(self):
        # Exception 생성 가능
        error = ServerNotRespondedError("BINANCE")
        assert error is not None

    def test_is_exception(self):
        # Exception의 서브클래스
        error = ServerNotRespondedError("BINANCE")
        assert isinstance(error, Exception)

    def test_message(self):
        # 올바른 메시지 포맷
        error = ServerNotRespondedError("BINANCE")
        assert str(error) == "Server for 'BINANCE' did not respond"

    def test_raise_and_catch(self):
        # raise/catch 정상 작동
        with pytest.raises(ServerNotRespondedError) as exc_info:
            raise ServerNotRespondedError("FDR")
        assert "FDR" in str(exc_info.value)


class TestInvalidDataError:
    def test_creation(self):
        # Exception 생성 가능
        error = InvalidDataError("missing price field")
        assert error is not None

    def test_is_exception(self):
        # Exception의 서브클래스
        error = InvalidDataError("missing price field")
        assert isinstance(error, Exception)

    def test_message(self):
        # 올바른 메시지 포맷
        error = InvalidDataError("null price cannot be recovered")
        assert str(error) == "Invalid data found: null price cannot be recovered"

    def test_raise_and_catch(self):
        # raise/catch 정상 작동
        with pytest.raises(InvalidDataError) as exc_info:
            raise InvalidDataError("test reason")
        assert "test reason" in str(exc_info.value)
