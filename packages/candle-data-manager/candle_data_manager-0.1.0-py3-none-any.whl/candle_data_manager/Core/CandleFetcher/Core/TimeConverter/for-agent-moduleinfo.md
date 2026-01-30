# TimeConverter

다양한 시간 형식을 Unix timestamp 또는 datetime으로 변환.

## 변환

mutate_to(value: str | int | datetime, to_type: str) -> int | datetime
    시간 형식 변환

    Args:
        value: 변환할 시간 (문자열, int, datetime)
            - 문자열: "2021-5-3", "2025-1-5 5:12:39"
            - int: Unix timestamp (sec 또는 ms, 자동 구분)
            - datetime: datetime 객체
        to_type: 목표 형식 ("timestamp" 또는 "datetime")

    Returns:
        int | datetime: 변환된 시간
            - "timestamp": int (Unix timestamp, 초 단위)
            - "datetime": datetime 객체

    Notes:
        - int 값의 자리수로 sec/ms 자동 구분 (10자리: sec, 13자리: ms)
        - 문자열 파싱은 dateutil.parser 활용
        - timezone은 UTC 가정

---

**사용 예시:**
```python
# 문자열 → timestamp
ts = TimeConverter.mutate_to("2024-1-1", "timestamp")  # 1704067200

# ms timestamp → sec timestamp
ts = TimeConverter.mutate_to(1704067200000, "timestamp")  # 1704067200

# timestamp → datetime
dt = TimeConverter.mutate_to(1704067200, "datetime")  # datetime(2024, 1, 1, 0, 0)
```

**의존성:**
- dateutil.parser: 문자열 파싱
- datetime: datetime 객체 처리
