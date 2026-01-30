# 구현되지 않은 Provider 호출 시 발생하는 예외
class ProviderNotImplementedError(Exception):
    def __init__(self, exchange: str):
        self.exchange = exchange
        super().__init__(f"Provider for exchange '{exchange}' is not implemented")
