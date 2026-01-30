from urllib.parse import urlparse

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..Models import Base


class Initializer:
    def __init__(self, database_url: str):
        self._original_url = database_url
        self._database_url = database_url

        # MySQL: utf8mb4 charset 추가
        if database_url.startswith('mysql'):
            if '?' in database_url:
                self._database_url = database_url + '&charset=utf8mb4'
            else:
                self._database_url = database_url + '?charset=utf8mb4'

        self.engine: Engine = None

    def _ensure_database_exists(self) -> None:
        """데이터베이스가 없으면 생성"""
        parsed = urlparse(self._original_url)

        # URL에서 데이터베이스명 추출 (path에서 / 제거)
        db_name = parsed.path.lstrip('/')
        if not db_name:
            return  # DB명이 없으면 스킵

        # 데이터베이스 없이 서버에 연결하기 위한 URL 생성
        server_url = f"{parsed.scheme}://{parsed.netloc}/"
        if parsed.scheme.startswith('mysql'):
            server_url += '?charset=utf8mb4'

        # 서버에 연결해서 데이터베이스 생성
        server_engine = create_engine(server_url, pool_pre_ping=True)
        with server_engine.connect() as conn:
            conn.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
            conn.commit()
        server_engine.dispose()

    def _create_engine(self) -> None:
        """엔진 생성"""
        if self.engine is None:
            self.engine = create_engine(self._database_url, pool_pre_ping=True)

    def check_connection(self) -> bool:
        """DB 연결 체크"""
        self._create_engine()
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            raise ConnectionError(f"Database connection failed: {e}")

    def initialize(self) -> None:
        """데이터베이스 및 기본 테이블 생성"""
        # 1. 데이터베이스 생성 (없으면)
        self._ensure_database_exists()

        # 2. 엔진 생성 및 연결 체크
        self._create_engine()
        self.check_connection()

        # 3. 기본 테이블 생성 (symbols, adjust_history, adjust_migration_history)
        Base.metadata.create_all(self.engine)

    def get_engine(self) -> Engine:
        """엔진 반환"""
        self._create_engine()
        return self.engine
