import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import importlib.util

# src를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / 'src'))

def load_module_from_file(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Exception 클래스들 로드
base_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'candle_data_manager' / 'Core' / 'CandleFetcher' / 'Exceptions'

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

# ApiValidationService 로드
service_path = Path(__file__).parent.parent.parent.parent.parent / 'src' / 'candle_data_manager' / 'Core' / 'CandleFetcher' / 'Service' / 'ApiValidationService'
api_validation_module = load_module_from_file(
    service_path / 'ApiValidationService.py',
    'ApiValidationService'
)
ApiValidationService = api_validation_module.ApiValidationService


class TestGetApiKey:
    def test_get_api_key_success(self):
        # 환경변수에 API 키가 있으면 반환
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = "test_api_key_123"
            result = service.get_api_key("BINANCE")
            assert result == "test_api_key_123"
            mock_getenv.assert_called_once_with("BINANCE_API_KEY")

    def test_get_api_key_no_key_found(self):
        # 환경변수에 API 키가 없으면 NoApiKeyError
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            with pytest.raises(Exception) as exc_info:
                service.get_api_key("BINANCE")
            assert "BINANCE" in str(exc_info.value)
            assert exc_info.value.exchange == "BINANCE"

    def test_get_api_key_different_exchanges(self):
        # 다양한 거래소 이름 처리
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = "upbit_key"
            result = service.get_api_key("UPBIT")
            assert result == "upbit_key"
            mock_getenv.assert_called_with("UPBIT_API_KEY")

    def test_get_api_key_empty_string(self):
        # 빈 문자열도 None과 동일하게 처리
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = ""
            with pytest.raises(Exception) as exc_info:
                service.get_api_key("BINANCE")
            assert "BINANCE" in str(exc_info.value)


class TestGetApiSecret:
    def test_get_api_secret_success(self):
        # 환경변수에 API Secret이 있으면 반환
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = "test_secret_xyz"
            result = service.get_api_secret("BINANCE")
            assert result == "test_secret_xyz"
            mock_getenv.assert_called_once_with("BINANCE_API_SECRET")

    def test_get_api_secret_no_key_found(self):
        # 환경변수에 API Secret이 없으면 NoApiKeyError
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = None
            with pytest.raises(Exception) as exc_info:
                service.get_api_secret("UPBIT")
            assert "UPBIT" in str(exc_info.value)
            assert exc_info.value.exchange == "UPBIT"

    def test_get_api_secret_empty_string(self):
        # 빈 문자열도 None과 동일하게 처리
        service = ApiValidationService()
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = ""
            with pytest.raises(Exception) as exc_info:
                service.get_api_secret("BINANCE")
            assert "BINANCE" in str(exc_info.value)


class TestCheckServer:
    def test_check_server_success(self):
        # 서버 응답 성공시 True 반환
        service = ApiValidationService()
        with patch.object(api_validation_module, 'requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"serverTime": 1234567890}
            mock_requests.get.return_value = mock_response

            result = service.check_server("BINANCE", "test_key")
            assert result is True
            mock_requests.get.assert_called_once()
            # timeout 5초 확인
            assert mock_requests.get.call_args[1]['timeout'] == 5

    def test_check_server_timeout(self):
        # timeout 발생시 ServerNotRespondedError
        service = ApiValidationService()
        import requests as req_module

        with patch.object(api_validation_module, 'requests') as mock_requests:
            mock_requests.get.side_effect = req_module.Timeout()

            with pytest.raises(Exception) as exc_info:
                service.check_server("BINANCE", "test_key")
            assert "BINANCE" in str(exc_info.value)
            assert exc_info.value.exchange == "BINANCE"

    def test_check_server_connection_error(self):
        # 연결 실패시 ServerNotRespondedError
        service = ApiValidationService()
        import requests as req_module

        with patch.object(api_validation_module, 'requests') as mock_requests:
            mock_requests.get.side_effect = req_module.ConnectionError()

            with pytest.raises(Exception) as exc_info:
                service.check_server("BINANCE", "test_key")
            assert "BINANCE" in str(exc_info.value)

    def test_check_server_http_error(self):
        # HTTP 에러 발생시 ServerNotRespondedError
        service = ApiValidationService()
        with patch.object(api_validation_module, 'requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = Exception("Server Error")
            mock_requests.get.return_value = mock_response

            with pytest.raises(Exception) as exc_info:
                service.check_server("BINANCE", "test_key")
            assert "BINANCE" in str(exc_info.value)

    def test_check_server_different_exchanges(self):
        # 다양한 거래소 처리
        service = ApiValidationService()
        with patch.object(api_validation_module, 'requests') as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            result = service.check_server("UPBIT", "upbit_key")
            assert result is True
