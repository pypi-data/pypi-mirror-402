# TimeConverter

다양한 시간 형식을 Unix timestamp로 변환.

mutate_to(value: str | int | datetime, to_type: str) -> int | datetime
    시간 형식 변환 (자동 sec/ms 구분, 문자열 파싱)

---

**특징:**
- 자동 sec/ms 구분 (자리수로 판별: 10자리=sec, 13자리=ms)
- 문자열 파싱 ("2021-5-3", "2025-1-5 5:12:39")
- datetime 객체 지원
- timezone은 UTC 가정
