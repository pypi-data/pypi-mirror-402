# NormalizationService

거래소별 API 응답을 통일된 형식으로 정규화.

normalize_binance(raw_data: list[dict]) -> list[dict]
    Binance 응답 정규화 (키 매핑, 타입 변환, 가격 int 변환)

normalize_upbit(raw_data: list[dict]) -> list[dict]
    Upbit 응답 정규화

normalize_fdr(raw_data: pd.DataFrame) -> list[dict]
    FDR DataFrame 정규화

# NullHandlingService

누락된 데이터 처리 (volume → 0, price → 이전값 또는 DB 조회).

_conn_manager: ConnectionManager  # DB 연결 관리자

__init__(conn_manager: ConnectionManager) -> None
    DB 연결 관리자 주입

handle(data: list[dict], symbol: Symbol) -> list[dict]
    raise InvalidDataError
    Null 처리 (응답 내 이전값 → DB 조회 → 에러)

# ApiValidationService

API 키 확보 및 서버 응답 검증.

get_api_key(exchange: str) -> str
    raise NoApiKeyError
    .env에서 API 키 조회 ({EXCHANGE}_API_KEY)

check_server(exchange: str, api_key: str) -> bool
    raise ServerNotRespondedError
    서버 응답 확인 (ping 또는 server time)
