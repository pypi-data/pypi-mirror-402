# API 키가 환경변수에 없을 때 발생하는 예외
class NoApiKeyError(Exception):
    def __init__(self, exchange: str):
        self.exchange = exchange
        super().__init__(f"API key for '{exchange}' not found in environment variables")
