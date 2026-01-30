# ApiValidationService

API 키 확보 및 서버 응답 검증. python-dotenv로 .env 파일 자동 로드.

## 초기화

__init__() -> None
    .env 파일 자동 로드 (find_dotenv로 프로젝트 루트까지 탐색)

## API 키 조회

get_api_key(exchange: str) -> str
    .env에서 거래소별 Access Key 조회

    Args:
        exchange: 거래소 이름 (대문자, 예: "BINANCE", "UPBIT")

    Returns:
        str: API Access Key

    Raises:
        NoApiKeyError: .env에 해당 키가 없는 경우

    Notes:
        - 환경변수 이름: {EXCHANGE}_API_KEY (예: BINANCE_API_KEY)
        - FDR은 API 키 불필요 (호출하지 않음)

get_api_secret(exchange: str) -> str
    .env에서 거래소별 Secret Key 조회

    Args:
        exchange: 거래소 이름 (대문자, 예: "BINANCE", "UPBIT")

    Returns:
        str: API Secret Key

    Raises:
        NoApiKeyError: .env에 해당 키가 없는 경우

    Notes:
        - 환경변수 이름: {EXCHANGE}_API_SECRET (예: BINANCE_API_SECRET)
        - FDR은 API 키 불필요 (호출하지 않음)

## 서버 응답 확인

check_server(exchange: str, api_key: str) -> bool
    API 서버 응답 확인

    Args:
        exchange: 거래소 이름
        api_key: API 키

    Returns:
        bool: 서버 정상 여부 (True)

    Raises:
        ServerNotRespondedError: 서버 응답 실패

    Notes:
        - 간단한 ping 또는 server time 조회로 확인
        - timeout 설정 필요 (예: 5초)

---

**사용 예시:**
```python
service = ApiValidationService()  # .env 파일 자동 로드

# API 키 조회
api_key = service.get_api_key("BINANCE")        # "abc123..."
api_secret = service.get_api_secret("BINANCE")  # "xyz789..."

# 서버 확인
service.check_server("BINANCE", api_key)  # True or raises
```

**의존성:**
- python-dotenv: .env 파일 로드
- os.getenv: 환경변수 조회
- requests: API 서버 응답 확인
