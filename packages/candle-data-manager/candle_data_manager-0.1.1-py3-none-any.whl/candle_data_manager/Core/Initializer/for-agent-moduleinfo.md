# Initializer

DB 연결 및 초기화.

## Initializer

__init__(database_url: str)
    MySQL 자동 utf8mb4 추가

check_connection() -> bool
    raise ConnectionError

initialize() -> None
    기본 테이블 생성

get_engine() -> Engine
    SQLAlchemy Engine 반환
