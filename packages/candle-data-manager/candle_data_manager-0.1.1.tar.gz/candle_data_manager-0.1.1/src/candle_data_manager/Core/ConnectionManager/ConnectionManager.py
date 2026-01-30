from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger


class ConnectionManager:
    def __init__(self, database_url: str = None, pool_size: int = 5, max_overflow: int = 10):
        logger.debug("ConnectionManager 초기화 시작")

        # database_url이 없으면 기본 MySQL 설정 사용
        if database_url is None:
            database_url = "mysql+pymysql://root@localhost/candle_data_manager"
            logger.info("database_url 미제공, 기본 MySQL 설정 사용: {}", database_url)

        # MySQL charset 설정
        if database_url.startswith('mysql'):
            if '?' in database_url:
                database_url += '&charset=utf8mb4'
            else:
                database_url += '?charset=utf8mb4'

        # Engine 생성 (pool_pre_ping: 연결 끊김 자동 감지)
        self.engine: Engine = create_engine(
            database_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600
        )

        # SessionFactory 생성
        self.Session = sessionmaker(bind=self.engine)

        logger.info("ConnectionManager 초기화 완료: pool_size={}, max_overflow={}", pool_size, max_overflow)

    def get_session(self) -> Session:
        logger.debug("새 세션 생성")
        return self.Session()

    @contextmanager
    def get_connection(self):
        logger.debug("Raw connection 생성")
        conn = self.engine.connect()
        try:
            yield conn
            conn.commit()
            logger.debug("Connection 커밋 완료")
        except Exception as e:
            conn.rollback()
            logger.error("Connection 롤백: {}", e)
            raise
        finally:
            conn.close()
            logger.debug("Connection 종료")

    @contextmanager
    def session_scope(self):
        logger.debug("세션 스코프 시작")
        session = self.Session()
        try:
            yield session
            session.commit()
            logger.debug("세션 커밋 완료")
        except Exception as e:
            session.rollback()
            logger.error("세션 롤백: {}", e)
            raise
        finally:
            session.close()
            logger.debug("세션 종료")

    def check_health(self) -> bool:
        logger.debug("DB 연결 상태 확인 중")
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.debug("DB 연결 정상")
            return True
        except Exception as e:
            logger.error("DB 연결 실패: {}", e)
            raise ConnectionError(f"Database connection failed: {e}")

    def close(self) -> None:
        logger.info("모든 DB 연결 종료")
        self.engine.dispose()
