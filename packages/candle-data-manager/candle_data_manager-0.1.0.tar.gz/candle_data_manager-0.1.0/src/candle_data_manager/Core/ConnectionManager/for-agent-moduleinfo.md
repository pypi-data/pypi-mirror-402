# ConnectionManager

DB 연결 관리 및 자동 재연결.

## ConnectionManager

__init__(database_url: str, pool_size: int = 5, max_overflow: int = 10)
    Engine 생성 및 SessionFactory 설정
    MySQL charset 자동 추가

get_session() -> Session
    새 세션 반환 (ORM 작업용)

session_scope() -> ContextManager[Session]
    with문용 ORM 세션 context manager
    자동 commit/rollback/close

get_connection() -> ContextManager[Connection]
    with문용 Raw connection context manager
    자동 commit/rollback/close

check_health() -> bool
    raise ConnectionError
    연결 상태 확인

close() -> None
    모든 연결 종료

## 사용 예시

```python
# ORM 작업
conn_mgr = ConnectionManager(database_url)
with conn_mgr.session_scope() as session:
    symbol = session.query(Symbol).first()

# Raw SQL
with conn_mgr.get_connection() as conn:
    result = conn.execute(text("SELECT * FROM symbols"))
```
