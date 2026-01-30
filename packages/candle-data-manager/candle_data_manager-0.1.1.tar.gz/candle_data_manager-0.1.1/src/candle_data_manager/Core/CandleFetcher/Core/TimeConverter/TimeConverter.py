from datetime import datetime, timezone
from dateutil import parser


class TimeConverter:

    @staticmethod
    def mutate_to(value: str | int | datetime, to_type: str) -> int | datetime:
        # 입력값을 datetime으로 먼저 변환
        dt = TimeConverter._to_datetime(value)

        # 목표 형식으로 변환
        if to_type == "timestamp":
            return int(dt.timestamp())
        elif to_type == "datetime":
            return dt
        else:
            raise ValueError(f"Invalid to_type: {to_type}")

    @staticmethod
    def _to_datetime(value: str | int | datetime) -> datetime:
        # 이미 datetime인 경우
        if isinstance(value, datetime):
            # timezone 정보가 없으면 UTC 추가
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value

        # 문자열인 경우
        if isinstance(value, str):
            dt = parser.parse(value)
            # timezone 정보가 없으면 UTC 추가
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        # int인 경우
        if isinstance(value, int):
            # 자리수로 sec/ms 구분
            digit_count = len(str(value))
            if digit_count == 13:
                # ms를 sec로 변환
                value = value // 1000
            elif digit_count != 10:
                raise ValueError(f"Invalid timestamp length: {digit_count}")

            return datetime.fromtimestamp(value, tz=timezone.utc)

        raise TypeError(f"Unsupported type: {type(value)}")
