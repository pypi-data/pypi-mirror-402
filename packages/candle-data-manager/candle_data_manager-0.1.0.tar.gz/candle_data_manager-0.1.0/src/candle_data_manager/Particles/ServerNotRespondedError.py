# 서버가 응답하지 않을 때 발생하는 예외
class ServerNotRespondedError(Exception):
    def __init__(self, exchange: str):
        self.exchange = exchange
        super().__init__(f"Server for '{exchange}' did not respond")
