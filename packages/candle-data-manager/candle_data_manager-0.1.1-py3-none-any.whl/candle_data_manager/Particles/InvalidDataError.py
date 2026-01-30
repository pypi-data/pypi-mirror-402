# 유효하지 않은 데이터 발견 시 발생하는 예외
class InvalidDataError(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid data found: {reason}")
