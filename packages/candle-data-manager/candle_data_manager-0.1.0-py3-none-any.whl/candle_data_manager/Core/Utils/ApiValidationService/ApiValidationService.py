import os
import requests
from dotenv import load_dotenv, find_dotenv
from candle_data_manager.Particles.NoApiKeyError import NoApiKeyError
from candle_data_manager.Particles.ServerNotRespondedError import ServerNotRespondedError


# API 키 확보 및 서버 응답 검증
class ApiValidationService:
    def __init__(self):
        # .env 파일 자동 로드
        load_dotenv(find_dotenv())

        self.server_urls = {
            'BINANCE': 'https://api.binance.com/api/v3/time',
            'UPBIT': 'https://api.upbit.com/v1/market/all',
        }

    def get_api_key(self, exchange: str) -> str:
        # .env에서 거래소별 API 키 조회
        env_key_name = f"{exchange}_API_KEY"
        api_key = os.getenv(env_key_name)

        # 빈 문자열도 None으로 처리
        if not api_key:
            raise NoApiKeyError(exchange)

        return api_key

    def get_api_secret(self, exchange: str) -> str:
        # .env에서 거래소별 API Secret 조회
        env_key_name = f"{exchange}_API_SECRET"
        api_secret = os.getenv(env_key_name)

        # 빈 문자열도 None으로 처리
        if not api_secret:
            raise NoApiKeyError(exchange)

        return api_secret

    def check_server(self, exchange: str, api_key: str) -> bool:
        # API 서버 응답 확인
        url = self.server_urls.get(exchange, 'https://api.binance.com/api/v3/time')

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return True
        except Exception:
            raise ServerNotRespondedError(exchange)
