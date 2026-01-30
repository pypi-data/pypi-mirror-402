# Core - 핵심 계층

## 개요
외부와의 통신, 저장된 데이터 입출력, 기본 기능 구현.
상호 의존성 없는 단위 기능.

## 모듈

### Models
데이터베이스 모델 정의.
Symbol, AdjustHistory, AdjustMigrationHistory (ORM).
CandleRepository (Core, 동적 테이블).

### Initializer
DB 연결 및 초기화.
기본 테이블 생성.

### ConnectionManager
DB 연결 관리.
세션 생성, 자동 재연결, 연결 풀 관리.
